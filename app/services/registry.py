from __future__ import annotations

from app.core.config import (
    DoneTickConfig,
    HomeAssistantConfig,
    MealieConfig,
    RawTcpOutputConfig,
)
from app.modules.label import LabelModule
from app.modules.notes import NotesModule
from app.modules.recipe import RecipeModule
from app.modules.todo import TodoModule
from app.outputs.raw_tcp import RawTcpOutput
from app.sources.donetick import DoneTickSource
from app.sources.home_assistant import HomeAssistantSource
from app.sources.mealie import MealieSource


class SourceRegistry:
    def create(self, source_name: str, config: dict | None = None):
        cfg = config or {}
        if source_name == "donetick":
            return DoneTickSource(DoneTickConfig(**cfg))
        if source_name == "home_assistant":
            return HomeAssistantSource(HomeAssistantConfig(**cfg))
        if source_name == "mealie":
            return MealieSource(MealieConfig(**cfg))
        raise ValueError(f"Unsupported source: {source_name}")


class ModuleRegistry:
    def create(self, module_name: str):
        modules = {
            "label": LabelModule,
            "notes": NotesModule,
            "recipe": RecipeModule,
            "todo": TodoModule,
        }
        if module_name in modules:
            return modules[module_name]()
        raise ValueError(f"Unsupported module: {module_name}")


class OutputRegistry:
    def create(self, output_name: str, config: dict | None = None):
        cfg = config or {}
        if output_name in ("raw_tcp", "mock", "escpos"):
            return RawTcpOutput(), RawTcpOutputConfig(**cfg)
        raise ValueError(f"Unsupported output: {output_name}")
