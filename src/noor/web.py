from __future__ import annotations

import json
import os
import re
import uuid
from email.parser import BytesParser
from email.policy import default
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .automation.data_ingest import DataIngestSkill
from .automation.orchestra import TaskGraph, UnifiedOrchestra
from .automation.registry import default_registry
from .automation.tasks.data_profiling import profile_data
from .automation.v1_planner import V1Planner

MAX_BODY_BYTES = 25 * 1024 * 1024
ALLOWED_UPLOADS = {
    ".csv", ".tsv", ".txt", ".json", ".jsonl", ".ndjson", ".xml", ".xlsx", ".xlsm", ".xltx", ".xltm",
    ".xls", ".ods", ".parquet", ".feather", ".pkl", ".pickle", ".sas7bdat", ".xpt", ".sav", ".zsav",
    ".dta", ".arff", ".h5", ".hdf", ".hdf5", ".html", ".htm", ".sql", ".db", ".sqlite", ".sqlite3",
    ".avro", ".orc", ".dat", ".data",
}


class NoorApplication:
    """Local HTTP bridge between the Noor chat UI and the V1 Orchestra."""

    def __init__(self, upload_dir: Path | None = None) -> None:
        self.planner = V1Planner()
        self.registry = default_registry()
        self.ingest = DataIngestSkill()
        self.upload_dir = (upload_dir or Path.cwd() / ".noor_uploads").resolve()
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def execute(self, request: str, path: str | None = None, sheet_name: str | None = None) -> dict[str, Any]:
        if not request.strip():
            raise ValueError("request cannot be empty")
        graph = self.planner.plan(request, path or "", sheet_name)
        orchestra = UnifiedOrchestra()
        registered: set[str] = set()
        for node in graph.nodes:
            provider_name = "result.verify" if node.capability == "result.verify" else node.capability
            if provider_name in registered:
                continue
            _, handler = self.registry.get(provider_name)
            orchestra.register_provider(node.capability, handler)
            registered.add(provider_name)
        executions = orchestra.execute(graph)
        return {
            "request": request,
            "plan": self._serialize_graph(graph),
            "executions": [self._serialize_execution(item) for item in executions],
            "success": all(item.status == "success" for item in executions),
            "next_step": self._next_step(executions),
        }

    def preview_dataset(self, path: str, sheet_name: str | None = None, nrows: int = 25) -> dict[str, Any]:
        """Return a bounded, UI-safe preview for a dataset uploaded to Noor."""
        file_path = self._validate_uploaded_path(path)
        loaded = self.ingest.load(str(file_path), sheet_name=sheet_name, nrows=nrows)
        return {
            "filename": file_path.name,
            "format": loaded["format"],
            "extension": file_path.suffix.lower(),
            "bytes": file_path.stat().st_size,
            "rows_returned": loaded["rows_returned"],
            "columns": loaded["columns"],
            "dtypes": loaded["dtypes"],
            "records": loaded["records"],
            "preview_limit": nrows,
        }

    def profile_dataset(self, path: str) -> dict[str, Any]:
        """Run the same deterministic profiling provider used by the Orchestra."""
        file_path = self._validate_uploaded_path(path)
        result = profile_data({"path": str(file_path)})
        result["filename"] = file_path.name
        result["extension"] = file_path.suffix.lower()
        return result

    def _validate_uploaded_path(self, path: str) -> Path:
        if not path:
            raise ValueError("No dataset is attached")
        file_path = Path(path).expanduser().resolve()
        try:
            file_path.relative_to(self.upload_dir)
        except ValueError as exc:
            raise ValueError("Dataset access is only available for files uploaded through Noor") from exc
        return self.ingest.validate_path(str(file_path))

    def save_upload(self, filename: str, content: bytes) -> dict[str, str | int]:
        suffix = Path(filename).suffix.lower()
        if suffix not in ALLOWED_UPLOADS:
            raise ValueError(f"Unsupported dataset upload: {suffix or 'missing extension'}")
        if not content:
            raise ValueError("Uploaded file is empty")
        if len(content) > MAX_BODY_BYTES:
            raise ValueError("Uploaded file exceeds the 25 MB limit")
        safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", Path(filename).name)
        destination = self.upload_dir / f"{uuid.uuid4().hex}_{safe_name}"
        destination.write_bytes(content)
        return {"filename": safe_name, "path": str(destination), "bytes": len(content)}

    @staticmethod
    def _serialize_graph(graph: TaskGraph) -> list[dict[str, Any]]:
        return [{
            "id": node.id, "capability": node.capability, "inputs": node.inputs,
            "depends_on": list(node.depends_on), "retries": node.retries, "provider": node.capability,
        } for node in graph.nodes]

    @staticmethod
    def _serialize_execution(execution: Any) -> dict[str, Any]:
        return {
            "node_id": execution.node_id, "capability": execution.capability, "provider": execution.capability,
            "status": execution.status, "attempts": execution.attempts, "errors": execution.errors,
            "output": execution.output,
        }

    @staticmethod
    def _next_step(executions: list[Any]) -> str:
        if not executions:
            return "No task was executed."
        failed = next((item for item in executions if item.status != "success"), None)
        if failed:
            return f"The {failed.capability} step needs attention before Noor can continue."
        verified = [item for item in executions if item.capability == "result.verify"]
        if verified and all(item.output.get("valid") for item in verified):
            return "The workflow completed and the final result passed structural verification."
        return "The workflow completed; inspect the execution details before continuing."


class NoorRequestHandler(BaseHTTPRequestHandler):
    server_version = "NoorV1/0.3"

    @property
    def app(self) -> NoorApplication:
        return self.server.app  # type: ignore[attr-defined]

    @property
    def web_root(self) -> Path:
        return Path(__file__).resolve().parent / "ui" / "chat"

    def _send_json(self, payload: dict[str, Any], status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length", "0"))
        if length > MAX_BODY_BYTES:
            raise ValueError("Request body exceeds the 25 MB limit")
        return self.rfile.read(length)

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/health":
            self._send_json({"status": "ok", "service": "noor", "version": "v1-data-excel", "upload_formats": len(ALLOWED_UPLOADS)})
            return
        self._serve_ui(path)

    def do_POST(self) -> None:
        try:
            path = urlparse(self.path).path
            if path == "/api/chat":
                payload = json.loads(self._read_body().decode("utf-8"))
                result = self.app.execute(
                    str(payload.get("message", "")),
                    str(payload["path"]) if payload.get("path") else None,
                    str(payload["sheet_name"]) if payload.get("sheet_name") else None,
                )
                self._send_json(result)
                return
            if path == "/api/preview":
                payload = json.loads(self._read_body().decode("utf-8"))
                result = self.app.preview_dataset(
                    str(payload.get("path", "")),
                    str(payload["sheet_name"]) if payload.get("sheet_name") else None,
                )
                self._send_json(result)
                return
            if path == "/api/profile":
                payload = json.loads(self._read_body().decode("utf-8"))
                result = self.app.profile_dataset(str(payload.get("path", "")))
                self._send_json(result)
                return
            if path == "/api/upload":
                result = self._parse_upload(self._read_body())
                self._send_json(result, HTTPStatus.CREATED)
                return
            self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
        except (ValueError, KeyError, json.JSONDecodeError) as exc:
            self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
        except Exception as exc:  # noqa: BLE001 - HTTP boundary
            self._send_json({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def _parse_upload(self, body: bytes) -> dict[str, Any]:
        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            raise ValueError("Upload must use multipart/form-data")
        message = BytesParser(policy=default).parsebytes(
            f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode() + body
        )
        for part in message.iter_parts():
            if part.get_content_disposition() != "form-data":
                continue
            filename = part.get_filename()
            if filename:
                content = part.get_payload(decode=True) or b""
                return {"upload": self.app.save_upload(filename, content)}
        raise ValueError("No dataset file was included in the upload")

    def _serve_ui(self, path: str) -> None:
        relative = path.lstrip("/") or "preview.html"
        if relative.startswith("api/"):
            self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
            return
        candidate = (self.web_root / relative).resolve()
        root = self.web_root.resolve()
        if root not in candidate.parents and candidate != root:
            self._send_json({"error": "Invalid path"}, HTTPStatus.BAD_REQUEST)
            return
        if not candidate.is_file():
            candidate = self.web_root / "preview.html"
        content_type = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "application/javascript; charset=utf-8"}.get(candidate.suffix, "application/octet-stream")
        body = candidate.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run(host: str = "127.0.0.1", port: int = 8765) -> None:
    upload_dir = Path(os.environ.get("NOOR_UPLOAD_DIR", str(Path.cwd() / ".noor_uploads")))
    app = NoorApplication(upload_dir=upload_dir)
    server = ThreadingHTTPServer((host, port), NoorRequestHandler)
    server.app = app  # type: ignore[attr-defined]
    print(f"Noor V1 UI: http://{host}:{port}/preview.html")
    print(f"Health:     http://{host}:{port}/api/health")
    server.serve_forever()


if __name__ == "__main__":
    run()
