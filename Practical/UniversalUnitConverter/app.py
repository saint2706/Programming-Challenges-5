"""FastAPI application exposing the unit converter service.

This application loads unit definitions from configuration and provides endpoints
to list available units and perform conversions.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Dict

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from .unit_converter import (
    CategoryNotFound,
    ConversionDataSource,
    UnitConverter,
    UnitNotFound,
)


def _build_converter(config_path: Optional[str] = None) -> UnitConverter:
    """Factory to create a configured UnitConverter."""
    config_file = config_path or os.environ.get(
        "UNIT_CONFIG_PATH",
        str(Path(__file__).with_name("config").joinpath("sample_units.json")),
    )
    data_source = ConversionDataSource(config_file)
    return UnitConverter(data_source)


class ConversionPayload(BaseModel):
    """Request payload for conversion."""
    category: str = Field(..., description="Unit category, e.g. 'length'.")
    from_unit: str = Field(..., description="Source unit name or alias.")
    to_unit: str = Field(..., description="Target unit name or alias.")
    value: float = Field(..., description="Value to convert.")


class ConversionResponse(BaseModel):
    """Response payload for conversion."""
    category: str
    from_unit: str
    to_unit: str
    value: float
    factor: float
    converted_value: float


class CategoryResponse(BaseModel):
    """Schema for category metadata."""
    description: str
    units: list[str]


class UnitsResponse(BaseModel):
    """Schema for the units listing endpoint."""
    categories: Dict[str, CategoryResponse]


def create_app(config_path: Optional[str] = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    converter = _build_converter(config_path)
    app = FastAPI(title="Universal Unit Converter", version="1.0.0")

    def get_converter() -> UnitConverter:
        return converter

    @app.get("/units", response_model=UnitsResponse)
    def list_units(
        conv: UnitConverter = Depends(get_converter),
    ) -> UnitsResponse:
        """List all supported unit categories and units."""
        categories = conv.list_categories()
        # Transform the raw dict to the pydantic model structure
        # categories structure from converter: {name: {"description": ..., "units": [...]}}
        typed: Dict[str, CategoryResponse] = {}
        for k, v in categories.items():
            # v is Dict[str, object]
            typed[k] = CategoryResponse(
                description=str(v.get("description", "")),
                units=v.get("units", []) # type: ignore
            )
        return UnitsResponse(categories=typed)

    @app.post("/convert", response_model=ConversionResponse)
    def convert_units(
        payload: ConversionPayload,
        conv: UnitConverter = Depends(get_converter),
    ) -> ConversionResponse:
        """Perform a unit conversion."""
        try:
            result = conv.convert(
                payload.category,
                payload.from_unit,
                payload.to_unit,
                payload.value,
            )
        except CategoryNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except UnitNotFound as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return ConversionResponse(
            category=result.category,
            from_unit=result.from_unit,
            to_unit=result.to_unit,
            value=result.value,
            factor=result.factor,
            converted_value=result.converted_value,
        )

    return app


app = create_app()
