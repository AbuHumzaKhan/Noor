# Noor V1 Live UI + Orchestra

The V1 Excel chat screen is connected to the real Python Orchestra. It is no longer a deterministic browser-only mock.

## Runtime

From the repository root:

```powershell
python -m pip install -e ".[analytics,dev]"
python -m noor.web
```

Then open:

```text
http://127.0.0.1:8765/preview.html
```

The server binds to localhost by default. `NOOR_UPLOAD_DIR` can override the upload directory.

## Request flow

```text
Chat UI
  -> POST /api/chat
  -> V1Planner
  -> TaskGraph
  -> UnifiedOrchestra
  -> registered capability provider
  -> result.verify
  -> JSON execution report
  -> chat UI
```

Excel workbooks can be attached through the UI. Uploads are limited to `.xlsx`, `.xlsm`, `.xltx`, and `.xltm` and 25 MB per request. VBA is not executed by the Excel skill.

## UI output

After a request, the chat displays:

- generated task graph
- selected provider/capability for each task
- execution status and attempts
- provider errors when a step fails
- structural verification result
- Noor's next-step recommendation

## Supported V1 natural-language requests

- inspect/open/show an Excel workbook
- read a named worksheet
- profile/analyze an Excel workbook
- generate basic SUM, AVERAGE, COUNT, MIN, and MAX formulas when a range is supplied
- remove duplicates
- fill blank cells
- rename a header

The planner remains intentionally deterministic in V1. A later LLM planner can produce the same `TaskGraph` contract without changing the execution layer.
