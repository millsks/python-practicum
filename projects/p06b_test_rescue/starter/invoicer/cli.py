"""Command-line entry point: read ``description,qty,cents`` lines from stdin."""

import sys
from typing import Any

from invoicer.invoices import build_invoice, save_invoice


def parse_line(text: str) -> dict[str, Any]:
    """Parse one ``description,qty,cents`` line.

    Args:
        text: The line to parse.

    Returns:
        The line item.

    Raises:
        ValueError: If the line is malformed.
    """
    description, qty, cents = text.strip().split(",")
    return {"description": description, "qty": int(qty), "cents": int(cents)}


def main(argv: list[str] | None = None) -> int:
    """Run the tool.

    Args:
        argv: Arguments after the program name; defaults to ``sys.argv[1:]``.

    Returns:
        0 on success, or 2 on a usage or input error.
    """
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: invoicer CUSTOMER", file=sys.stderr)
        return 2
    try:
        lines = [parse_line(line) for line in sys.stdin if line.strip()]
        invoice = build_invoice(args[0], lines)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    save_invoice(invoice)
    print(f"{invoice['number']} total {invoice['total']} {invoice['currency']}")
    return 0
