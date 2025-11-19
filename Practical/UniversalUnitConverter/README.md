# Universal Unit Converter

A FastAPI microservice that loads unit categories from a JSON/YAML configuration
and exposes endpoints for listing supported units and converting values. The
service supports hot reloading of the configuration file, alias resolution, and
fallback conversions through chained relationships.

## Features

* Automatic loading of unit metadata from JSON or YAML files.
* `/units` endpoint for discovering supported categories and unit names.
* `/convert` endpoint that supports chained conversions when a direct factor is
  unavailable.
* Validation and helpful error responses for invalid categories or units.
* File change detection so the service reloads configuration data when the
  source is updated.
* Conversion factor caching to avoid recomputing common conversions.
* Automated unit and API tests.

## Getting started

1. **Install dependencies** (preferably in a virtual environment):

   ```bash
   pip install -r Practical/UniversalUnitConverter/requirements.txt
   ```

2. **Run the FastAPI app**. By default the service uses the JSON sample config
   included in this directory. Point the `UNIT_CONFIG_PATH` environment variable
   to a different JSON/YAML file to override.

   ```bash
   export UNIT_CONFIG_PATH=Practical/UniversalUnitConverter/config/sample_units.yaml
   uvicorn Practical.UniversalUnitConverter.app:app --reload
   ```

3. **List supported units**:

   ```bash
   curl http://localhost:8000/units | jq
   ```

4. **Convert values**:

   ```bash
   curl -X POST http://localhost:8000/convert \
     -H 'Content-Type: application/json' \
     -d '{
       "category": "length",
       "from_unit": "mile",
       "to_unit": "centimeter",
       "value": 0.25
     }'
   ```

## Configuration format

The configuration file contains a `categories` object. Each category declares a
`base_unit`, one or more `units` with factors relative to the base, optional
`aliases`, and optional additional `relationships` that add custom conversion
paths.

```jsonc
{
  "categories": {
    "length": {
      "description": "Length measurements based on the meter.",
      "base_unit": "meter",
      "units": {
        "meter": {"to_base": 1, "aliases": ["m"]},
        "centimeter": {"to_base": 0.01, "aliases": ["cm"]},
        "inch": {"to_base": 0.0254, "aliases": ["in"]}
      },
      "relationships": [
        {"from": "inch", "to": "centimeter", "factor": 2.54}
      ]
    }
  }
}
```

When the file changes on disk the running application will reload it and flush
its conversion cache automatically.

## Tests

Use `pytest` to run the conversion engine and API tests:

```bash
pytest Practical/UniversalUnitConverter/tests
```

The tests spin up a FastAPI TestClient with a temporary configuration file so no
external services are required.
