from __future__ import annotations

import csv
import json
import time
from pathlib import Path
from urllib import request

from src.config import DISCORD_WEBHOOK_URL, OUTPUT_DIR, VALID_STATUSES


class LabValidationError(RuntimeError):
    pass


def read_rows(csv_path: str | Path) -> list[dict[str, str]]:
    with Path(csv_path).open("r", encoding="utf-8", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def is_positive_number(raw_amount: str) -> bool:
    try:
        return float(raw_amount) > 0
    except (TypeError, ValueError):
        return False


def build_summary(rows: list[dict[str, str]]) -> dict[str, int | str]:
    missing_customer_ids = 0
    invalid_amounts = 0
    invalid_statuses = 0

    for row in rows:
        customer_id = row.get("customer_id", "").strip()
        amount = row.get("amount", "").strip()
        status = row.get("status", "").strip()

        if not customer_id:
            missing_customer_ids += 1
        if not is_positive_number(amount):
            invalid_amounts += 1
        if status not in VALID_STATUSES:
            invalid_statuses += 1

    return {
        "row_count": len(rows),
        "missing_customer_ids": missing_customer_ids,
        "invalid_amounts": invalid_amounts,
        "invalid_statuses": invalid_statuses,
        "validation_status": (
            "failed" if missing_customer_ids or invalid_amounts or invalid_statuses else "passed"
        ),
    }


def write_summary(summary: dict[str, int | str], output_path: str | Path) -> Path:
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(f"{json.dumps(summary, indent=2)}\n", encoding="utf-8")
    return output_file


def send_discord_message(summary: dict[str, int | str], webhook_url: str = DISCORD_WEBHOOK_URL) -> None:
    if not webhook_url:
        print("[Discord] No webhook URL configured, skipping alert.")
        return

    message = (
        f"Sales Data Quality {summary['validation_status'].upper()}\n"
        f"Rows: {summary['row_count']}\n"
        f"Missing customer_id: {summary['missing_customer_ids']}\n"
        f"Invalid amounts: {summary['invalid_amounts']}\n"
        f"Invalid statuses: {summary['invalid_statuses']}"
    )
    payload = json.dumps({"content": message}).encode("utf-8")
    http_request = request.Request(
        webhook_url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "DataQualityPipeline/1.0",
        },
        method="POST",
    )

    max_retries = 3
    last_err: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            with request.urlopen(http_request, timeout=15) as response:
                if response.status >= 400:
                    raise RuntimeError(f"Discord webhook returned HTTP {response.status}")
            print(f"[Discord] Alert sent successfully: {summary['validation_status'].upper()}")
            return
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            if attempt < max_retries:
                wait = 2 ** (attempt - 1)
                print(f"[Discord] Attempt {attempt} failed ({exc}), retrying in {wait}s...")
                time.sleep(wait)

    print(f"[Discord] WARNING: Failed to send alert after {max_retries} attempts: {last_err}")
    print("[Discord] Pipeline will continue without Discord notification.")


def run_lab_check(
    input_path: str | Path,
    output_path: str | Path | None = None,
    allow_failure: bool = False,
    skip_discord: bool = False,
) -> dict[str, int | str]:
    rows = read_rows(input_path)
    summary = build_summary(rows)
    output_file = write_summary(summary, output_path or (OUTPUT_DIR / "validation_summary.json"))

    if not skip_discord:
        send_discord_message(summary)

    if summary["validation_status"] == "failed" and not allow_failure:
        raise LabValidationError(f"Validation failed. Summary saved to {output_file}")

    return summary
