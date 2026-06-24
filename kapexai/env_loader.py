"""Environment configuration helpers."""

from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


def load_environment(env_file: Optional[str] = None) -> bool:
    path = Path(env_file) if env_file else Path.cwd() / ".env"
    return load_dotenv(path, override=False)
