from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


class RecipeIngredient(BaseModel):
    text: str
    quantity: str | None = None
    unit: str | None = None
    item: str | None = None
    note: str | None = None
    original_text: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class RecipeStep(BaseModel):
    number: int
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class RecipeItem(BaseModel):
    id: str
    title: str
    description: str | None = None
    servings: int | None = None
    prep_time: str | None = None
    cook_time: str | None = None
    total_time: str | None = None
    source_url: str | None = None
    ingredients: list[RecipeIngredient] = Field(default_factory=list)
    steps: list[RecipeStep] = Field(default_factory=list)
    labels: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskItem(BaseModel):
    id: str
    title: str
    completed: bool = False
    labels: list[str] = Field(default_factory=list)
    due: str | None = None
    description: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    subtasks: list["TaskItem"] = Field(default_factory=list)


TaskItem.model_rebuild()


class DocumentSection(BaseModel):
    kind: Literal[
        "title",
        "text",
        "spacer",
        "divider",
        "task_list",
        "label",
        "ingredient_list",
        "step_list",
    ]
    text: str | None = None
    tasks: list[TaskItem] = Field(default_factory=list)
    ingredients: list[RecipeIngredient] = Field(default_factory=list)
    steps: list[RecipeStep] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Document(BaseModel):
    title: str
    sections: list[DocumentSection] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RenderedReceipt(BaseModel):
    text_preview: str
    raw_bytes: bytes | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
