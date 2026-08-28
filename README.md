# ThermaList

ThermaList is a modular FastAPI app for building and printing receipt-style thermal documents from external sources such as DoneTick, Home Assistant, and recipe providers. It supports previewing rendered output, sending it to printer backends, and composing new printable modules through registries and a shared document model.

## Current features

- Source registry for external data providers.
- Module registry for printable document builders.
- Receipt-oriented renderer for 80mm output.
- Output backends for preview, mock, ESC/POS, and raw TCP.
- Preview and print API routes.
- Tested pipeline error handling for failed source fetches.

## Architecture

- Sources: fetch external data and return source payloads.
- Pipeline: validates source results, maps payloads to module input, and builds receipts.
- Modules: convert module-shaped payloads into `Document` objects.
- Renderers: convert `Document` objects into thermal receipt output.
- Outputs: send rendered receipts to preview, printer backends, or mock targets.

## Project layout

```text
app/
├── api/
├── core/
├── modules/
├── outputs/
├── renderers/
├── services/
└── sources/

tests/
```

## Setup

Create and activate a virtual environment, then install dependencies.

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Configuration

The app loads configuration from:

```text
config.yaml
```

At minimum, configure:
- source connection settings, such as `base_url` and `token`
- printer settings, such as `host`, `port`, `font`, and `width`
- app timezone

## Run locally

```bash
uvicorn app.main:app --reload
```

App URLs:
- API root: `http://127.0.0.1:8000/`
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Testing

Run all tests:

```bash
python -m pytest
```

Run one file:

```bash
python -m pytest tests/test_pipeline.py
```

## Example preview request

```json
{
  "module_name": "todo",
  "source_name": "donetick",
  "source_config": {
    "base_url": "http://donetick.local:2021",
    "token": "YOUR_TOKEN"
  },
  "source_options": {
    "label": "home"
  }
}
```

## Example recipe preview request

```json
{
  "module_name": "recipe",
  "source_name": "mealie",
  "source_config": {
    "base_url": "http://mealie.local:9000",
    "token": "YOUR_TOKEN"
  },
  "source_options": {
    "slug": "chicken-kyiv"
  },
  "render_options": {
    "variant": "full-recipe",
    "include_description": true,
    "include_times": true,
    "include_labels": false,
    "include_source_url": false
  }
}
```

## Example print request

```json
{
  "module_name": "todo",
  "source_name": "donetick",
  "source_config": {
    "base_url": "http://donetick.local:2021",
    "token": "YOUR_TOKEN"
  },
  "output_kind": "escpos",
  "output_config": {
    "host": "192.168.1.50",
    "port": 9100,
    "dry_run": true
  }
}
```

## Notes

- Source failures are handled in the pipeline and surfaced as API errors.
- Modules are intended to receive normalized payloads from the pipeline rather than raw source envelopes.
- Thermal formatting is currently optimized for receipt-style output.

## Roadmap

- Add more modules and source integrations.
- Improve request/response documentation.
- Expand test coverage around source-to-module payload mapping.