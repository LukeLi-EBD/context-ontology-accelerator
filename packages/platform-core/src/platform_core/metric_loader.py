"""External metric-fact loader: CSV/Parquet -> platform.metric_observation.

The loader is deliberately dumb: every column is declared in a YAML mapping,
nothing is inferred from headers, and a single bad row rejects the whole batch
before anything is written. The write itself is one transaction with an upsert
on the observation window key, so re-importing the same facts never duplicates
rows.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable, Iterator

import yaml

from .adapters.metadata_pg import MetadataPg

MAPPING_INVALID = "E_LOADER_MAPPING_INVALID"
MISSING_COLUMN = "E_LOADER_MISSING_COLUMN"
BAD_ROWS = "E_LOADER_BAD_ROWS"
WINDOW_INVALID = "E_LOADER_WINDOW_INVALID"
WINDOW_UNDEFINED = "E_LOADER_WINDOW_UNDEFINED"
BAD_SOURCE = "E_LOADER_SOURCE_INVALID"
UNSUPPORTED_FORMAT = "E_LOADER_UNSUPPORTED_FORMAT"
PARQUET_UNSUPPORTED = "E_LOADER_PARQUET_UNSUPPORTED"
FILE_UNREADABLE = "E_LOADER_FILE_UNREADABLE"
DB_FAILED = "E_LOADER_DB_FAILED"
METRIC_NOT_FOUND = "E_METRIC_NOT_FOUND"
METRIC_NOT_PUBLISHABLE = "E_METRIC_NOT_PUBLISHABLE"

MAX_REPORTED_ERRORS = 100

_ALLOWED_COLUMNS = {
    "entity_key",
    "numerator",
    "denominator",
    "window_start",
    "window_end",
    "institution",
    "product",
}
_REQUIRED_COLUMNS = ("entity_key", "numerator", "window_start", "window_end")

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

_UPSERT_SQL = """
INSERT INTO platform.metric_observation
  (metric_id, definition_version, institution, product, entity_key,
   as_of, period_start, period_end, numerator, denominator,
   window_start, window_end, data_source, fixture)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT ON CONSTRAINT metric_observation_window_key DO UPDATE SET
  institution = EXCLUDED.institution,
  product = EXCLUDED.product,
  as_of = EXCLUDED.as_of,
  period_start = EXCLUDED.period_start,
  period_end = EXCLUDED.period_end,
  numerator = EXCLUDED.numerator,
  denominator = EXCLUDED.denominator,
  data_source = EXCLUDED.data_source,
  fixture = EXCLUDED.fixture,
  computed_at = now()
"""


class _Reject(Exception):
    """A rejection that is reported as a structured result, never a traceback."""

    def __init__(self, code: str, message: str, **detail: Any) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.detail = detail


@dataclass
class _Row:
    line: int
    entity_key: str
    numerator: Decimal
    denominator: Decimal | None
    window_start: date
    window_end: date
    institution: str | None
    product: str | None


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (date,)):
        return value.isoformat()
    return str(value).strip()


def _parse_date(value: Any) -> date:
    text = _text(value)
    if not _DATE_RE.match(text):
        raise ValueError(f"expected YYYY-MM-DD, got {value!r}")
    return date.fromisoformat(text)


def _parse_number(value: Any, column: str) -> Decimal:
    text = _text(value)
    if not text:
        raise ValueError(f"{column} is empty")
    try:
        number = Decimal(text)
    except InvalidOperation:
        raise ValueError(f"{column} is not numeric: {text!r}") from None
    if not number.is_finite():
        raise ValueError(f"{column} is not finite: {text!r}")
    return number


def _read_mapping(path: Path) -> dict[str, Any]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise _Reject(MAPPING_INVALID, f"cannot read mapping {path}: {exc}") from None
    if not isinstance(raw, dict):
        raise _Reject(MAPPING_INVALID, "mapping must be a YAML mapping")
    columns = raw.get("columns")
    if not isinstance(columns, dict):
        raise _Reject(MAPPING_INVALID, "mapping requires a 'columns' mapping")
    unknown = sorted(set(columns) - _ALLOWED_COLUMNS)
    if unknown:
        raise _Reject(
            MAPPING_INVALID,
            f"unknown mapping column(s): {', '.join(unknown)}",
            columns=unknown,
        )
    for key, value in columns.items():
        if not isinstance(value, str) or not value.strip():
            raise _Reject(
                MAPPING_INVALID, f"mapping column {key!r} must name a non-empty column"
            )
        columns[key] = value.strip()
    metric_id = raw.get("metric_id")
    if metric_id is not None and not isinstance(metric_id, str):
        raise _Reject(MAPPING_INVALID, "mapping metric_id must be a string")
    return {"metric_id": metric_id, "columns": columns}


def _iter_csv(path: Path) -> tuple[list[str], Iterator[tuple[int, dict[str, Any]]]]:
    handle = path.open("r", encoding="utf-8-sig", newline="")
    reader = csv.DictReader(handle)
    header = list(reader.fieldnames or [])

    def rows() -> Iterator[tuple[int, dict[str, Any]]]:
        try:
            for row in reader:
                yield reader.line_num, dict(row)
        finally:
            handle.close()

    return header, rows()


def _iter_parquet(path: Path) -> tuple[list[str], Iterator[tuple[int, dict[str, Any]]]]:
    try:
        import pyarrow.parquet as parquet  # type: ignore[import-not-found]
    except ImportError:
        raise _Reject(
            PARQUET_UNSUPPORTED,
            "parquet input needs the optional pyarrow dependency, which is not "
            "installed in this image; convert the file to CSV or install pyarrow",
        ) from None
    table = parquet.read_table(path)
    header = list(table.schema.names)
    columns = {name: table[name].to_pylist() for name in header}

    def rows() -> Iterator[tuple[int, dict[str, Any]]]:
        for index in range(table.num_rows):
            yield index + 2, {name: columns[name][index] for name in header}

    return header, rows()


def _read_table(path: Path) -> tuple[list[str], Iterator[tuple[int, dict[str, Any]]]]:
    suffix = path.suffix.lower()
    try:
        if suffix == ".csv":
            return _iter_csv(path)
        if suffix == ".parquet":
            return _iter_parquet(path)
    except OSError as exc:
        raise _Reject(FILE_UNREADABLE, f"cannot read {path}: {exc}") from None
    except _Reject:
        raise
    except Exception as exc:  # pyarrow raises its own error types
        raise _Reject(FILE_UNREADABLE, f"cannot read {path}: {exc}") from None
    raise _Reject(
        UNSUPPORTED_FORMAT,
        f"unsupported input format {suffix!r} (expected .csv or .parquet)",
    )


class MetricLoader:
    """Load external facts for one metric into platform.metric_observation."""

    def __init__(self, metadata: MetadataPg) -> None:
        self._meta = metadata

    def _definition(self, metric_id: str) -> dict[str, Any]:
        rows = self._meta.query(
            "SELECT metric_id, definition_version, publishable, metric_kind, "
            "window_kind, min_window_days FROM platform.metric_definition "
            "WHERE metric_id = %s",
            (metric_id,),
        )
        if not rows:
            raise _Reject(METRIC_NOT_FOUND, f"unknown metric: {metric_id}", metricId=metric_id)
        row = rows[0]
        if not row["publishable"]:
            raise _Reject(
                METRIC_NOT_PUBLISHABLE,
                f"metric is not publishable, loading is refused: {metric_id}",
                metricId=metric_id,
            )
        if not row["window_kind"]:
            raise _Reject(
                WINDOW_UNDEFINED,
                f"metric definition has no window_kind (V19 fields not seeded): {metric_id}",
                metricId=metric_id,
            )
        return row

    def _validate_rows(
        self,
        header: list[str],
        rows: Iterable[tuple[int, dict[str, Any]]],
        columns: dict[str, str],
        definition: dict[str, Any],
        require_denominator: bool,
    ) -> tuple[list[_Row], list[dict[str, Any]], int]:
        missing = [key for key in _REQUIRED_COLUMNS if key not in columns]
        if require_denominator and "denominator" not in columns:
            missing.append("denominator")
        if missing:
            raise _Reject(
                MAPPING_INVALID,
                "mapping does not declare required column(s): " + ", ".join(missing),
                columns=missing,
            )
        not_in_file = [name for name in columns.values() if name not in header]
        if not_in_file:
            raise _Reject(
                MISSING_COLUMN,
                "declared column(s) missing from the input header: " + ", ".join(not_in_file),
                columns=not_in_file,
            )

        window_kind = definition["window_kind"]
        min_days = int(definition["min_window_days"] or 0)
        valid: list[_Row] = []
        errors: list[dict[str, Any]] = []
        rows_read = 0

        for line, raw in rows:
            rows_read += 1
            row_errors: list[tuple[str, str, str]] = []
            entity_key = _text(raw.get(columns["entity_key"]))
            if not entity_key:
                row_errors.append((columns["entity_key"], "entity key is empty", BAD_ROWS))

            try:
                numerator = _parse_number(raw.get(columns["numerator"]), columns["numerator"])
            except ValueError as exc:
                numerator = None
                row_errors.append((columns["numerator"], str(exc), BAD_ROWS))

            denominator: Decimal | None = None
            if "denominator" in columns:
                try:
                    denominator = _parse_number(
                        raw.get(columns["denominator"]), columns["denominator"]
                    )
                except ValueError as exc:
                    row_errors.append((columns["denominator"], str(exc), BAD_ROWS))

            try:
                window_start = _parse_date(raw.get(columns["window_start"]))
            except ValueError as exc:
                window_start = None
                row_errors.append((columns["window_start"], str(exc), WINDOW_INVALID))
            try:
                window_end = _parse_date(raw.get(columns["window_end"]))
            except ValueError as exc:
                window_end = None
                row_errors.append((columns["window_end"], str(exc), WINDOW_INVALID))

            if window_start is not None and window_end is not None:
                if window_kind == "instant":
                    if window_start != window_end:
                        row_errors.append(
                            (columns["window_start"], "instant metric requires start == end",
                             WINDOW_INVALID)
                        )
                elif window_kind == "period":
                    if window_end < window_start:
                        row_errors.append(
                            (columns["window_end"], "window end precedes start", WINDOW_INVALID)
                        )
                    elif (window_end - window_start).days + 1 < min_days:
                        row_errors.append(
                            (
                                columns["window_end"],
                                f"window has {(window_end - window_start).days + 1} days, "
                                f"definition needs {min_days}",
                                WINDOW_INVALID,
                            )
                        )

            if row_errors:
                if len(errors) < MAX_REPORTED_ERRORS:
                    for column, message, code in row_errors:
                        errors.append(
                            {
                                "row": line,
                                "column": column,
                                "code": code,
                                "message": message,
                            }
                        )
                continue

            institution = _text(raw.get(columns["institution"])) if "institution" in columns else ""
            product = _text(raw.get(columns["product"])) if "product" in columns else ""
            valid.append(
                _Row(
                    line=line,
                    entity_key=entity_key,
                    numerator=numerator,
                    denominator=denominator,
                    window_start=window_start,
                    window_end=window_end,
                    institution=institution or None,
                    product=product or None,
                )
            )

        return valid, errors, rows_read

    def _count(self, metric_id: str, definition_version: str) -> int:
        rows = self._meta.query(
            "SELECT COUNT(*) AS n FROM platform.metric_observation "
            "WHERE metric_id = %s AND definition_version = %s",
            (metric_id, definition_version),
        )
        return int(rows[0]["n"]) if rows else 0

    def load(
        self,
        *,
        file: str,
        metric_id: str,
        mapping_path: str,
        apply: bool = False,
        data_source: str,
        fixture: bool,
    ) -> dict[str, Any]:
        """Validate and (optionally) upsert one batch.

        Returns a structured result; rejections keep ``ok=false`` and never
        write anything.
        """
        base: dict[str, Any] = {
            "ok": False,
            "metricId": metric_id,
            "file": file,
            "mapping": mapping_path,
            "dryRun": not apply,
            "dataSource": data_source,
            "fixture": fixture,
        }
        try:
            if data_source not in ("fixture", "business"):
                raise _Reject(
                    BAD_SOURCE,
                    f"dataSource must be fixture or business, got {data_source!r}",
                )
            if fixture != (data_source == "fixture"):
                raise _Reject(
                    BAD_SOURCE,
                    "fixture must be true for data_source=fixture and false otherwise",
                )

            definition = self._definition(metric_id)
            base["definitionVersion"] = definition["definition_version"]
            base["metricKind"] = definition["metric_kind"]
            base["windowKind"] = definition["window_kind"]

            mapping = _read_mapping(Path(mapping_path))
            if mapping["metric_id"] and mapping["metric_id"] != metric_id:
                raise _Reject(
                    MAPPING_INVALID,
                    f"mapping targets {mapping['metric_id']}, command targets {metric_id}",
                )
            columns = mapping["columns"]

            header, rows = _read_table(Path(file))
            try:
                valid, errors, rows_read = self._validate_rows(
                    header,
                    rows,
                    columns,
                    definition,
                    require_denominator=definition["metric_kind"] == "ratio",
                )
            finally:
                close = getattr(rows, "close", None)
                if callable(close):
                    close()
            base["rowsRead"] = rows_read
            base["rowsValid"] = len(valid)
            base["errorCount"] = len(errors)
            base["errors"] = errors
            if errors:
                codes = {item["code"] for item in errors}
                base["errorCode"] = (
                    WINDOW_INVALID if codes == {WINDOW_INVALID} else BAD_ROWS
                )
                base["message"] = f"{len(errors)} row error(s); nothing was written"
                unchanged = self._count(metric_id, definition["definition_version"])
                base["rowsBefore"] = unchanged
                base["rowsAfter"] = unchanged
                return base

            definition_version = definition["definition_version"]
            before = self._count(metric_id, definition_version)
            base["rowsBefore"] = before
            base["rowsUpserted"] = len(valid)
            if not apply:
                base["rowsAfter"] = before
                base["ok"] = True
                return base

            params = [
                (
                    metric_id,
                    definition_version,
                    row.institution,
                    row.product,
                    row.entity_key,
                    row.window_start if definition["window_kind"] == "instant" else None,
                    row.window_start if definition["window_kind"] == "period" else None,
                    row.window_end if definition["window_kind"] == "period" else None,
                    row.numerator,
                    row.denominator,
                    row.window_start,
                    row.window_end,
                    data_source,
                    fixture,
                )
                for row in valid
            ]
            try:
                with self._meta.tx() as tx:
                    tx.executemany(_UPSERT_SQL, params)
            except Exception as exc:  # noqa: BLE001 - normalized into a typed rejection
                after = self._count(metric_id, definition_version)
                base["rowsAfter"] = after
                base["errorCode"] = DB_FAILED
                base["message"] = f"transaction rolled back: {exc}"
                return base

            after = self._count(metric_id, definition_version)
            base["rowsAfter"] = after
            base["ok"] = True
            return base
        except _Reject as exc:
            base["errorCode"] = exc.code
            base["message"] = exc.message
            if exc.detail:
                base["detail"] = exc.detail
            return base
