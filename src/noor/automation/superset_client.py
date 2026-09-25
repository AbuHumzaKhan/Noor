from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass
class SupersetClient:
    """Minimal read-only Superset connector for NOOR.

    Authentication follows Superset's JWT login endpoint. Mutating endpoints are
    deliberately excluded from this first connector so NOOR cannot alter a BI
    workspace merely because a natural-language request was misinterpreted.
    """

    base_url: str
    access_token: str | None = None
    timeout: float = 20.0

    def __post_init__(self) -> None:
        self.base_url = self.base_url.rstrip("/")

    def login(self, username: str, password: str, provider: str = "db") -> dict:
        payload = self._request(
            "POST",
            "/api/v1/security/login",
            body={
                "username": username,
                "password": password,
                "provider": provider,
                "refresh": True,
            },
            authenticated=False,
        )
        token = payload.get("access_token")
        if not token:
            raise RuntimeError("Superset login did not return an access_token")
        self.access_token = str(token)
        return {
            "authenticated": True,
            "has_refresh_token": bool(payload.get("refresh_token")),
        }

    def list_dashboards(self) -> dict:
        return self._request("GET", "/api/v1/dashboard/")

    def get_dashboard(self, dashboard_id_or_slug: str) -> dict:
        return self._request("GET", f"/api/v1/dashboard/{dashboard_id_or_slug}")

    def list_charts(self) -> dict:
        return self._request("GET", "/api/v1/chart/")

    def get_chart(self, chart_id_or_uuid: str) -> dict:
        return self._request("GET", f"/api/v1/chart/{chart_id_or_uuid}")

    def list_datasets(self) -> dict:
        return self._request("GET", "/api/v1/dataset/")

    def get_dataset(self, dataset_id_or_uuid: str) -> dict:
        return self._request("GET", f"/api/v1/dataset/{dataset_id_or_uuid}")

    def list_databases(self) -> dict:
        return self._request("GET", "/api/v1/database/")

    def _request(
        self,
        method: str,
        path: str,
        *,
        body: dict | None = None,
        authenticated: bool = True,
    ) -> dict:
        if authenticated and not self.access_token:
            raise RuntimeError("Superset access token is required; authenticate first")

        headers = {"Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        if authenticated:
            headers["Authorization"] = f"Bearer {self.access_token}"

        request = Request(
            f"{self.base_url}{path}",
            data=json.dumps(body).encode("utf-8") if body is not None else None,
            headers=headers,
            method=method,
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Superset API returned HTTP {exc.code}: {detail[:500]}") from exc
        except URLError as exc:
            raise RuntimeError(f"Could not reach Superset at {self.base_url}: {exc.reason}") from exc

        try:
            result = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Superset API returned non-JSON content") from exc
        if not isinstance(result, dict):
            return {"result": result}
        return result
