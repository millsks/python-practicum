"""Extract: find raw files that have not been processed yet and read them into raw rows."""

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
        # TODO: store path and a copy of processed as a set
        raise NotImplementedError

    @classmethod
    def load(cls, path: Path) -> Self:
        """Load a manifest, or return an empty one if ``path`` does not exist.

        Args:
            path: Manifest file location.

        Returns:
            The manifest.
        """
        # TODO: return an empty manifest if the file is missing; else read {'processed': [...]} JSON
        raise NotImplementedError

    def is_processed(self, name: str) -> bool:
        """Return whether a file name has been processed.

        Args:
            name: File name (not a full path).

        Returns:
            ``True`` if it was recorded.
        """
        # TODO: membership test
        raise NotImplementedError

    def mark(self, name: str) -> None:
        """Record a file name as processed (in memory; call :meth:`save` to persist).

        Args:
            name: File name.
        """
        # TODO: add the name (do not write the file here)
        raise NotImplementedError

    @property
    def processed(self) -> list[str]:
        """Processed file names, sorted."""
        # TODO: sorted list of names
        raise NotImplementedError

    def save(self) -> None:
        """Write the manifest atomically (write a temp file, then rename over the old one)."""
        # TODO: write JSON to a .tmp file, then Path.replace() it over self.path (atomic)
        raise NotImplementedError


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
    # TODO: glob, keep files the manifest has not seen, sort by name
    raise NotImplementedError


def _as_text(value: object) -> str:
    # TODO: None -> '', everything else str(value)
    raise NotImplementedError


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
    # TODO: csv.DictReader for .csv, json.loads per line for .jsonl; add '_source'; bad JSON -> {'_error': 'bad_json:line<N>'}
    raise NotImplementedError


def read_station_file(path: Path) -> list[Station]:
    """Read a station snapshot CSV.

    Args:
        path: File with ``station_id,name,capacity`` columns.

    Returns:
        The stations in file order.
    """
    # TODO: csv.DictReader -> Station(station_id, name.strip(), int(capacity))
    raise NotImplementedError


def snapshot_date(path: Path) -> str:
    """Return the ISO date embedded in a file name such as ``stations_2026-03-08.csv``.

    Args:
        path: A raw file path.

    Returns:
        The ``YYYY-MM-DD`` part of the name.
    """
    # TODO: 'stations_2026-03-08.csv' -> '2026-03-08'
    raise NotImplementedError
