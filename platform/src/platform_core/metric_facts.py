"""Entity facts for time-series metrics: CSV loader + observation projector.

Two fact tables back the two v3 metrics that had only definition cards:

* ``platform.ins_payment_record``  -- installment-level payment/status history
* ``platform.loan_installment_plan`` -- installment-level repayment plan

They are independent fact tables. The calculator never reads them: the
projector aggregates them through the SQL function named in
``metric_definition.fact_function`` for an explicit observation window and
upserts the result into ``platform.metric_observation``. That keeps the
instant/period contract in one place (the function) and keeps fixture/business
provenance on every row.

Both steps are dry-run by default; nothing is written until ``--apply``.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterator

from .adapters.metadata_pg import MetadataPg

KIND_INVALID = "E_FACT_KIND_INVALID"
FILE_UNREADABLE = "E_FACT_FILE_UNREADABLE"
HEADER_INVALID = "E_FACT_HEADER_INVALID"
MISSING_COLUMN = "E_FACT_MISSING_COLUMN"
BAD_ROWS = "E_FACT_BAD_ROWS"
SOURCE_INVALID = "E_FACT_SOURCE_INVALID"
DB_FAILED = "E_FACT_DB_FAILED"

METRIC_NOT_FOUND = "E_METRIC_NOT_FOUND"
NOT_PUBLISHABLE = "E_METRIC_NOT_PUBLISHABLE"
FORMULA_DISABLED = "E_METRIC_FORMULA_DISABLED"
FACT_MISSING = "E_METRIC_FACT_SOURCE_MISSING"
FACT_INVALID = "E_METRIC_FACT_SOURCE_INVALID"
WINDOW_INSUFFICIENT = "E_METRIC_WINDOW_INSUFFICIENT"

MAX_REPORTED_ERRORS = 100
_FACT_FN = re.compile(r"^platform\.metric_fact_[a-z0-9_]+$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

_OBS_UPSERT = """
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
    def __init__(self, code: str, message: str, **detail: Any) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.detail = detail


@dataclass(frozen=True)
class _Spec:
    table: str
    columns: tuple[str, ...]
    required: tuple[str, ...]
    date_columns: tuple[str, ...]
    decimal_columns: tuple[str, ...]
    int_columns: tuple[str, ...]
    enum_columns: dict[str, tuple[str, ...]]
    upsert_sql: str


_INSURANCE = _Spec(
    table="platform.ins_payment_record",
    columns=(
        "policy_no", "product", "installment_no", "due_date", "due_amount",
        "paid_amount", "paid_date", "payment_status", "policy_status",
        "status_as_of", "institution",
    ),
    required=(
        "policy_no", "product", "installment_no", "due_date", "due_amount",
        "payment_status", "policy_status", "status_as_of",
    ),
    date_columns=("due_date", "paid_date", "status_as_of"),
    decimal_columns=("due_amount", "paid_amount"),
    int_columns=("installment_no",),
    enum_columns={
        "payment_status": ("paid", "unpaid", "waived"),
        "policy_status": ("in_force", "lapsed", "surrendered", "cancelled"),
    },
    upsert_sql="""
INSERT INTO platform.ins_payment_record
  (policy_no, product, installment_no, due_date, due_amount, paid_amount,
   paid_date, payment_status, policy_status, status_as_of, institution,
   data_source, fixture)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT ON CONSTRAINT ins_payment_record_key DO UPDATE SET
  product = EXCLUDED.product,
  due_date = EXCLUDED.due_date,
  due_amount = EXCLUDED.due_amount,
  paid_amount = EXCLUDED.paid_amount,
  paid_date = EXCLUDED.paid_date,
  payment_status = EXCLUDED.payment_status,
  policy_status = EXCLUDED.policy_status,
  institution = EXCLUDED.institution,
  fixture = EXCLUDED.fixture
""",
)

_LOAN = _Spec(
    table="platform.loan_installment_plan",
    columns=(
        "agreement_id", "installment_no", "due_date", "due_amount",
        "paid_amount", "paid_date", "overdue_days", "status_as_of",
        "institution",
    ),
    required=(
        "agreement_id", "installment_no", "due_date", "due_amount",
        "overdue_days", "status_as_of",
    ),
    date_columns=("due_date", "paid_date", "status_as_of"),
    decimal_columns=("due_amount", "paid_amount"),
    int_columns=("installment_no", "overdue_days"),
    enum_columns={},
    upsert_sql="""
INSERT INTO platform.loan_installment_plan
  (agreement_id, installment_no, due_date, due_amount, paid_amount, paid_date,
   overdue_days, status_as_of, institution, data_source, fixture)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT ON CONSTRAINT loan_installment_plan_key DO UPDATE SET
  due_date = EXCLUDED.due_date,
  due_amount = EXCLUDED.due_amount,
  paid_amount = EXCLUDED.paid_amount,
  paid_date = EXCLUDED.paid_date,
  overdue_days = EXCLUDED.overdue_days,
  institution = EXCLUDED.institution,
  fixture = EXCLUDED.fixture
""",
)

_KINDS = {"insurance_payment": _INSURANCE, "loan_installment": _LOAN}


def _spec(
    table: str,
    key: str,
    columns: tuple[str, ...],
    *,
    dates: tuple[str, ...] = (),
    decimals: tuple[str, ...] = (),
    ints: tuple[str, ...] = (),
    enums: dict[str, tuple[str, ...]] | None = None,
) -> _Spec:
    """Build a v6 fact spec; every declared column is required in the CSV."""
    updates = ", ".join(f"{name} = EXCLUDED.{name}" for name in columns)
    placeholders = ", ".join(["%s"] * (len(columns) + 2))
    column_sql = ", ".join(columns + ("data_source", "fixture"))
    return _Spec(
        table=table,
        columns=columns,
        required=columns,
        date_columns=dates,
        decimal_columns=decimals,
        int_columns=ints,
        enum_columns=enums or {},
        upsert_sql=(
            f"INSERT INTO {table} ({column_sql}) VALUES ({placeholders})\n"
            f"ON CONFLICT ON CONSTRAINT {key} DO UPDATE SET {updates}"
        ),
    )


_COLLECTION_RECOVERY = _spec(
    "platform.bank_collection_recovery",
    "bank_collection_recovery_key",
    ("case_id", "recovery_date", "principal_recovered", "interest_recovered",
     "fee_recovered", "recovery_channel"),
    dates=("recovery_date",),
    decimals=("principal_recovered", "interest_recovered", "fee_recovered"),
)

_KINDS.update(
    {
        "bank_credit_application": _spec(
            "platform.bank_credit_application",
            "bank_credit_application_key",
            ("application_id", "customer_no", "product", "channel", "institution",
             "accept_date", "decision_date", "decision_status", "requested_amount",
             "duplicate_group_id", "first_flag", "test_flag", "internal_flag"),
            dates=("accept_date", "decision_date"),
            decimals=("requested_amount",),
            enums={"decision_status": ("approved", "rejected", "pending", "withdrawn", "voided")},
        ),
        "bank_credit_facility": _spec(
            "platform.bank_credit_facility",
            "bank_credit_facility_key",
            ("agreement_id", "customer_no", "product", "institution",
             "approved_limit", "drawn_principal", "currency", "fx_rate",
             "limit_type", "facility_status", "effective_from", "effective_to",
             "internal_flag", "test_flag", "status_as_of"),
            dates=("effective_from", "effective_to", "status_as_of"),
            decimals=("approved_limit", "drawn_principal", "fx_rate"),
            enums={
                "limit_type": ("revolving", "term", "overdraft"),
                "facility_status": ("active", "frozen", "expired", "cancelled"),
            },
        ),
        "bank_collection_case": _spec(
            "platform.bank_collection_case",
            "bank_collection_case_key",
            ("case_id", "account_id", "customer_no", "product", "institution",
             "outstanding_principal", "case_status", "status_as_of"),
            dates=("status_as_of",),
            decimals=("outstanding_principal",),
            enums={"case_status": ("collecting", "written_off", "transferred",
                                   "restructured", "closed")},
        ),
        "bank_collection_recovery": _COLLECTION_RECOVERY,
        "bank_npl_snapshot": _spec(
            "platform.bank_npl_snapshot",
            "bank_npl_snapshot_key",
            ("asset_id", "institution", "product", "risk_class", "npl_balance", "as_of"),
            dates=("as_of",),
            decimals=("npl_balance",),
            enums={"risk_class": ("substandard", "doubtful", "loss")},
        ),
        "bank_disposal_event": _spec(
            "platform.bank_disposal_event",
            "bank_disposal_event_key",
            ("event_id", "asset_id", "institution", "product", "disposal_type",
             "completion_date", "gross_amount", "recovery_cash",
             "recovery_noncash_fv", "disposal_fee"),
            dates=("completion_date",),
            decimals=("gross_amount", "recovery_cash", "recovery_noncash_fv", "disposal_fee"),
            enums={"disposal_type": ("cash", "transfer", "asset_swap", "judicial", "write_off")},
        ),
        "ins_policy": _spec(
            "platform.ins_policy",
            "ins_policy_key",
            ("policy_no", "product", "channel", "institution", "customer_no",
             "issue_date", "policy_year", "premium_type", "premium_amount",
             "first_year_premium", "is_investment_linked", "reversal_amount",
             "policy_status", "status_as_of"),
            dates=("issue_date", "status_as_of"),
            decimals=("premium_amount", "first_year_premium", "reversal_amount"),
            ints=("policy_year",),
            enums={
                "premium_type": ("single", "regular"),
                "policy_status": ("in_force", "lapsed", "surrendered", "cancelled"),
            },
        ),
        "cust_master": _spec(
            "platform.cust_master",
            "cust_master_key",
            ("customer_no", "registration_date", "channel", "segment", "institution",
             "customer_status", "as_of"),
            dates=("registration_date", "as_of"),
            enums={"customer_status": ("active", "closed")},
        ),
        "cust_product_holding": _spec(
            "platform.cust_product_holding",
            "cust_product_holding_key",
            ("holding_id", "customer_no", "product_category", "holding_status",
             "as_of", "institution"),
            dates=("as_of",),
            enums={
                "product_category": ("deposit", "loan", "insurance", "wealth", "card"),
                "holding_status": ("active", "closed"),
            },
        ),
    }
)


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _parse_date(value: Any, column: str) -> date:
    text = _text(value)
    if not _DATE_RE.match(text):
        raise ValueError(f"{column} must be YYYY-MM-DD, got {value!r}")
    return date.fromisoformat(text)


def _parse_decimal(value: Any, column: str) -> Decimal:
    text = _text(value)
    if not text:
        raise ValueError(f"{column} is empty")
    try:
        number = Decimal(text)
    except InvalidOperation:
        raise ValueError(f"{column} is not numeric: {text!r}") from None
    if not number.is_finite() or number < 0:
        raise ValueError(f"{column} must be a finite non-negative number: {text!r}")
    return number


def _parse_int(value: Any, column: str, minimum: int = 0) -> int:
    text = _text(value)
    if not text:
        raise ValueError(f"{column} is empty")
    try:
        number = int(text)
    except ValueError:
        raise ValueError(f"{column} is not an integer: {text!r}") from None
    if number < minimum:
        raise ValueError(f"{column} must be >= {minimum}: {text!r}")
    return number


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


class FactLoader:
    """Validate a whole entity-fact batch, then upsert it in one transaction."""

    def __init__(self, metadata: MetadataPg) -> None:
        self._meta = metadata

    def _count(self, spec: _Spec, data_source: str) -> int:
        rows = self._meta.query(
            f"SELECT COUNT(*) AS n FROM {spec.table} WHERE data_source = %s",
            (data_source,),
        )
        return int(rows[0]["n"]) if rows else 0

    def load(
        self,
        *,
        kind: str,
        file: str,
        apply: bool = False,
        data_source: str = "fixture",
        fixture: bool = True,
    ) -> dict[str, Any]:
        base: dict[str, Any] = {
            "ok": False,
            "kind": kind,
            "file": file,
            "dryRun": not apply,
            "dataSource": data_source,
            "fixture": fixture,
        }
        try:
            spec = _KINDS.get(kind)
            if spec is None:
                raise _Reject(KIND_INVALID, f"unknown fact kind: {kind}")
            if data_source not in ("fixture", "business"):
                raise _Reject(SOURCE_INVALID, "dataSource must be fixture or business")
            if fixture != (data_source == "fixture"):
                raise _Reject(SOURCE_INVALID, "fixture must match dataSource")

            path = Path(file)
            try:
                header, rows = _iter_csv(path)
            except OSError as exc:
                raise _Reject(FILE_UNREADABLE, f"cannot read {file}: {exc}") from None

            unknown = sorted(set(header) - set(spec.columns))
            if unknown:
                raise _Reject(
                    HEADER_INVALID,
                    "unknown column(s): " + ", ".join(unknown),
                    columns=unknown,
                )
            missing = [name for name in spec.required if name not in header]
            if missing:
                raise _Reject(
                    MISSING_COLUMN,
                    "missing required column(s): " + ", ".join(missing),
                    columns=missing,
                )

            valid: list[dict[str, Any]] = []
            errors: list[dict[str, Any]] = []
            rows_read = 0
            try:
                for line, raw in rows:
                    rows_read += 1
                    try:
                        record = self._validate_row(spec, raw)
                    except ValueError as exc:
                        if len(errors) < MAX_REPORTED_ERRORS:
                            errors.append(
                                {"row": line, "code": BAD_ROWS, "message": str(exc)}
                            )
                        continue
                    valid.append(record)
            finally:
                close = getattr(rows, "close", None)
                if callable(close):
                    close()

            before = self._count(spec, data_source)
            base.update(
                {
                    "table": spec.table,
                    "rowsRead": rows_read,
                    "rowsValid": len(valid),
                    "errorCount": len(errors),
                    "errors": errors,
                    "rowsBefore": before,
                }
            )
            if errors:
                base["errorCode"] = BAD_ROWS
                base["message"] = f"{len(errors)} row error(s); nothing was written"
                base["rowsAfter"] = before
                return base

            base["rowsUpserted"] = len(valid)
            if not apply:
                base["rowsAfter"] = before
                base["ok"] = True
                return base

            params = [
                tuple(record[name] for name in spec.columns) + (data_source, fixture)
                for record in valid
            ]
            try:
                with self._meta.tx() as tx:
                    tx.executemany(spec.upsert_sql, params)
            except Exception as exc:  # noqa: BLE001 - normalized typed rejection
                base["rowsAfter"] = self._count(spec, data_source)
                base["errorCode"] = DB_FAILED
                base["message"] = f"transaction rolled back: {exc}"
                return base

            base["rowsAfter"] = self._count(spec, data_source)
            base["ok"] = True
            return base
        except _Reject as exc:
            base["errorCode"] = exc.code
            base["message"] = exc.message
            if exc.detail:
                base["detail"] = exc.detail
            return base

    @staticmethod
    def _validate_row(spec: _Spec, raw: dict[str, Any]) -> dict[str, Any]:
        record: dict[str, Any] = {}
        for name in spec.columns:
            if name in spec.date_columns:
                text = _text(raw.get(name))
                if text:
                    record[name] = _parse_date(text, name)
                elif name == "paid_date":
                    record[name] = None
                else:
                    raise ValueError(f"{name} is empty")
            elif name in spec.decimal_columns:
                text = _text(raw.get(name))
                if text:
                    record[name] = _parse_decimal(text, name)
                elif name == "paid_amount":
                    record[name] = Decimal("0")
                else:
                    raise ValueError(f"{name} is empty")
            elif name in spec.int_columns:
                minimum = 1 if name == "installment_no" else 0
                record[name] = _parse_int(raw.get(name), name, minimum)
            elif name in spec.enum_columns:
                text = _text(raw.get(name))
                if text not in spec.enum_columns[name]:
                    raise ValueError(
                        f"{name} must be one of {', '.join(spec.enum_columns[name])}"
                    )
                record[name] = text
            else:
                text = _text(raw.get(name))
                if name in spec.required and not text:
                    raise ValueError(f"{name} is empty")
                record[name] = text or None
        return record


class MetricProjector:
    """Aggregate entity facts over the definition's window into observations."""

    def __init__(self, metadata: MetadataPg) -> None:
        self._meta = metadata

    def _count(self, metric_id: str, version: str) -> int:
        rows = self._meta.query(
            "SELECT COUNT(*) AS n FROM platform.metric_observation "
            "WHERE metric_id = %s AND definition_version = %s",
            (metric_id, version),
        )
        return int(rows[0]["n"]) if rows else 0

    def project(
        self,
        *,
        metric_id: str,
        window_start: date,
        window_end: date,
        data_source: str = "fixture",
        apply: bool = True,
    ) -> dict[str, Any]:
        fixture = data_source == "fixture"
        base: dict[str, Any] = {
            "ok": False,
            "metricId": metric_id,
            "dataSource": data_source,
            "fixture": fixture,
            "dryRun": not apply,
            "window": {
                "start": window_start.isoformat(),
                "end": window_end.isoformat(),
            },
        }
        try:
            rows = self._meta.query(
                "SELECT metric_id, definition_version, publishable, formula_disabled, "
                "window_kind, min_window_days, fact_function "
                "FROM platform.metric_definition WHERE metric_id = %s",
                (metric_id,),
            )
            if not rows:
                raise _Reject(METRIC_NOT_FOUND, f"unknown metric: {metric_id}")
            definition = rows[0]
            base["definitionVersion"] = definition["definition_version"]
            if definition["formula_disabled"]:
                raise _Reject(FORMULA_DISABLED, f"metric formula is disabled: {metric_id}")
            function = definition["fact_function"]
            if not function:
                raise _Reject(
                    FACT_MISSING,
                    f"metric has no entity fact source: {metric_id}",
                )
            if not _FACT_FN.match(function):
                raise _Reject(FACT_INVALID, f"invalid fact function name: {function!r}")

            window_kind = definition["window_kind"]
            if data_source not in ("fixture", "business"):
                raise _Reject(SOURCE_INVALID, "dataSource must be fixture or business")
            if window_kind == "instant":
                if window_start != window_end:
                    raise _Reject(
                        WINDOW_INSUFFICIENT,
                        "instant metric requires window_start == window_end",
                    )
            elif window_kind == "period":
                days = (window_end - window_start).days + 1
                if window_end < window_start:
                    raise _Reject(WINDOW_INSUFFICIENT, "window end precedes start")
                min_days = int(definition["min_window_days"] or 0)
                if days < min_days:
                    raise _Reject(
                        WINDOW_INSUFFICIENT,
                        f"window has {days} days, needs {min_days}",
                    )
            else:
                raise _Reject(FACT_INVALID, f"unsupported window kind: {window_kind}")

            fact_rows = self._meta.query(
                f"SELECT * FROM {function}(%s, %s, %s)",
                (window_start, window_end, data_source),
            )
            base["rowsValid"] = len(fact_rows)
            base["rowsBefore"] = self._count(metric_id, definition["definition_version"])

            if not apply:
                base["rowsAfter"] = base["rowsBefore"]
                base["ok"] = True
                return base

            params: list[tuple[Any, ...]] = []
            for row in fact_rows:
                if row.get("data_source") != data_source or bool(row.get("fixture")) != fixture:
                    raise _Reject(
                        FACT_INVALID,
                        "fact row provenance does not match the requested source",
                    )
                if row.get("numerator") is None:
                    raise _Reject(FACT_INVALID, "fact row has no numerator")
                instant = window_kind == "instant"
                params.append(
                    (
                        metric_id,
                        definition["definition_version"],
                        row.get("institution"),
                        row.get("product"),
                        row["entity_key"],
                        window_start if instant else None,
                        None if instant else window_start,
                        None if instant else window_end,
                        row["numerator"],
                        row.get("denominator"),
                        row["window_start"],
                        row["window_end"],
                        data_source,
                        fixture,
                    )
                )
            try:
                with self._meta.tx() as tx:
                    tx.executemany(_OBS_UPSERT, params)
            except Exception as exc:  # noqa: BLE001 - normalized typed rejection
                base["rowsAfter"] = self._count(metric_id, definition["definition_version"])
                base["errorCode"] = DB_FAILED
                base["message"] = f"transaction rolled back: {exc}"
                return base

            base["rowsProjected"] = len(params)
            base["rowsAfter"] = self._count(metric_id, definition["definition_version"])
            base["ok"] = True
            return base
        except _Reject as exc:
            base["errorCode"] = exc.code
            base["message"] = exc.message
            if exc.detail:
                base["detail"] = exc.detail
            return base
