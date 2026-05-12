from pathlib import Path
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from voice_to_text__app.infrastructure.config.cli_source import parse_argv
from voice_to_text__app.paths import DEFAULT_WORKSPACE_DIR

Mode = Literal["prod", "bench"]


class WhisperSettings(BaseModel):
    model: str = "large-v3"
    device: str = "cpu"  # cpu/cuda/auto
    compute_type: Optional[str] = None

    threads: int = Field(default=10, ge=1)
    workers: int = Field(default=1, ge=1)

    beam_size: int = Field(default=10, ge=1)
    patience: float = Field(default=1.0, ge=0.0)

    vad: bool = False
    lang: str = "auto"


class BenchSettings(BaseModel):
    ref: Optional[Path] = None
    sample_seconds: int = Field(default=120, ge=1)

    # CPU-only defaults
    computes: tuple[str, ...] = ("int8",)
    vads: tuple[bool, ...] = (False,)

    threads: tuple[int, ...] = (4, 6, 8, 10, 12)
    workers: tuple[int, ...] = (1, 2, 3, 4, 5)
    beams: tuple[int, ...] = (1, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15)
    patiences: float = 1.0


class Settings(BaseSettings):
    """
    Settings() читает:
      1) CLI argv (наш source, без argparse)
      2) ENV VOICE2TEXT__...
      3) дефолты
    """
    model_config = SettingsConfigDict(
        env_prefix="VOICE2TEXT__",
        env_nested_delimiter="__",
        extra="ignore",
    )

    mode: Mode = "prod"
    target: str = ""
    out_dir: Path = DEFAULT_WORKSPACE_DIR
    log_level: str = "INFO"

    whisper: WhisperSettings = WhisperSettings()
    bench: BenchSettings = BenchSettings()

    @classmethod
    def settings_customise_sources(
            cls,
            settings_cls,
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
    ):
        def cli_settings() -> dict[str, Any]:
            return parse_argv()

        return (cli_settings, env_settings, init_settings, dotenv_settings, file_secret_settings)