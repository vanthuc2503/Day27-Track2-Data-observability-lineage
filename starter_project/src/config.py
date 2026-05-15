from __future__ import annotations

import os
from pathlib import Path

try:
	from dotenv import load_dotenv
except ImportError:  # pragma: no cover
	load_dotenv = None


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"
if load_dotenv is not None and ENV_FILE.exists():
	load_dotenv(ENV_FILE)
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"

PASSED_DATASET = DATA_DIR / "orders_passed.csv"
FAILED_DATASET = DATA_DIR / "orders_failed.csv"
SUMMARY_FILE = OUTPUT_DIR / "validation_summary.json"

VALID_STATUSES = {"completed", "pending", "cancelled"}

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
AIRFLOW_INPUT_FILE = os.getenv("AIRFLOW_INPUT_FILE", str(PASSED_DATASET))
