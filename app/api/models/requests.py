from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, ConfigDict, model_validator


class RenderOptions(BaseModel):
    model_config = ConfigDict(extra="allow")
    mode: str | None = None
    show_labels: bool = True
    show_due: bool = True
    show_description: bool = True
    show_subtasks: bool = True

class PrintRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "module_name": "notes",
                    "content": {
                        "title": "Reminder",
                        "body": "Bring the return label to UPS",
                    },
                    "output_kind": "raw_tcp",
                    "output_config": {
                        "dry_run": False,
                    },
                }
            ]
        }
    )

    module_name: str
    content: dict[str, Any] | None = None
    source_name: str | None = None
    source_config: dict[str, Any] = Field(default_factory=dict)
    source_options: dict[str, Any] = Field(default_factory=dict)
    output_kind: str | None = None
    output_config: dict[str, Any] = Field(default_factory=dict)
    render_config: dict[str, Any] = Field(default_factory=dict)
    render_options: RenderOptions = Field(default_factory=RenderOptions)
    module_options: dict[str, Any] = Field(default_factory=dict)
    theme_name: str = "framed_food"

    @model_validator(mode="after")
    def validate_content_or_source(self) -> "PrintRequest":
        """
        Require either content or source_name.
        """
        if self.content is None and self.source_name is None:
            raise ValueError("Either 'content' or 'source_name' must be provided.")
        return self
