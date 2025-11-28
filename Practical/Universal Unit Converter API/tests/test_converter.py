import json
import os
import time
from pathlib import Path

import pytest
from Practical.UniversalUnitConverter.unit_converter import (
    CategoryNotFound,
    ConversionDataSource,
    UnitConverter,
    UnitNotFound,
)


@pytest.fixture()
def config_file(tmp_path: Path) -> Path:
    data = {
        "categories": {
            "length": {
                "base_unit": "meter",
                "units": {
                    "meter": {"to_base": 1, "aliases": ["m"]},
                    "centimeter": {"to_base": 0.01, "aliases": ["cm"]},
                    "inch": {"to_base": 0.0254, "aliases": ["in"]},
                    "mile": {"to_base": 1609.34, "aliases": ["mi"]},
                },
            }
        }
    }
    path = tmp_path / "units.json"
    path.write_text(json.dumps(data))
    return path


@pytest.fixture()
def converter(config_file: Path) -> UnitConverter:
    return UnitConverter(ConversionDataSource(config_file))


def test_basic_conversion(converter: UnitConverter):
    result = converter.convert("length", "centimeter", "meter", 10)
    assert pytest.approx(result.converted_value) == 0.1


def test_alias_resolution(converter: UnitConverter):
    result = converter.convert("length", "cm", "m", 250)
    assert pytest.approx(result.converted_value) == 2.5


def test_chained_conversion(converter: UnitConverter):
    result = converter.convert("length", "mile", "centimeter", 0.5)
    # 0.5 miles -> 80467 centimeters with the configured factors
    assert result.converted_value == pytest.approx(80467.0, rel=1e-6)


def test_missing_category_raises(converter: UnitConverter):
    with pytest.raises(CategoryNotFound):
        converter.convert("temperature", "celsius", "kelvin", 1)


def test_missing_unit_raises(converter: UnitConverter):
    with pytest.raises(UnitNotFound):
        converter.convert("length", "parsec", "meter", 1)


def test_reload_when_file_changes(converter: UnitConverter, config_file: Path):
    # Add a new unit to the config
    updated_data = json.loads(config_file.read_text())
    updated_data["categories"]["length"]["units"]["kilometer"] = {
        "to_base": 1000,
        "aliases": ["km"],
    }
    time.sleep(0.02)
    config_file.write_text(json.dumps(updated_data))
    # Force a modified timestamp in case the filesystem resolution is low
    new_time = config_file.stat().st_mtime + 1
    os.utime(config_file, (new_time, new_time))
    result = converter.convert("length", "kilometer", "meter", 1)
    assert pytest.approx(result.converted_value) == 1000
