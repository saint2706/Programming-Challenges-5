"""
Project implementation.
"""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from Practical.UniversalUnitConverter.app import create_app


@pytest.fixture()
def config_file(tmp_path: Path) -> Path:
    """
    Docstring for config_file.
    """
    data = {
        "categories": {
            "mass": {
                "description": "Mass units",
                "base_unit": "kilogram",
                "units": {
                    "kilogram": {"to_base": 1, "aliases": ["kg"]},
                    "gram": {"to_base": 0.001, "aliases": ["g"]},
                    "pound": {"to_base": 0.45359237, "aliases": ["lb"]},
                },
            }
        }
    }
    path = tmp_path / "units.json"
    path.write_text(json.dumps(data))
    return path


@pytest.fixture()
def client(config_file: Path) -> TestClient:
    """
    Docstring for client.
    """
    app = create_app(str(config_file))
    return TestClient(app)


def test_list_units(client: TestClient):
    """
    Docstring for test_list_units.
    """
    response = client.get("/units")
    assert response.status_code == 200
    payload = response.json()
    assert "mass" in payload["categories"]
    assert set(payload["categories"]["mass"]["units"]) == {"kilogram", "gram", "pound"}


def test_convert_endpoint(client: TestClient):
    """
    Docstring for test_convert_endpoint.
    """
    response = client.post(
        "/convert",
        json={
            "category": "mass",
            "from_unit": "kilogram",
            "to_unit": "gram",
            "value": 2,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["converted_value"] == pytest.approx(2000)


def test_invalid_unit_returns_error(client: TestClient):
    """
    Docstring for test_invalid_unit_returns_error.
    """
    response = client.post(
        "/convert",
        json={
            "category": "mass",
            "from_unit": "stone",
            "to_unit": "gram",
            "value": 1,
        },
    )
    assert response.status_code == 400
    assert "Unknown unit" in response.json()["detail"]
