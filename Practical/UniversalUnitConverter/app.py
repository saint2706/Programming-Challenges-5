"""FastAPI application exposing the unit converter service."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from .unit_converter import (
    CategoryNotFound,
    ConversionDataSource,
    UnitConverter,
    UnitNotFound,
)


def _build_converter(config_path: Optional[str] = None) -> UnitConverter:
    config_file = config_path or os.environ.get(
        "UNIT_CONFIG_PATH",
        Path(__file__).with_name("config").joinpath("sample_units.json"),
    )
    data_source = ConversionDataSource(config_file)
    return UnitConverter(data_source)


class ConversionPayload(BaseModel):
    category: str = Field(..., description="Unit category, e.g. 'length'.")
    from_unit: str = Field(..., description="Source unit name or alias.")
    to_unit: str = Field(..., description="Target unit name or alias.")
    value: float = Field(..., description="Value to convert.")


class ConversionResponse(BaseModel):
    category: str
    from_unit: str
    to_unit: str
    value: float
    factor: float
    converted_value: float


class CategoryResponse(BaseModel):
    description: str
    units: list[str]


class UnitsResponse(BaseModel):
    categories: dict[str, CategoryResponse]


def create_app(config_path: Optional[str] = None) -> FastAPI:
    converter = _build_converter(config_path)
    app = FastAPI(title="Universal Unit Converter", version="1.0.0")

    def get_converter() -> UnitConverter:
        return converter

    @app.get("/units", response_model=UnitsResponse)
    def list_units(conv: UnitConverter = Depends(get_converter)) -> UnitsResponse:
        categories = conv.list_categories()
        typed = {k: CategoryResponse(**v) for k, v in categories.items()}
        return UnitsResponse(categories=typed)

    @app.post("/convert", response_model=ConversionResponse)
    def convert_units(payload: ConversionPayload, conv: UnitConverter = Depends(get_converter)) -> ConversionResponse:
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
        response = ConversionResponse(
            category=result.category,
            from_unit=result.from_unit,
            to_unit=result.to_unit,
            value=result.value,
            factor=result.factor,
            converted_value=result.converted_value,
        )
        return response

    return app


app = create_app()
