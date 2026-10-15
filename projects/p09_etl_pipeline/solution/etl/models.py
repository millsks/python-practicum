"""Shared data types for the bike-share ETL pipeline."""

from dataclasses import dataclass, field
from datetime import date, datetime
from zoneinfo import ZoneInfo

LOCAL_TZ = ZoneInfo("America/New_York")
"""The time zone the bike-share system's devices record naive timestamps in."""

TRIP_FIELDS: tuple[str, ...] = (
    "trip_id",
    "start_time",
    "end_time",
    "start_station_id",
    "end_station_id",
    "bike_id",
    "member_type",
)
"""Columns every raw trip record must carry."""

RawRow = dict[str, str]
"""A raw record as read from a file: every value is a string (missing values are ``""``)."""


@dataclass(frozen=True, slots=True)
class Station:
    """One station in a station reference snapshot.

    Attributes:
        station_id: Natural key, for example ``"S03"``.
        name: Display name; renames are tracked as SCD type 2 history.
        capacity: Number of docks.
    """

    station_id: str
    name: str
    capacity: int


@dataclass(frozen=True, slots=True)
class Trip:
    """A validated, normalized, enriched trip ready to load.

    Attributes:
        trip_id: Natural key used for deduplication and upserts.
        start_utc: Start time as an aware UTC datetime.
        end_utc: End time as an aware UTC datetime.
        duration_s: Whole seconds between start and end.
        start_station_id: Station the trip started at.
        end_station_id: Station the trip ended at.
        bike_id: Bike identifier.
        member_type: ``"member"`` or ``"casual"``.
        local_date: Calendar date of the start in the system's local time zone (the business day).
        start_station_name: Station name at enrichment time.
        end_station_name: Station name at enrichment time.
    """

    trip_id: str
    start_utc: datetime
    end_utc: datetime
    duration_s: int
    start_station_id: str
    end_station_id: str
    bike_id: str
    member_type: str
    local_date: date
    start_station_name: str = ""
    end_station_name: str = ""


@dataclass(frozen=True, slots=True)
class Rejection:
    """A raw row that failed validation.

    Attributes:
        row: The original raw row, unchanged.
        reasons: Every rule violation, for example ``("unknown_station:start_station_id",)``.
    """

    row: RawRow
    reasons: tuple[str, ...]


@dataclass(slots=True)
class RunSummary:
    """What one pipeline run did; returned by :func:`etl.pipeline.run_pipeline`.

    Attributes:
        files_processed: Names of raw files read in this run, in processing order.
        rows_read: Raw trip rows read.
        rows_valid: Rows that passed validation (before deduplication).
        rows_rejected: Rows that failed validation.
        rejected_by_reason: Count of rejections per reason code (a row can have several reasons).
        duplicates_removed: Valid rows dropped because their ``trip_id`` repeated within the batch.
        late_records: Loaded trips that started at or before the watermark from the previous run.
        trips_loaded: Trips upserted into ``fact_trip`` in this run.
        fact_trip_rows: Total rows in ``fact_trip`` after the run.
        station_versions: Total rows in ``dim_station`` after the run.
        watermark: The watermark after the run (ISO-8601 UTC), or ``None`` when nothing has loaded.
    """

    files_processed: list[str] = field(default_factory=list)
    rows_read: int = 0
    rows_valid: int = 0
    rows_rejected: int = 0
    rejected_by_reason: dict[str, int] = field(default_factory=dict)
    duplicates_removed: int = 0
    late_records: int = 0
    trips_loaded: int = 0
    fact_trip_rows: int = 0
    station_versions: int = 0
    watermark: str | None = None
