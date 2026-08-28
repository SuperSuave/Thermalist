from __future__ import annotations

from app.core.config import (
    DoneTickConfig,
    EscposOutputConfig,
    HomeAssistantConfig,
    MealieConfig,
    MockOutputConfig,
    RawTcpOutputConfig,
)
from app.modules.label import LabelModule
from app.modules.notes import NotesModule
from app.modules.recipe import RecipeModule
from app.modules.todo import TodoModule
from app.outputs.escpos_python import EscposPythonOutput
from app.outputs.mock import MockOutput
from app.outputs.raw_tcp import RawTcpOutput
from app.sources.donetick import DoneTickSource
from app.sources.home_assistant import HomeAssistantSource
from app.sources.mealie import MealieSource


class SourceRegistry:
    def create(self, source_name: str, config: dict | None = None):
        config = config or {}
        if source_name == "donetick":
            return DoneTickSource(DoneTickConfig(**config))
        if source_name == "home_assistant":
            return HomeAssistantSource(HomeAssistantConfig(**config))
        if source_name == "mealie":
            return MealieSource(MealieConfig(**config))
        raise ValueError(f"Unsupported source: {source_name}")


class ModuleRegistry:
    def create(self, module_name: str):
        if module_name == "label":
            return LabelModule()
        if module_name == "notes":
            return NotesModule()
        if module_name == "recipe":
            return RecipeModule()
        if module_name == "todo":
            return TodoModule()
        raise ValueError(f"Unsupported module: {module_name}")


class OutputRegistry:
    def create(self, output_name: str, config: dict | None = None):
        config = config or {}
        if output_name == "mock":
            backend = MockOutput()
            return backend, MockOutputConfig(**config)
        if output_name == "escpos":
            backend = EscposPythonOutput()
            return backend, EscposOutputConfig(**config)
        if output_name == "raw_tcp":
            backend = RawTcpOutput()
            return backend, RawTcpOutputConfig(**config)
        raise ValueError(f"Unsupported output: {output_name}")
