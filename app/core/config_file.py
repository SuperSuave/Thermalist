from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PrinterConfig(BaseModel):
    backend: str = Field(default="raw_tcp")
    host: str | None = None
    port: int = 9100
    font: str = "A"
    width: int = 48
    cut: bool = True
    initialize: bool = True


class SourceConfig(BaseModel):
    name: str = "donetick"
    base_url: str | None = None
    token: str | None = None
    options: dict[str, Any] = Field(default_factory=dict)


class AppConfig(BaseModel):
    printer: PrinterConfig = Field(default_factory=PrinterConfig)
    source: SourceConfig = Field(default_factory=SourceConfig)
    timezone: str = "UTC"


class Settings(BaseSettings):
    mealie_base_url: str | None = None
    mealie_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


def load_config(path: Path = Path("config.yaml")) -> AppConfig:
    if not path.exists():
        return AppConfig()

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return AppConfig(**data)