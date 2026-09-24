# Noor V1 Data + Excel Capabilities

## Dataset upload formats

The V1 web interface accepts these 35 file extensions:

- CSV, TSV, TXT, DAT, DATA
- JSON, JSONL, NDJSON, XML
- XLSX, XLSM, XLTX, XLTM, XLS, ODS
- Parquet, Feather, Pickle
- SAS7BDAT, XPT, SAV, ZSAV, DTA
- ARFF
- HDF5/HDF/H5
- HTML/HTM tables
- SQLite/DB/SQLITE3
- Avro, ORC
- SQL scripts (inspection only in V1)

The upload boundary remains extension allow-listed and capped at 25 MB. Uploaded files are stored under the configured Noor upload directory with randomized names.

## Data workflow

```text
Upload
  -> data.inspect
  -> data.profile
  -> result.verify
```

The loader uses pandas and format-specific optional engines. If an engine is unavailable, Noor returns a structured dependency error rather than silently falling back to an incorrect parser.

## Excel V1

### Core

- Workbook inspection
- Bounded worksheet reading
- Explicit cell/formula writing
- Formula generation
- Duplicate removal
- Blank-value filling
- Header renaming
- Numeric worksheet analytics

### Advanced

- Workbook summary
- Cell text search
- Create worksheet
- Rename worksheet
- Freeze panes
- AutoFilter ranges
- Sort worksheet rows
- Formula validation
- Formula explanation

Noor does not execute VBA/macros. Macro-enabled workbooks are preserved with `keep_vba` when they are rewritten.

## Safety boundaries

- Only registered Orchestra capabilities can execute.
- Dataset uploads are restricted to known extensions.
- SQL script files are not executed by the V1 loader.
- SQLite table names are validated before query construction.
- Formula validation blocks selected external/action functions.
- Write operations are explicit and deterministic.
- Results continue through the existing verification task.
