"""Extract: find raw files that have not been processed yet and read them into raw rows."""

import csv
import json
from pathlib import Path
from typing import Self

from etl.models import RawRow, Station


class Manifest:
    """A JSON file recording which raw files have already been processed.

    The manifest makes extraction incremental: a re-run skips files it has seen. It is saved only after a successful
    load, so a crash mid-run leaves the files unprocessed and the next run retries them.

    Attributes:
        path: Location of the manifest file.
    """

    def __init__(self, path: Path, processed: set[str] | None = None) -> None:
        """Create a manifest.

        Args:
            path: Where the manifest is stored.
            processed: File names already processed.
        """
        self.path = path
        self._processed: set[str] = set(processed or ())

    @classmethod
    def load(cls, path: Path) -> Self:
        """Load a manifest, or return an empty one if ``path`` does not exist.

        Args:
            path: Manifest file location.

        Returns:
            The manifest.
        """
        if not path.exists():
            return cls(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(path, set(data.get("processed", [])))

    def is_processed(self, name: str) -> bool:
        """Return whether a file name has been processed.

        Args:
            name: File name (not a full path).

        Returns:
            ``True`` if it was recorded.
        """
        return name in self._processed

    def mark(self, name: str) -> None:
        """Record a file name as processed (in memory; call :meth:`save` to persist).

        Args:
            name: File name.
        """
        self._processed.add(name)

    @property
    def processed(self) -> list[str]:
        """Processed file names, sorted."""
        return sorted(self._processed)

    def save(self) -> None:
        """Write the manifest atomically (write a temp file, then rename over the old one)."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps({"processed": self.processed}, indent=2), encoding="utf-8")
        tmp.replace(self.path)


def discover_new_files(raw_dir: Path, manifest: Manifest, pattern: str) -> list[Path]:
    """List files matching ``pattern`` that the manifest has not seen, sorted by name.

    File names embed ISO dates, so sorting by name is sorting by date.

    Args:
        raw_dir: Directory of raw files.
        manifest: Processed-files manifest.
        pattern: Glob such as ``"trips_*"``.

    Returns:
        Unprocessed paths in name order.
    """
    return sorted(p for p in raw_dir.glob(pattern) if p.is_file() and not manifest.is_processed(p.name))


def _as_text(value: object) -> str:
    return "" if value is None else str(value)


def read_trip_file(path: Path) -> list[RawRow]:
    """Read a raw trip file (``.csv`` or ``.jsonl``) into string-valued rows.

    Every value becomes a string and missing values become ``""``, so validation sees one shape regardless of the
    source format. Blank JSONL lines are skipped; a malformed JSONL line becomes a row with only ``_error`` set so the
    validator can reject it with a reason instead of crashing the run.

    Args:
        path: File to read.

    Returns:
        Raw rows, each with an extra ``_source`` key holding the file name.

    Raises:
        ValueError: If the extension is not ``.csv`` or ``.jsonl``.
    """
    rows: list[RawRow] = []
    if path.suffix == ".csv":
        with path.open(encoding="utf-8", newline="") as fh:
            for record in csv.DictReader(fh):
                rows.append({k: _as_text(v) for k, v in record.items()} | {"_source": path.name})
    elif path.suffix == ".jsonl":
        with path.open(encoding="utf-8") as fh:
            for line_no, line in enumerate(fh, start=1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    rows.append({"_error": f"bad_json:line{line_no}", "_source": path.name})
                    continue
                rows.append({k: _as_text(v) for k, v in record.items()} | {"_source": path.name})
    else:
        raise ValueError(f"unsupported trip file type: {path.name}")
    return rows


def read_station_file(path: Path) -> list[Station]:
    """Read a station snapshot CSV.

    Args:
        path: File with ``station_id,name,capacity`` columns.

    Returns:
        The stations in file order.
    """
    with path.open(encoding="utf-8", newline="") as fh:
        return [Station(r["station_id"], r["name"].strip(), int(r["capacity"])) for r in csv.DictReader(fh)]


def snapshot_date(path: Path) -> str:
    """Return the ISO date embedded in a file name such as ``stations_2026-03-08.csv``.

    Args:
        path: A raw file path.

    Returns:
        The ``YYYY-MM-DD`` part of the name.
    """
    return path.stem.split("_", 1)[1]
