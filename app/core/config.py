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


class DoneTickConfig(BaseModel):
    base_url: str = Field(default="http://localhost:2021")
    token: str | None = None
    timeout_seconds: float = 10.0
    timezone: str | None = None


class HomeAssistantConfig(BaseModel):
    base_url: str = Field(default="http://homeassistant.local:8123")
    token: str | None = None
    timeout_seconds: float = 10.0


class MealieConfig(BaseModel):
    base_url: str = Field(default="https://mealie.myfqdn.com")
    token: str | None = None
    timeout_seconds: float = 10.0


class MockOutputConfig(BaseModel):
    enabled: bool = True


class RendererConfig(BaseModel):
    width: int = 48
    show_due: bool = True
    show_labels: bool = True


class EscposOutputConfig(BaseModel):
    host: str | None = None
    port: int = 9100
    profile: str | None = None
    dry_run: bool = True


class RawTcpOutputConfig(BaseModel):
    host: str | None = None
    port: int = 9100
    timeout: int = 5
    dry_run: bool = True
    cut: bool = False
    initialize: bool = True
    font: str = "A"


class AppConfig(BaseModel):
    donetick: DoneTickConfig = Field(default_factory=DoneTickConfig)
    homeassistant: HomeAssistantConfig = Field(default_factory=HomeAssistantConfig)
    mealie: MealieConfig = Field(default_factory=MealieConfig)
    renderer: RendererConfig = Field(default_factory=RendererConfig)
    output_mock: MockOutputConfig = Field(default_factory=MockOutputConfig)
    output_escpos: EscposOutputConfig = Field(default_factory=EscposOutputConfig)
    raw_tcp: RawTcpOutputConfig = Field(default_factory=RawTcpOutputConfig)
    timezone: str = "UTC"

    @property
    def printer(self) -> PrinterConfig:
        return PrinterConfig(
            backend="raw_tcp",
            host=self.raw_tcp.host,
            port=self.raw_tcp.port,
            font=self.raw_tcp.font,
            width=self.renderer.width,
            cut=self.raw_tcp.cut,
            initialize=self.raw_tcp.initialize,
        )

    @property
    def source(self) -> SourceConfig:
        return SourceConfig(
            name="donetick",
            base_url=self.donetick.base_url,
            token=self.donetick.token,
            options={"timezone": self.donetick.timezone} if self.donetick.timezone else {},
        )


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


def resolve_mealie_config(app_cfg: AppConfig, settings: Settings) -> MealieConfig:
    return MealieConfig(
        base_url=settings.mealie_base_url or app_cfg.mealie.base_url,
        token=settings.mealie_api_key or app_cfg.mealie.token,
        timeout_seconds=app_cfg.mealie.timeout_seconds,
    )
