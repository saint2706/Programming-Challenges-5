# Universal Unit Converter

A FastAPI microservice that loads unit categories from a JSON/YAML configuration
and exposes endpoints for listing supported units and converting values.

## 📋 Features

- **Dynamic Configuration**: Loads unit definitions from JSON or YAML files.
- **Hot Reloading**: Automatically reloads configuration when the file changes.
- **API Endpoints**:
  - `/units`: Discover supported categories and units.
  - `/convert`: Perform chained conversions (e.g., inch -> cm).
- **Smart Resolution**: Handles aliases (e.g., "m", "meter") and transitive conversions.

## 💻 Getting Started

### 1. Install Dependencies

```bash
pip install -r Practical/UniversalUnitConverter/requirements.txt
```

### 2. Run the Service

By default, the service uses the included `sample_units.json`.

```bash
# Optional: Override config path
# export UNIT_CONFIG_PATH=config/my_units.yaml

uvicorn Practical.UniversalUnitConverter.app:app --reload
```

### 3. Usage Examples

**List Units:**

```bash
curl http://localhost:8000/units
```

**Convert Value:**

```bash
curl -X POST http://localhost:8000/convert \
  -H 'Content-Type: application/json' \
  -d '{
    "category": "length",
    "from_unit": "mile",
    "to_unit": "kilometer",
    "value": 5
  }'
```

## ⚙️ Configuration Format

The configuration file defines categories, a base unit for each, and conversion factors relative to that base.

```json
{
  "categories": {
    "length": {
      "description": "Length measurements",
      "base_unit": "meter",
      "units": {
        "meter": { "to_base": 1, "aliases": ["m"] },
        "kilometer": { "to_base": 1000, "aliases": ["km"] },
        "mile": { "to_base": 1609.34 }
      }
    }
  }
}
```

## 🧪 Tests

Run the test suite using pytest:

```bash
pytest Practical/UniversalUnitConverter/tests
```
