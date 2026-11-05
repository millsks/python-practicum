"""Build and store invoices."""

import json
import logging
import os
import random
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from invoicer.config import load_config
from invoicer.rates import fetch_rate

logger = logging.getLogger("invoicer")
HISTORY: list[str] = []


def build_invoice(customer: str, lines: list[dict[str, Any]]) -> dict[str, Any]:
    """Build an invoice dated today and due in 30 days.

    Args:
        customer: Customer name.
        lines: Line items, each with ``qty`` and ``cents``.

    Returns:
        The invoice. Amounts are converted to the configured currency.

    Raises:
        ValueError: If there are no lines.
    """
    if not lines:
        raise ValueError("an invoice needs at least one line")
    config = load_config()
    net = sum(line["qty"] * line["cents"] for line in lines)
    tax = round(net * float(str(config["tax"])))
    currency = str(config["currency"])
    rate = 1.0 if currency == "USD" else fetch_rate(currency)
    today = date.today()
    invoice = {
        "number": f"INV-{today:%Y%m%d}-{random.randint(1000, 9999)}",
        "customer": customer,
        "currency": currency,
        "net": round(net * rate),
        "tax": round(tax * rate),
        "total": round((net + tax) * rate),
        "issued": today.isoformat(),
        "due": (today + timedelta(days=30)).isoformat(),
    }
    if invoice["total"] > 1_000_000:
        logger.warning("large invoice %s", invoice["number"])
    HISTORY.append(str(invoice["number"]))
    return invoice


def is_overdue(invoice: dict[str, Any]) -> bool:
    """Return whether the invoice's due date has passed.

    Args:
        invoice: An invoice with a ``due`` date.

    Returns:
        True from the day after the due date onward.
    """
    return date.today() > date.fromisoformat(invoice["due"])


def save_invoice(invoice: dict[str, Any]) -> Path:
    """Write the invoice as JSON under ``INVOICER_DIR``, or ``invoices`` by default.

    Args:
        invoice: The invoice to save.

    Returns:
        The file that was written.
    """
    directory = Path(os.environ.get("INVOICER_DIR", "invoices"))
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{invoice['number']}.json"
    if path.exists():
        logger.warning("overwriting %s", path)
    path.write_text(json.dumps(invoice, indent=2), encoding="utf-8")
    print(f"saved {path}")
    return path
