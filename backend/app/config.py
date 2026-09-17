from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def _path_from_env(name: str, default: str) -> Path:
    path = Path(os.getenv(name, default))
    return path if path.is_absolute() else REPO_ROOT / path


@dataclass(frozen=True)
class Settings:
    standard_procedures_path: Path = _path_from_env(
        "STANDARD_PROCEDURES_PATH", "demo_std_ptc_data/standard_procedures.json"
    )
    emerging_treatments_path: Path = _path_from_env(
        "EMERGING_TREATMENTS_PATH", "demo_emg_trt_data/emerging_treatments.json"
    )
    query_test_set_path: Path = _path_from_env("QUERY_TEST_SET_PATH", "test_set/queries.json")
    embedding_model: str = os.getenv(
        "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )
    llm_provider: str = os.getenv("LLM_PROVIDER", "")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "")
    llm_model: str = os.getenv("LLM_MODEL", "")


settings = Settings()
