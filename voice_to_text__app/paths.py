from pathlib import Path
from typing import Final

MAIN_DIR: Final[Path] = Path(__file__).resolve().parents[1]

DEFAULT_WORKSPACE_DIR: Final[Path] = MAIN_DIR / "workspace"
