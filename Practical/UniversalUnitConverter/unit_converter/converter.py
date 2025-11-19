"""Conversion engine built on top of the configuration loader."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Tuple

from .config_loader import ConversionDataSource


class UnitConversionError(RuntimeError):
    """Base error for conversion problems."""


class CategoryNotFound(UnitConversionError):
    pass


class UnitNotFound(UnitConversionError):
    pass


class InvalidConfiguration(UnitConversionError):
    pass


@dataclass(frozen=True)
class ConversionResult:
    category: str
    from_unit: str
    to_unit: str
    factor: float
    value: float

    @property
    def converted_value(self) -> float:
        return self.value * self.factor


class UnitConverter:
    """Performs conversions using the metadata provided by a data source."""

    def __init__(self, data_source: ConversionDataSource):
        self.data_source = data_source
        self._categories: Dict[str, Dict[str, float]] = {}
        self._graphs: Dict[str, Dict[str, Dict[str, float]]] = {}
        self._aliases: Dict[str, Dict[str, str]] = {}
        self._descriptions: Dict[str, str] = {}
        self._factor_cache: Dict[Tuple[str, str, str], float] = {}
        self._data_version = -1
        self._ensure_latest()

    # ------------------------------------------------------------------
    def _ensure_latest(self) -> None:
        data = self.data_source.load()
        if self._data_version == self.data_source.version:
            return
        self._build_categories(data)
        self._factor_cache.clear()
        self._data_version = self.data_source.version

    def _build_categories(self, data: Dict[str, Dict]) -> None:
        categories = data.get("categories")
        if not isinstance(categories, dict):
            raise InvalidConfiguration("Configuration must include a 'categories' mapping")
        self._categories.clear()
        self._graphs.clear()
        self._aliases.clear()
        self._descriptions.clear()
        for category_name, config in categories.items():
            units = config.get("units")
            if not units:
                raise InvalidConfiguration(f"Category '{category_name}' does not define any units")
            processed_units: Dict[str, float] = {}
            alias_map: Dict[str, str] = {}
            for unit_name, definition in units.items():
                if isinstance(definition, dict):
                    factor = definition.get("to_base")
                    aliases = definition.get("aliases", [])
                else:
                    factor = definition
                    aliases = []
                if factor is None:
                    raise InvalidConfiguration(
                        f"Unit '{unit_name}' in '{category_name}' is missing a 'to_base' factor"
                    )
                if factor <= 0:
                    raise InvalidConfiguration(
                        f"Unit '{unit_name}' in '{category_name}' must have a positive factor"
                    )
                processed_units[unit_name] = float(factor)
                for alias in aliases:
                    alias_map[alias] = unit_name
            base_unit = config.get("base_unit")
            if not base_unit:
                base_unit = next(iter(processed_units))
            if base_unit not in processed_units:
                raise InvalidConfiguration(
                    f"Base unit '{base_unit}' is not defined in '{category_name}'"
                )
            self._categories[category_name] = processed_units
            self._aliases[category_name] = alias_map
            self._descriptions[category_name] = config.get("description", "")
            self._graphs[category_name] = self._build_graph(
                processed_units, base_unit, config.get("relationships", [])
            )

    def _build_graph(self, units: Dict[str, float], base_unit: str, relationships: List[Dict]) -> Dict[str, Dict[str, float]]:
        graph: Dict[str, Dict[str, float]] = {unit: {} for unit in units}
        base_factor = units[base_unit]
        if base_factor <= 0:
            raise InvalidConfiguration("Base unit must have a positive factor")
        # Connect every unit to the base unit so indirect paths can be found.
        for unit_name, factor in units.items():
            if unit_name == base_unit:
                continue
            to_base = factor / base_factor
            graph[unit_name][base_unit] = to_base
            graph[base_unit][unit_name] = 1 / to_base
        # Additional explicit relationships for custom chains.
        for relationship in relationships or []:
            source = relationship.get("from")
            target = relationship.get("to")
            rel_factor = relationship.get("factor")
            if not source or not target or rel_factor is None:
                raise InvalidConfiguration("Relationships must define 'from', 'to' and 'factor'")
            if source not in graph or target not in graph:
                raise InvalidConfiguration(
                    f"Relationship references unknown units: {source!r} -> {target!r}"
                )
            if rel_factor <= 0:
                raise InvalidConfiguration("Relationship factors must be positive")
            graph[source][target] = float(rel_factor)
            graph[target][source] = 1 / float(rel_factor)
        return graph

    # ------------------------------------------------------------------
    def list_categories(self) -> Dict[str, Dict[str, object]]:
        self._ensure_latest()
        response: Dict[str, Dict[str, object]] = {}
        for name, units in self._categories.items():
            response[name] = {
                "description": self._descriptions.get(name, ""),
                "units": sorted(units.keys()),
            }
        return response

    def convert(self, category: str, from_unit: str, to_unit: str, value: float) -> ConversionResult:
        self._ensure_latest()
        canonical_category = self._categories.get(category)
        if canonical_category is None:
            raise CategoryNotFound(f"Unknown category '{category}'")
        source = self._resolve_unit(category, from_unit)
        target = self._resolve_unit(category, to_unit)
        cache_key = (category, source, target)
        factor = self._factor_cache.get(cache_key)
        if factor is None:
            factor = self._find_factor(category, source, target)
            self._factor_cache[cache_key] = factor
        return ConversionResult(category, source, target, factor, float(value))

    def _resolve_unit(self, category: str, unit: str) -> str:
        if unit in self._categories[category]:
            return unit
        alias_map = self._aliases.get(category, {})
        resolved = alias_map.get(unit)
        if not resolved:
            raise UnitNotFound(f"Unknown unit '{unit}' in category '{category}'")
        return resolved

    def _find_factor(self, category: str, source: str, target: str) -> float:
        if source == target:
            return 1.0
        graph = self._graphs[category]
        visited = set()
        queue = deque([(source, 1.0)])
        while queue:
            unit, acc_factor = queue.popleft()
            visited.add(unit)
            for neighbor, edge_factor in graph[unit].items():
                if neighbor in visited:
                    continue
                new_factor = acc_factor * edge_factor
                if neighbor == target:
                    return new_factor
                queue.append((neighbor, new_factor))
        raise UnitNotFound(
            f"No conversion path between '{source}' and '{target}' in '{category}'"
        )

