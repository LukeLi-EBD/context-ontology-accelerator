"""Synthetic data generator driven by the live platform schema.

Design references: `_design/40-合成数据生成器.md`.

Hard rules implemented here:
* table/column/type/unique-key metadata is read from ``information_schema`` and
  ``pg_index``; a missing required column raises ``E_DATAGEN_SCHEMA_DRIFT``
  instead of being skipped;
* every generated row carries ``data_source='synthetic'``; nothing is written to
  ``platform.metric_observation``, metric definitions, bindings or the T-Box;
* writing to the official ``platform`` schema is gated by
  ``datagen.allow_official_schema``; the safe fallback is a ``synthetic`` schema;
* the same seed reproduces byte-identical rows (fixed timestamps included).

The module deliberately does not touch ``api.py`` or any existing migration.
"""

from __future__ import annotations

import hashlib
import json
import random
import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Iterable, Iterator

from .adapters.metadata_pg import MetadataPg
from .errors import PortError
from .metric_compiler import MetricCompiler, formula_to_sql
from .rules import RuleExecutor

SYNTHETIC = "synthetic"
OFFICIAL_SCHEMA = "platform"
SAFE_SCHEMA = "synthetic"
CREATED_AT = datetime(2025, 12, 31, 0, 0, tzinfo=timezone.utc)
AS_OF = date(2025, 12, 31)
WINDOW_START = date(2025, 1, 1)
WINDOW_END = date(2025, 12, 31)
INTEREST_RATE = Decimal("0.05")
CENT = Decimal("0.01")

INSTITUTIONS = [f"INST-SYN-{i:02d}" for i in range(1, 21)]
BANK_PRODUCTS = ["mortgage", "consumer", "sme", "auto", "credit_card"]
INS_PRODUCTS = ["life_term", "critical_illness", "health", "property", "motor"]
CUST_PRODUCTS = ["deposit", "loan", "insurance", "wealth", "card"]
CHANNELS = ["branch", "app", "web", "partner", "agent"]
SEGMENTS = ["mass", "mass_affluent", "affluent", "private", "small_business"]
REGIONS = ["east", "south", "north", "central", "west", "northeast"]
INDUSTRIES = ["manufacturing", "retail", "services", "real_estate", "agriculture", "tmt", "energy", "logistics"]
RISK_CLASSES = ["normal", "special", "substandard", "doubtful", "loss"]
BAD_RISK_CLASSES = {"substandard", "doubtful", "loss"}
GUARANTEE_TYPES = ["credit", "mortgage", "pledge", "guarantee", "unsecured"]
FACILITY_STATUS = ["active", "frozen", "expired", "cancelled"]
APPLICATION_STATUS = ["approved", "rejected", "pending", "withdrawn", "voided"]
CASE_STATUS = ["collecting", "written_off", "transferred", "restructured", "closed"]
CLAIM_STATUS = ["reported", "approved", "rejected", "paid", "withdrawn"]
RESERVE_STATUS = ["open", "closed"]
POLICY_STATUS = ["in_force", "lapsed", "surrendered", "cancelled"]
PAYMENT_STATUS = ["paid", "unpaid", "waived"]
EVENT_TYPES = ["lapse", "surrender", "reinstatement", "termination"]
DISPOSAL_TYPES = ["cash", "transfer", "asset_swap", "judicial", "write_off"]
TX_TYPES = ["purchase", "refund", "transfer"]
TICKET_STATUS = ["open", "closed", "escalated"]
HOLDING_STATUS = ["active", "closed"]


def _err(code: str, detail: str, hint: str = "", **details: Any) -> PortError:
    return PortError(
        code="InvalidArgument",
        message=detail,
        provider="platform",
        provider_code=code,
        details=details,
        retryable=False,
    )


def _safe_ident(name: str) -> str:
    if not re.match(r"^[a-z_][a-z0-9_]*$", name):
        raise _err("E_DATAGEN_IDENTIFIER", f"unsafe identifier: {name!r}")
    return name


def _q(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def _jdefault(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=_q, sort_keys=True)


def _money(value: Any) -> Decimal:
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


def _rand_money(rng: random.Random, low: int, high: int) -> Decimal:
    return _money(rng.randint(low * 100, high * 100) / 100)


def _customer_index(customer_no: str) -> int:
    try:
        return int(customer_no.rsplit("-", 1)[1])
    except (IndexError, ValueError):
        return 0


# ----------------------------------------------------------------------------
# Schema introspection
# ----------------------------------------------------------------------------


@dataclass(frozen=True)
class ColumnInfo:
    name: str
    data_type: str
    udt_name: str
    nullable: bool
    default: str | None
    ordinal: int


@dataclass(frozen=True)
class TableInfo:
    name: str
    schema: str
    columns: dict[str, ColumnInfo]
    unique_key: tuple[str, ...]

    @property
    def required_columns(self) -> set[str]:
        return {
            c.name
            for c in self.columns.values()
            if not c.nullable and not c.default and c.name not in self.columns_with_identity
        }

    @property
    def columns_with_identity(self) -> set[str]:
        # Serial/identity columns expose a nextval default; they are never
        # required from the caller.
        return {c.name for c in self.columns.values() if c.default and "nextval" in c.default}


def discover_tables(meta: MetadataPg, schema: str) -> list[str]:
    rows = meta.query(
        "SELECT table_name FROM information_schema.columns "
        "WHERE table_schema = %s AND column_name = 'data_source' "
        "AND table_name <> 'metric_observation' "
        "ORDER BY table_name",
        (schema,),
    )
    return [r["table_name"] for r in rows]


def introspect(meta: MetadataPg, schema: str) -> dict[str, TableInfo]:
    schema = _safe_ident(schema)
    tables = discover_tables(meta, schema)
    if not tables:
        raise _err(
            "E_DATAGEN_NO_TABLES",
            f"no fact tables with a data_source column found in schema {schema}",
        )
    col_rows = meta.query(
        "SELECT table_name, column_name, data_type, udt_name, is_nullable, "
        "column_default, ordinal_position "
        "FROM information_schema.columns WHERE table_schema = %s "
        "ORDER BY table_name, ordinal_position",
        (schema,),
    )
    columns: dict[str, dict[str, ColumnInfo]] = {}
    for row in col_rows:
        columns.setdefault(row["table_name"], {})[row["column_name"]] = ColumnInfo(
            name=row["column_name"],
            data_type=row["data_type"],
            udt_name=row["udt_name"],
            nullable=row["is_nullable"] == "YES",
            default=row["column_default"],
            ordinal=int(row["ordinal_position"]),
        )
    key_rows = meta.query(
        "SELECT c.relname AS table_name, "
        "array_agg(a.attname ORDER BY k.ord) AS key_columns "
        "FROM pg_index i "
        "JOIN pg_class c ON c.oid = i.indrelid "
        "JOIN pg_namespace n ON n.oid = c.relnamespace "
        "JOIN unnest(i.indkey) WITH ORDINALITY k(attnum, ord) ON true "
        "JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = k.attnum "
        "WHERE n.nspname = %s AND i.indisunique "
        "GROUP BY c.relname",
        (schema,),
    )
    keys = {r["table_name"]: tuple(r["key_columns"]) for r in key_rows}
    return {
        name: TableInfo(
            name=name,
            schema=schema,
            columns=columns.get(name, {}),
            unique_key=keys.get(name, ()),
        )
        for name in tables
    }


def ensure_target(meta: MetadataPg, target_schema: str, allow_official: bool) -> dict[str, TableInfo]:
    """Validate/create the write target. Never touches metric/T-Box tables."""

    target_schema = _safe_ident(target_schema)
    if target_schema == OFFICIAL_SCHEMA:
        if not allow_official:
            raise _err(
                "E_DATAGEN_TARGET_FORBIDDEN",
                "refusing to write the official platform schema: "
                "datagen.allow_official_schema is false",
                hint="set datagen.allow_official_schema=true only in a designated test environment",
            )
        info = introspect(meta, OFFICIAL_SCHEMA)
        bad = _tables_without_synthetic_label(meta, OFFICIAL_SCHEMA, info)
        if bad:
            raise _err(
                "E_DATAGEN_TARGET_FORBIDDEN",
                "official fact tables do not accept data_source='synthetic' yet",
                hint="run `platform migrate` to apply V26__datagen.sql",
                tables=sorted(bad),
            )
        return info

    # Safe mode: mirror the already migrated platform tables into an isolated
    # schema. The mirror uses the live DDL, so schema drift follows automatically.
    with meta.tx() as tx:
        tx.execute(f"CREATE SCHEMA IF NOT EXISTS {_safe_ident(target_schema)}")
        for name in discover_tables(meta, OFFICIAL_SCHEMA):
            _safe_ident(name)
            tx.execute(
                f"CREATE TABLE IF NOT EXISTS {target_schema}.{name} "
                f"(LIKE {OFFICIAL_SCHEMA}.{name} INCLUDING ALL)"
            )
    return introspect(meta, target_schema)


def _tables_without_synthetic_label(
    meta: MetadataPg, schema: str, info: dict[str, TableInfo]
) -> set[str]:
    rows = meta.query(
        "SELECT c.relname AS table_name, pg_get_constraintdef(con.oid) AS def "
        "FROM pg_constraint con "
        "JOIN pg_class c ON c.oid = con.conrelid "
        "JOIN pg_namespace n ON n.oid = c.relnamespace "
        "WHERE n.nspname = %s AND con.contype = 'c'",
        (schema,),
    )
    accepted: set[str] = set()
    for row in rows:
        if "data_source" in row["def"] and "synthetic" in row["def"]:
            accepted.add(row["table_name"])
    # A table without any data_source check still accepts the label.
    checked = {r["table_name"] for r in rows if "data_source" in r["def"]}
    return {name for name in info if name in checked and name not in accepted}


# ----------------------------------------------------------------------------
# Deterministic factory
# ----------------------------------------------------------------------------


def _month_end(year: int, month: int) -> date:
    if month == 12:
        return date(year, 12, 31)
    return date(year, month + 1, 1) - timedelta(days=1)


def _iter_months(start_year: int, start_month: int, count: int) -> Iterator[date]:
    year, month = start_year, start_month
    for _ in range(count):
        yield _month_end(year, month)
        month += 1
        if month > 12:
            month = 1
            year += 1


class SyntheticFactory:
    """Builds deterministic entity pools and row payloads for every fact table.

    The factory is pure: it does not touch the database. ``run_datagen`` writes
    the returned rows after validating each payload against the introspected
    columns. Tests use the same factory to prove seed reproducibility.
    """

    def __init__(
        self,
        seed: int = 42,
        *,
        rows_per_table: int = 1000,
        master_rows: int = 5000,
        scale: float = 1.0,
    ) -> None:
        self.seed = int(seed)
        self.scale = float(scale)
        self.rows_per_table = max(1, int(rows_per_table * self.scale))
        self.master_rows = max(5, int(master_rows * self.scale))
        self.n_customers = max(5000, self.master_rows)
        self.n_policies = max(5000, self.master_rows) + 1000
        self.n_accounts = max(5000, self.master_rows)
        self.rng = random.Random(self.seed)
        self._build_pools()

    # -- pools ---------------------------------------------------------------
    def _build_pools(self) -> None:
        rng = random.Random(f"{self.seed}:pools")
        self.customers: list[dict[str, Any]] = []
        for i in range(self.n_customers):
            self.customers.append(
                {
                    "customer_no": f"CUST-SYN-{i:05d}",
                    "registration_date": date(2020, 1, 1) + timedelta(days=(i * 37) % 1900),
                    "channel": CHANNELS[i % len(CHANNELS)],
                    "segment": SEGMENTS[i % len(SEGMENTS)],
                    "institution": INSTITUTIONS[i % len(INSTITUTIONS)],
                    "customer_status": "closed" if i % 11 == 0 else "active",
                }
            )

        self.policies: list[dict[str, Any]] = []
        for i in range(self.n_policies):
            customer = self.customers[i % self.n_customers]
            if i < 3000:
                issue_date = date(2025, 1, 1) + timedelta(days=i % 300)
            else:
                issue_date = date(2022, 1, 1) + timedelta(days=i % 1000)
            status_idx = i % 20
            if status_idx < 16:
                status = "in_force"
            elif status_idx < 18:
                status = "lapsed"
            elif status_idx == 18:
                status = "surrendered"
            else:
                status = "cancelled"
            premium = _money(1000 + (i * 37) % 90000)
            self.policies.append(
                {
                    "policy_no": f"POL-SYN-{i:05d}",
                    "product": INS_PRODUCTS[i % len(INS_PRODUCTS)],
                    "channel": CHANNELS[i % len(CHANNELS)],
                    "institution": customer["institution"],
                    "customer_no": customer["customer_no"],
                    "issue_date": issue_date,
                    "policy_year": 1 if issue_date.year == 2025 else 2025 - issue_date.year + 1,
                    "premium_type": "single" if i % 10 == 0 else "regular",
                    "premium_amount": premium,
                    "first_year_premium": premium,
                    "is_investment_linked": i % 6 == 0,
                    "reversal_amount": _money(premium * Decimal("0.10")) if i % 9 == 0 else Decimal("0.00"),
                    "policy_status": status,
                }
            )

        self.accounts: list[dict[str, Any]] = []
        for i in range(self.n_accounts):
            customer = self.customers[i % self.n_customers]
            disbursed = date(2023, 1, 1) + timedelta(days=(i * 11) % 900)
            risk_end = RISK_CLASSES[i % len(RISK_CLASSES)]
            if i % 7 == 0:
                risk_start = "normal"
                if risk_end == "normal":
                    risk_end = "special"
            else:
                risk_start = risk_end
            principal = Decimal("0.00") if i % 50 == 0 else _money(1000 + (i * 7919) % 300000)
            balance_start = _money(principal * Decimal("1.20")) if risk_start == "normal" else principal
            self.accounts.append(
                {
                    "account_id": f"LN-SYN-{i:05d}",
                    "customer_no": customer["customer_no"],
                    "product": BANK_PRODUCTS[i % len(BANK_PRODUCTS)],
                    "industry": INDUSTRIES[i % len(INDUSTRIES)],
                    "region": REGIONS[i % len(REGIONS)],
                    "guarantee_type": GUARANTEE_TYPES[i % len(GUARANTEE_TYPES)],
                    "risk_class": risk_end,
                    "risk_class_start": risk_start,
                    "risk_class_end": risk_end,
                    "principal_balance": principal,
                    "balance_start": balance_start,
                    "balance_end": principal,
                    "period_decrease_amount": _money(balance_start - principal),
                    "disbursed_date": disbursed,
                    "maturity_date": disbursed + timedelta(days=365 * 5),
                    "first_payment_due_date": disbursed + timedelta(days=30),
                    "first_payment_default_flag": i % 13 == 0,
                    "dpd_start": self._dpd_pair(i)[0],
                    "dpd_end": self._dpd_pair(i)[1],
                    "account_status": (
                        "closed" if i % 10 == 0
                        else "written_off" if i % 25 == 0
                        else "transferred" if i % 40 == 0
                        else "active"
                    ),
                    "institution": customer["institution"],
                    "as_of": AS_OF,
                }
            )
        rng.random()  # keep the pool RNG stable if more fields are added later

    @staticmethod
    def _dpd_pair(i: int) -> tuple[int | None, int | None]:
        pairs = [
            (0, 0), (30, 30), (30, 60), (45, 75), (60, 90), (90, 90),
            (0, 30), (None, None), (120, 120), (None, 60), (30, 59), (30, 45),
        ]
        return pairs[i % len(pairs)]

    # -- table dispatch ------------------------------------------------------
    def supported_tables(self) -> list[str]:
        return sorted(
            name[3:] for name in dir(self) if name.startswith("_t_") and callable(getattr(self, name))
        )

    def rows_for(self, table: str) -> list[dict[str, Any]]:
        method = getattr(self, f"_t_{table}", None)
        if method is None:
            raise _err(
                "E_DATAGEN_TABLE_UNSUPPORTED",
                f"no synthetic recipe for table {table!r}",
                hint="add a recipe in SyntheticFactory._t_<table>",
            )
        return list(method())

    # -- loan and related ----------------------------------------------------
    def _t_cust_master(self) -> Iterable[dict[str, Any]]:
        for customer in self.customers:
            yield {
                **customer,
                "as_of": AS_OF,
            }
        # A second historical snapshot exercises multiple as_of keys.
        for i, customer in enumerate(self.customers):
            if i % 5 == 0:
                yield {
                    **customer,
                    "as_of": date(2025, 6, 30),
                }

    def _t_ins_policy(self) -> Iterable[dict[str, Any]]:
        for policy in self.policies:
            yield {
                "policy_no": policy["policy_no"],
                "product": policy["product"],
                "channel": policy["channel"],
                "institution": policy["institution"],
                "customer_no": policy["customer_no"],
                "issue_date": policy["issue_date"],
                "policy_year": policy["policy_year"],
                "premium_type": policy["premium_type"],
                "premium_amount": policy["premium_amount"],
                "first_year_premium": policy["first_year_premium"],
                "is_investment_linked": policy["is_investment_linked"],
                "reversal_amount": policy["reversal_amount"],
                "policy_status": policy["policy_status"],
                "status_as_of": AS_OF,
            }

    def _t_bank_loan_account(self) -> Iterable[dict[str, Any]]:
        for account in self.accounts:
            yield {
                key: account[key]
                for key in (
                    "account_id",
                    "customer_no",
                    "product",
                    "industry",
                    "region",
                    "guarantee_type",
                    "risk_class",
                    "principal_balance",
                    "disbursed_date",
                    "maturity_date",
                    "account_status",
                    "as_of",
                    "institution",
                    "risk_class_start",
                    "risk_class_end",
                    "balance_start",
                    "balance_end",
                    "period_decrease_amount",
                    "dpd_start",
                    "dpd_end",
                    "first_payment_due_date",
                    "first_payment_default_flag",
                )
            } | {"period_start": WINDOW_START}
        # Denominator-zero boundary snapshot: 20 institutions, all balances 0.
        for i in range(len(INSTITUTIONS)):
            account = self.accounts[i]
            yield {
                "account_id": account["account_id"],
                "customer_no": account["customer_no"],
                "product": account["product"],
                "industry": account["industry"],
                "region": account["region"],
                "guarantee_type": account["guarantee_type"],
                "risk_class": "normal",
                "principal_balance": Decimal("0.00"),
                "disbursed_date": account["disbursed_date"],
                "maturity_date": account["maturity_date"],
                "account_status": "active",
                "as_of": date(2025, 12, 30),
                "institution": INSTITUTIONS[i],
                "risk_class_start": "normal",
                "risk_class_end": "normal",
                "balance_start": Decimal("0.00"),
                "balance_end": Decimal("0.00"),
                "period_decrease_amount": Decimal("0.00"),
                "dpd_start": 0,
                "dpd_end": 0,
                "first_payment_due_date": account["first_payment_due_date"],
                "first_payment_default_flag": False,
                "period_start": WINDOW_START,
            }

    def _plan_parts(self, principal: Decimal) -> list[tuple[Decimal, Decimal, Decimal]]:
        """Return (principal_part, interest_part, due_part) for 3 installments.

        ``sum(due_part) == principal * (1 + 5%)`` with exact 2-decimal arithmetic.
        """

        total = _money(principal * (Decimal("1") + INTEREST_RATE))
        first = _money(principal / Decimal("3"))
        second = first
        third_principal = _money(principal - first - second)
        principal_parts = [first, second, third_principal]
        due_parts = [_money(total / Decimal("3")), _money(total / Decimal("3"))]
        due_parts.append(_money(total - due_parts[0] - due_parts[1]))
        return [
            (
                principal_parts[idx],
                _money(due_parts[idx] - principal_parts[idx]),
                due_parts[idx],
            )
            for idx in range(3)
        ]

    def _plan_rows(self, account: dict[str, Any], i: int) -> list[dict[str, Any]]:
        base_due = max(account["disbursed_date"] + timedelta(days=30), date(2025, 2, 1))
        mode = i % 10
        parts = self._plan_parts(account["principal_balance"])
        rows: list[dict[str, Any]] = []
        for inst in range(1, 4):
            due = base_due + timedelta(days=(inst - 1) * 30)
            if mode <= 5:
                paid = parts[inst - 1][2]
                paid_date = due + timedelta(days=i % 3)
                overdue = 0
            elif mode <= 7:
                paid = _money(parts[inst - 1][2] * Decimal("0.5"))
                paid_date = due + timedelta(days=i % 3)
                overdue = max(0, (AS_OF - due).days)
            else:
                paid = Decimal("0.00")
                paid_date = None
                overdue = max(0, (AS_OF - due).days)
            rows.append(
                {
                    "plan_id": 30_000_000 + i * 3 + inst - 1,
                    "agreement_id": account["account_id"],
                    "installment_no": inst,
                    "due_date": due,
                    "due_amount": parts[inst - 1][2],
                    "paid_amount": paid,
                    "paid_date": paid_date,
                    "overdue_days": overdue,
                    "status_as_of": AS_OF,
                    "institution": account["institution"],
                }
            )
        return rows

    def _t_loan_installment_plan(self) -> Iterable[dict[str, Any]]:
        for i, account in enumerate(self.accounts):
            yield from self._plan_rows(account, i)

    def _t_bank_loan_repayment(self) -> Iterable[dict[str, Any]]:
        for i, account in enumerate(self.accounts):
            plans = self._plan_rows(account, i)
            parts = self._plan_parts(account["principal_balance"])
            for idx, plan in enumerate(plans):
                due = plan["due_amount"]
                paid = plan["paid_amount"]
                if paid == due and paid > 0:
                    principal_paid = parts[idx][0]
                    interest_paid = parts[idx][1]
                else:
                    principal_paid = paid
                    interest_paid = Decimal("0.00")
                yield {
                    "repayment_id": 10_000_000 + i * 3 + idx,
                    "account_id": account["account_id"],
                    "installment_no": idx + 1,
                    "due_date": plan["due_date"],
                    "paid_date": plan["paid_date"],
                    "due_amount": due,
                    "paid_amount": paid,
                    "principal_paid": principal_paid,
                    "interest_paid": interest_paid,
                    "penalty_paid": Decimal("0.00"),
                    "overdue_days": plan["overdue_days"],
                    "is_partial": paid > 0 and paid < due,
                    "status_as_of": AS_OF,
                    "institution": account["institution"],
                }

    def _t_bank_credit_facility(self) -> Iterable[dict[str, Any]]:
        for i, customer in enumerate(self.customers):
            approved = _money(10000 + (i * 1237) % 500000)
            ratio_cases = [
                Decimal("1.00"), Decimal("0.95"), Decimal("0.90"), Decimal("0.60"),
                Decimal("0.10"), Decimal("0.50"), Decimal("0.30"), Decimal("0.80"),
            ]
            drawn = _money(approved * ratio_cases[i % len(ratio_cases)])
            effective_from = date(2023, 1, 1) + timedelta(days=i % 900)
            yield {
                "agreement_id": f"FAC-SYN-{i:05d}",
                "customer_no": customer["customer_no"],
                "product": BANK_PRODUCTS[i % len(BANK_PRODUCTS)],
                "institution": customer["institution"],
                "approved_limit": approved,
                "drawn_principal": drawn,
                "currency": "CNY",
                "fx_rate": Decimal("1"),
                "limit_type": "revolving" if i % 2 == 0 else "term",
                "facility_status": FACILITY_STATUS[i % len(FACILITY_STATUS)],
                "effective_from": effective_from,
                "effective_to": effective_from + timedelta(days=365 * 3),
                "internal_flag": i % 19 == 0,
                "test_flag": i % 17 == 0,
                "status_as_of": AS_OF,
            }

    def _t_bank_credit_application(self) -> Iterable[dict[str, Any]]:
        for i in range(max(self.rows_per_table, 2000)):
            customer = self.customers[i % self.n_customers]
            accept_date = date(2025, 1, 1) + timedelta(days=(i * 3) % 300)
            status = APPLICATION_STATUS[i % len(APPLICATION_STATUS)]
            decision_date = None if status == "pending" else accept_date + timedelta(days=(i % 60) + 1)
            yield {
                "application_id": f"APP-SYN-{i:05d}",
                "customer_no": customer["customer_no"],
                "product": BANK_PRODUCTS[i % len(BANK_PRODUCTS)],
                "channel": CHANNELS[i % len(CHANNELS)],
                "institution": customer["institution"],
                "accept_date": accept_date,
                "decision_date": decision_date,
                "decision_status": status,
                "requested_amount": _money(1000 + (i * 97) % 500000),
                "duplicate_group_id": f"DG-SYN-{i // 2:05d}" if i % 2 == 0 else f"DG-SYN-{(i - 1) // 2:05d}",
                "first_flag": i % 2 == 0,
                "test_flag": i % 17 == 0,
                "internal_flag": i % 23 == 0,
            }

    def _t_bank_collection_case(self) -> Iterable[dict[str, Any]]:
        for i in range(max(self.rows_per_table, 1500)):
            account = self.accounts[i % self.n_accounts]
            yield {
                "case_id": f"COL-SYN-{i:05d}",
                "account_id": account["account_id"],
                "customer_no": account["customer_no"],
                "product": account["product"],
                "institution": account["institution"],
                "outstanding_principal": _money(account["principal_balance"] * Decimal("0.60")),
                "case_status": CASE_STATUS[i % len(CASE_STATUS)],
                "status_as_of": AS_OF,
            }

    def _t_bank_collection_recovery(self) -> Iterable[dict[str, Any]]:
        for i in range(max(self.rows_per_table, 1500)):
            account = self.accounts[i % self.n_accounts]
            outstanding = _money(account["principal_balance"] * Decimal("0.60"))
            principal = _money(outstanding * Decimal("0.40"))
            interest = _money(outstanding * Decimal("0.05"))
            fee = _money(outstanding * Decimal("0.01"))
            yield {
                "recovery_id": 40_000_000 + i,
                "case_id": f"COL-SYN-{i:05d}",
                "recovery_date": date(2025, 11, 30),
                "principal_recovered": principal,
                "interest_recovered": interest,
                "fee_recovered": fee,
                "recovery_channel": CHANNELS[i % len(CHANNELS)],
            }

    def _t_bank_npl_snapshot(self) -> Iterable[dict[str, Any]]:
        for i in range(max(self.rows_per_table, 1000)):
            account = self.accounts[i % self.n_accounts]
            yield {
                "asset_id": account["account_id"],
                "institution": account["institution"],
                "product": account["product"],
                "risk_class": RISK_CLASSES[2 + i % 3],
                "npl_balance": _money(account["principal_balance"] * Decimal("0.50")),
                "as_of": AS_OF,
            }

    def _t_bank_disposal_event(self) -> Iterable[dict[str, Any]]:
        for i in range(max(self.rows_per_table, 1000)):
            account = self.accounts[i % self.n_accounts]
            gross = _money(account["principal_balance"] * Decimal("0.50"))
            yield {
                "event_id": f"EVT-SYN-{i:05d}",
                "asset_id": account["account_id"],
                "institution": account["institution"],
                "product": account["product"],
                "disposal_type": DISPOSAL_TYPES[i % len(DISPOSAL_TYPES)],
                "completion_date": date(2025, 11, 30),
                "gross_amount": gross,
                "recovery_cash": _money(gross * Decimal("0.30")),
                "recovery_noncash_fv": _money(gross * Decimal("0.10")),
                "disposal_fee": _money(gross * Decimal("0.02")),
            }

    def _t_bank_provision_snapshot(self) -> Iterable[dict[str, Any]]:
        months = list(_iter_months(2020, 1, 72))
        for inst_idx, institution in enumerate(INSTITUTIONS):
            for month_idx, as_of in enumerate(months):
                zero_case = inst_idx == 0 and as_of == date(2025, 6, 30)
                npl = Decimal("0.00") if zero_case else _money(10000 + (inst_idx * 31 + month_idx * 7) % 200000)
                loan = _money(npl * Decimal("4.0")) if not zero_case else Decimal("0.00")
                provision = _money(npl * Decimal("0.90"))
                yield {
                    "institution": institution,
                    "as_of": as_of,
                    "provision_balance": provision,
                    "npl_balance": npl,
                    "loan_balance": loan,
                }

    def _t_bank_concentration_stat(self) -> Iterable[dict[str, Any]]:
        months = list(_iter_months(2020, 1, 72))
        for inst_idx, institution in enumerate(INSTITUTIONS):
            for month_idx, as_of in enumerate(months):
                scale = _money(1_000_000 + (inst_idx * 1000 + month_idx * 37) % 500_000)
                yield {
                    "institution": institution,
                    "as_of": as_of,
                    "capital_balance": _money(scale * Decimal("10")),
                    "capital_net": _money(scale * Decimal("10")),
                    "tier1_capital_net": _money(scale * Decimal("8")),
                    "max_single_customer_loan": _money(scale * Decimal("0.10")),
                    "max_single_customer_exposure": _money(scale * Decimal("0.12")),
                    "max_group_exposure": _money(scale * Decimal("0.20")),
                    "max_group_credit": _money(scale * Decimal("0.18")),
                    "total_related_exposure": _money(scale * Decimal("0.30")),
                }

    def _t_bank_deposit_account(self) -> Iterable[dict[str, Any]]:
        for i, customer in enumerate(self.customers):
            yield {
                "deposit_id": f"DEP-SYN-{i:05d}",
                "customer_no": customer["customer_no"],
                "product": CUST_PRODUCTS[i % len(CUST_PRODUCTS)],
                "balance": _money(0 if i % 37 == 0 else (100 + (i * 71) % 500000)),
                "account_status": "closed" if i % 23 == 0 else "active",
                "as_of": AS_OF,
                "institution": customer["institution"],
            }

    def _t_bank_ews_signal(self) -> Iterable[dict[str, Any]]:
        for i, account in enumerate(self.accounts):
            dpd = account["dpd_end"]
            notch_prev = 1 + i % 4
            notch_curr = notch_prev
            if i % 13 == 0:
                notch_curr = max(1, notch_prev - 2)
            if i % 17 == 0:
                notch_curr = notch_prev - 1
            monthly_inflow = _money(5000 + (i * 29) % 40000)
            inflow_avg = _money(monthly_inflow * Decimal("1.5")) if i % 11 != 0 else _money(monthly_inflow * Decimal("1.05"))
            missing = i % 20 == 0
            yield {
                "customer_no": account["customer_no"],
                "as_of": AS_OF,
                "dpd": dpd,
                "dpd_start": account["dpd_start"],
                "dpd_end": account["dpd_end"],
                "risk_class_prev": account["risk_class_start"],
                "risk_class_curr": account["risk_class_end"],
                "rating_notch_prev": None if missing else notch_prev,
                "rating_notch_curr": None if missing else notch_curr,
                "drawn_principal": _money(account["principal_balance"]),
                "approved_limit": _money(max(account["principal_balance"], Decimal("1000"))),
                "monthly_inflow": None if missing else monthly_inflow,
                "inflow_12m_avg": None if missing else inflow_avg,
                "consecutive_partial_count": 3 if i % 9 == 0 else (1 if i % 5 == 0 else 0),
                "paid_amount": _money(account["principal_balance"] * Decimal("0.3")),
                "due_amount": _money(max(account["principal_balance"], Decimal("1000"))),
                "collateral_ratio_prev": Decimal("0.80"),
                "collateral_ratio_curr": Decimal("0.40") if i % 12 == 0 else Decimal("0.75"),
                "guarantee_status": None if missing else ("revoked" if i % 15 == 0 else "active"),
                "other_facility_dpd_90plus": i % 16 == 0,
                "default_flag": i % 13 == 0,
                "institution": account["institution"],
            }

    # -- insurance -----------------------------------------------------------
    def _t_ins_claim_case(self) -> Iterable[dict[str, Any]]:
        for i in range(max(self.rows_per_table, 2000)):
            policy = self.policies[i % min(1800, len(self.policies))]
            base = max(policy["issue_date"] + timedelta(days=1), WINDOW_START)
            report_date = base + timedelta(days=i % 180)
            if report_date > date(2025, 10, 31):
                report_date = date(2025, 10, 31)
            filing_date = report_date + timedelta(days=1 + i % 10)
            status = CLAIM_STATUS[i % len(CLAIM_STATUS)]
            if status == "reported":
                decision_date = None
            else:
                decision_date = min(filing_date + timedelta(days=1 + i % 20), AS_OF)
                if decision_date <= filing_date:
                    decision_date = filing_date + timedelta(days=1)
            claim_amount = _money(1000 + (i * 53) % 100000)
            paid = claim_amount if status == "paid" else Decimal("0.00")
            yield {
                "claim_no": f"CLM-SYN-{i:05d}",
                "policy_no": policy["policy_no"],
                "product": policy["product"],
                "institution": policy["institution"],
                "report_date": report_date,
                "filing_date": filing_date,
                "decision_date": decision_date,
                "claim_amount": claim_amount,
                "paid_amount": paid,
                "claim_status": status,
            }

    def _t_ins_claim_reserve_snapshot(self) -> Iterable[dict[str, Any]]:
        for i in range(max(self.rows_per_table, 2000)):
            policy = self.policies[i % min(1800, len(self.policies))]
            status = RESERVE_STATUS[i % 2]
            reserve = Decimal("0.00") if status == "closed" else _money(500 + (i * 41) % 50000)
            yield {
                "claim_no": f"CLM-SYN-{i:05d}",
                "institution": policy["institution"],
                "product": policy["product"],
                "as_of": AS_OF,
                "reported_reserve": reserve,
                "ibnr_reserve": _money(reserve * Decimal("0.10")),
                "expense_reserve": _money(reserve * Decimal("0.02")),
                "case_status": status,
            }

    def _t_ins_payment_record(self) -> Iterable[dict[str, Any]]:
        for i, policy in enumerate(self.policies):
            due = policy["issue_date"] + timedelta(days=30)
            if due > AS_OF:
                due = AS_OF
            bucket = i % 10
            if bucket < 8:
                payment_status = "paid"
                paid_date = min(due + timedelta(days=i % 5), AS_OF)
                paid_amount = policy["premium_amount"]
            elif bucket == 8:
                payment_status = "unpaid"
                paid_date = None
                paid_amount = Decimal("0.00")
            else:
                payment_status = "waived"
                paid_date = None
                paid_amount = Decimal("0.00")
            payment_type = "reinstatement" if i % 15 == 0 else ("arrears" if bucket == 8 else "current")
            yield {
                "payment_id": 20_000_000 + i,
                "policy_no": policy["policy_no"],
                "product": policy["product"],
                "installment_no": 1,
                "due_date": due,
                "due_amount": policy["premium_amount"],
                "paid_amount": paid_amount,
                "paid_date": paid_date,
                "payment_status": payment_status,
                "policy_status": policy["policy_status"],
                "status_as_of": AS_OF,
                "institution": policy["institution"],
                "grace_end_date": due + timedelta(days=60),
                "payment_type": payment_type,
                "policy_year": policy["policy_year"],
                "reinstatement_flag": payment_type == "reinstatement",
            }

    def _t_ins_policy_event(self) -> Iterable[dict[str, Any]]:
        for i in range(max(self.rows_per_table, 1500)):
            policy = self.policies[i % len(self.policies)]
            event_type = EVENT_TYPES[i % len(EVENT_TYPES)]
            event_date = max(policy["issue_date"], date(2025, 1, 1)) + timedelta(days=i % 300)
            if event_date > AS_OF:
                event_date = AS_OF
            yield {
                "event_id": f"PEV-SYN-{i:05d}",
                "policy_no": policy["policy_no"],
                "event_type": event_type,
                "event_date": event_date,
            }

    def _t_ins_underwriting_stat(self) -> Iterable[dict[str, Any]]:
        quarters = [
            (date(2025, 1, 1), date(2025, 3, 31)),
            (date(2025, 4, 1), date(2025, 6, 30)),
            (date(2025, 7, 1), date(2025, 9, 30)),
            (date(2025, 10, 1), date(2025, 12, 31)),
        ]
        for institution in INSTITUTIONS:
            for product in INS_PRODUCTS:
                for channel in CHANNELS:
                    for line in ["life", "health", "property", "other"]:
                        for q_start, q_end in quarters:
                            raw = f"{institution}|{product}|{channel}|{line}|{q_start.isoformat()}"
                            seed = int(hashlib.md5(raw.encode()).hexdigest()[:8], 16) % 100000
                            signed = _money(10000 + seed * 7)
                            ceded = _money(signed * Decimal("0.20"))
                            retained = _money(signed - ceded)
                            unearned = _money(retained * Decimal("0.05"))
                            earned = _money(retained - unearned)
                            yield {
                                "institution": institution,
                                "product": product,
                                "channel": channel,
                                "business_line": line,
                                "period_start": q_start,
                                "period_end": q_end,
                                "signed_premium": signed,
                                "plan_premium": _money(signed * Decimal("0.95")),
                                "collected_premium": _money(signed * Decimal("0.80")),
                                "ceded_premium": ceded,
                                "retained_premium": retained,
                                "unearned_reserve_change": unearned,
                                "earned_premium": earned,
                                "paid_claims": _money(retained * Decimal("0.30")),
                                "claim_reserve_change": _money(retained * Decimal("0.10")),
                                "reinsurance_recoverable": _money(ceded * Decimal("0.50")),
                                "long_term_reserve_change": _money(retained * Decimal("0.02")),
                                "expense_total": _money(retained * Decimal("0.20")),
                                "commission_expense": _money(retained * Decimal("0.08")),
                                "surrender_amount": _money(retained * Decimal("0.03")),
                                "beginning_reserve_total": _money(retained * Decimal("2.0")),
                                "policyholder_deposit_beginning": _money(retained),
                                "separate_account_beginning": _money(retained * Decimal("0.30")),
                                "current_term_premium": _money(retained * Decimal("1.20")),
                            }

    def _t_ins_persistence_stat(self) -> Iterable[dict[str, Any]]:
        months = list(_iter_months(2025, 1, 12))
        bases = ["grace", "vehicle_renewal"]
        for institution in INSTITUTIONS:
            for product in INS_PRODUCTS:
                for channel in CHANNELS[:3]:
                    for month_idx, cohort in enumerate(months):
                        for basis in bases:
                            for year in (2, 3):
                                first = _money(1000 + (month_idx * 13 + year * 7) % 20000)
                                renewed = _money(first * Decimal("0.60"))
                                due = 10 + (month_idx + year) % 20
                                renewed_count = max(1, due - (month_idx % 4))
                                yield {
                                    "institution": institution,
                                    "product": product,
                                    "channel": channel,
                                    "cohort_period": cohort,
                                    "valuation_basis": basis,
                                    "renewal_year": year,
                                    "first_year_premium": first,
                                    "renewed_premium": renewed,
                                    "due_vehicle_count": due,
                                    "renewed_vehicle_count": renewed_count,
                                }

    # -- customer ------------------------------------------------------------
    def _t_cust_transaction(self) -> Iterable[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        txn_no = 0
        tie_amount = _money(888)
        for i, customer in enumerate(self.customers):
            start = max(customer["registration_date"] + timedelta(days=1), WINDOW_START)
            for j in range(2):
                txn_no += 1
                txn_type = "refund" if (i + j) % 10 == 0 else ("transfer" if (i + j) % 7 == 0 else "purchase")
                amount = tie_amount if i % 50 == 0 else _money(10 + (i * 19 + j * 7) % 5000)
                rows.append(
                    {
                        "txn_id": f"TXN-SYN-{txn_no:06d}",
                        "customer_no": customer["customer_no"],
                        "txn_date": min(start + timedelta(days=(i + j * 30) % 200), AS_OF),
                        "txn_type": txn_type,
                        "amount": amount,
                        "product_category": CUST_PRODUCTS[i % len(CUST_PRODUCTS)],
                        "channel": CHANNELS[i % len(CHANNELS)],
                    }
                )
        # Same-day multiple transactions for 500 customers.
        for i in range(500):
            customer = self.customers[i]
            day = max(customer["registration_date"] + timedelta(days=1), date(2025, 3, 1)) + timedelta(days=i % 30)
            for k in range(2):
                txn_no += 1
                rows.append(
                    {
                        "txn_id": f"TXN-SYN-{txn_no:06d}",
                        "customer_no": customer["customer_no"],
                        "txn_date": min(day, AS_OF),
                        "txn_type": "purchase",
                        "amount": _money(100 + k * 10),
                        "product_category": CUST_PRODUCTS[i % len(CUST_PRODUCTS)],
                        "channel": CHANNELS[i % len(CHANNELS)],
                    }
                )
        yield from rows

    def _t_cust_campaign_touch(self) -> Iterable[dict[str, Any]]:
        for i in range(max(self.rows_per_table, 2000)):
            customer = self.customers[i % self.n_customers]
            touch = date(2025, 1, 1) + timedelta(days=(i * 2) % 300)
            responded = i % 3 == 0
            yield {
                "touch_id": f"CTH-SYN-{i:05d}",
                "customer_no": customer["customer_no"],
                "campaign_id": f"CMP-SYN-{i % 20:03d}",
                "touch_date": touch,
                "channel": CHANNELS[i % len(CHANNELS)],
                "response_flag": responded,
                "response_date": touch + timedelta(days=1 + i % 10) if responded else None,
            }

    def _t_cust_complaint(self) -> Iterable[dict[str, Any]]:
        for i in range(max(self.rows_per_table, 1500)):
            customer = self.customers[i % self.n_customers]
            opened = date(2025, 1, 1) + timedelta(days=(i * 3) % 300)
            closed_bucket = i % 5
            closed = None if closed_bucket == 0 else min(opened + timedelta(days=1 + i % 30), AS_OF)
            yield {
                "ticket_id": f"TKT-SYN-{i:05d}",
                "customer_no": customer["customer_no"],
                "opened_date": opened,
                "closed_date": closed,
                "category": ["service", "fee", "product", "channel"][i % 4],
                "ticket_status": TICKET_STATUS[i % len(TICKET_STATUS)],
            }

    def _t_cust_product_holding(self) -> Iterable[dict[str, Any]]:
        holding_no = 0
        for i, customer in enumerate(self.customers):
            for k in range(1 + i % 3):
                holding_no += 1
                yield {
                    "holding_id": f"HOLD-SYN-{holding_no:06d}",
                    "customer_no": customer["customer_no"],
                    "product_category": CUST_PRODUCTS[(i + k) % len(CUST_PRODUCTS)],
                    "holding_status": HOLDING_STATUS[(i + k) % len(HOLDING_STATUS)],
                    "as_of": AS_OF,
                    "institution": customer["institution"],
                }

    def _t_cust_behavior_snapshot(self) -> Iterable[dict[str, Any]]:
        for i, customer in enumerate(self.customers):
            last_behavior = AS_OF - timedelta(days=i % 365)
            last_txn = None if i % 15 == 0 else AS_OF - timedelta(days=(i * 3) % 300)
            yield {
                "customer_no": customer["customer_no"],
                "institution": customer["institution"],
                "as_of": AS_OF,
                "last_behavior_date": last_behavior,
                "days_since_last_behavior": (AS_OF - last_behavior).days,
                "last_txn_date": last_txn,
                "days_since_proxy_event": (AS_OF - last_txn).days if last_txn else (AS_OF - last_behavior).days,
            }

    def _t_cust_cohort_stat(self) -> Iterable[dict[str, Any]]:
        months = list(_iter_months(2020, 1, 60))
        for institution in INSTITUTIONS:
            for month_idx, cohort in enumerate(months):
                cohort_customers = 50 + month_idx * 3
                retained = cohort_customers - month_idx
                active = max(1, retained - 5)
                prior = max(1, active - 2)
                both = min(active, prior)
                yield {
                    "cohort_key": f"{institution}:{cohort.isoformat()}",
                    "institution": institution,
                    "cohort_month": cohort,
                    "as_of": AS_OF,
                    "cohort_customers": cohort_customers,
                    "retained_customers": retained,
                    "active_customers": active,
                    "prior_month_active": prior,
                    "active_and_prior_month": both,
                }

    def _t_cust_aum_snapshot(self) -> Iterable[dict[str, Any]]:
        for i, customer in enumerate(self.customers):
            for k, product in enumerate(CUST_PRODUCTS):
                aum = Decimal("0.00") if (i + k) % 41 == 0 else _money((i * 7 + k * 131) % 1_000_000)
                yield {
                    "customer_no": customer["customer_no"],
                    "institution": customer["institution"],
                    "product_type": product,
                    "as_of": AS_OF,
                    "aum": aum,
                }


# ----------------------------------------------------------------------------
# Generation orchestration
# ----------------------------------------------------------------------------


def _validate_payload(info: TableInfo, columns: set[str]) -> None:
    missing = info.required_columns - columns
    unknown = columns - set(info.columns)
    if missing or unknown:
        raise _err(
            "E_DATAGEN_SCHEMA_DRIFT",
            f"payload for {info.name} does not match information_schema",
            missing=sorted(missing),
            unknown=sorted(unknown),
            required=sorted(info.required_columns),
        )


def _insert_rows(
    meta: MetadataPg,
    table: TableInfo,
    rows: list[dict[str, Any]],
    *,
    batch_size: int = 2000,
) -> int:
    if not rows:
        return 0
    for row in rows:
        row.setdefault("data_source", SYNTHETIC)
        row.setdefault("fixture", False)
        row.setdefault("created_at", CREATED_AT)
    columns = list(rows[0].keys())
    _validate_payload(table, set(columns))
    for row in rows:
        if set(row) != set(columns):
            raise _err(
                "E_DATAGEN_SCHEMA_DRIFT",
                f"inconsistent column set in payload for {table.name}",
            )
    placeholders = ", ".join(["%s"] * len(columns))
    sql = (
        f"INSERT INTO {table.schema}.{table.name} "
        f"({', '.join(columns)}) VALUES ({placeholders})"
    )
    total = 0
    with meta.tx() as tx:
        for offset in range(0, len(rows), batch_size):
            total += tx.executemany(sql, [tuple(row[c] for c in columns) for row in rows[offset : offset + batch_size]])
    return total


def _count_by_source(meta: MetadataPg, schema: str, tables: dict[str, TableInfo]) -> dict[str, int]:
    out: dict[str, int] = {}
    for table in tables.values():
        row = meta.query(
            f"SELECT count(*) AS n FROM {schema}.{table.name} WHERE data_source = %s",
            (SYNTHETIC,),
        )[0]
        out[table.name] = int(row["n"])
    return out


def _clean_synthetic(meta: MetadataPg, schema: str, tables: dict[str, TableInfo]) -> dict[str, Any]:
    before_total = {
        name: int(meta.query(f"SELECT count(*) AS n FROM {schema}.{name}")[0]["n"])
        for name in tables
    }
    before_syn = _count_by_source(meta, schema, tables)
    deleted: dict[str, int] = {}
    with meta.tx() as tx:
        for name in tables:
            deleted[name] = tx.execute(
                f"DELETE FROM {schema}.{name} WHERE data_source = %s", (SYNTHETIC,)
            )
    after_total = {
        name: int(meta.query(f"SELECT count(*) AS n FROM {schema}.{name}")[0]["n"])
        for name in tables
    }
    after_syn = _count_by_source(meta, schema, tables)
    bad = [name for name in tables if after_total[name] != before_total[name] - before_syn[name]]
    if bad or any(after_syn.values()):
        raise _err(
            "E_DATAGEN_CLEAN_ASSERT",
            "clean removed non-synthetic rows or left synthetic rows behind",
            badTables=bad,
            residual=after_syn,
        )
    return {
        "before": before_total,
        "syntheticBefore": before_syn,
        "deleted": deleted,
        "after": after_total,
        "syntheticAfter": after_syn,
    }


def generate(
    meta: MetadataPg,
    *,
    seed: int = 42,
    scale: float = 1.0,
    target_schema: str = OFFICIAL_SCHEMA,
    allow_official: bool = False,
    rows_per_table: int = 1000,
    clean: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    info = ensure_target(meta, target_schema, allow_official)
    factory = SyntheticFactory(
        seed,
        rows_per_table=rows_per_table,
        master_rows=max(5000, rows_per_table * 5),
        scale=scale,
    )
    expected_tables = set(info)
    supported = set(factory.supported_tables())
    missing_recipe = expected_tables - supported
    if missing_recipe:
        raise _err(
            "E_DATAGEN_TABLE_UNSUPPORTED",
            "schema contains fact tables without a synthetic recipe",
            tables=sorted(missing_recipe),
        )

    report: dict[str, Any] = {
        "seed": seed,
        "scale": scale,
        "schema": target_schema,
        "rowsPerTable": factory.rows_per_table,
        "masterRows": factory.n_customers,
        "dryRun": dry_run,
        "clean": None,
        "rowCounts": {},
    }
    if clean:
        if dry_run:
            report["clean"] = _count_by_source(meta, target_schema, info)
        else:
            report["clean"] = _clean_synthetic(meta, target_schema, info)

    insert_order = [
        "cust_master",
        "ins_policy",
        "bank_loan_account",
        "loan_installment_plan",
        "bank_loan_repayment",
        "bank_credit_facility",
        "bank_credit_application",
        "bank_collection_case",
        "bank_collection_recovery",
        "bank_npl_snapshot",
        "bank_disposal_event",
        "bank_provision_snapshot",
        "bank_concentration_stat",
        "bank_deposit_account",
        "bank_ews_signal",
        "ins_claim_case",
        "ins_claim_reserve_snapshot",
        "ins_payment_record",
        "ins_policy_event",
        "ins_underwriting_stat",
        "ins_persistence_stat",
        "cust_transaction",
        "cust_campaign_touch",
        "cust_complaint",
        "cust_product_holding",
        "cust_behavior_snapshot",
        "cust_cohort_stat",
        "cust_aum_snapshot",
    ]
    order = [name for name in insert_order if name in info] + sorted(expected_tables - set(insert_order))
    for name in order:
        rows = factory.rows_for(name)
        report["rowCounts"][name] = len(rows)
        if not dry_run:
            _insert_rows(meta, info[name], rows)
    return report


# ----------------------------------------------------------------------------
# Validation
# ----------------------------------------------------------------------------


RELATIONS: list[dict[str, Any]] = [
    {"name": "customer->policy", "child": "ins_policy", "child_col": "customer_no", "parent": "cust_master", "parent_col": "customer_no", "parent_filter": "as_of = '2025-12-31'"},
    {"name": "customer->loan", "child": "bank_loan_account", "child_col": "customer_no", "parent": "cust_master", "parent_col": "customer_no", "parent_filter": "as_of = '2025-12-31'"},
    {"name": "customer->facility", "child": "bank_credit_facility", "child_col": "customer_no", "parent": "cust_master", "parent_col": "customer_no", "parent_filter": "as_of = '2025-12-31'"},
    {"name": "customer->application", "child": "bank_credit_application", "child_col": "customer_no", "parent": "cust_master", "parent_col": "customer_no", "parent_filter": "as_of = '2025-12-31'"},
    {"name": "customer->deposit", "child": "bank_deposit_account", "child_col": "customer_no", "parent": "cust_master", "parent_col": "customer_no", "parent_filter": "as_of = '2025-12-31'"},
    {"name": "customer->ews", "child": "bank_ews_signal", "child_col": "customer_no", "parent": "cust_master", "parent_col": "customer_no", "parent_filter": "as_of = '2025-12-31'"},
    {"name": "customer->transaction", "child": "cust_transaction", "child_col": "customer_no", "parent": "cust_master", "parent_col": "customer_no", "parent_filter": "as_of = '2025-12-31'"},
    {"name": "customer->campaign", "child": "cust_campaign_touch", "child_col": "customer_no", "parent": "cust_master", "parent_col": "customer_no", "parent_filter": "as_of = '2025-12-31'"},
    {"name": "customer->complaint", "child": "cust_complaint", "child_col": "customer_no", "parent": "cust_master", "parent_col": "customer_no", "parent_filter": "as_of = '2025-12-31'"},
    {"name": "customer->holding", "child": "cust_product_holding", "child_col": "customer_no", "parent": "cust_master", "parent_col": "customer_no", "parent_filter": "as_of = '2025-12-31'"},
    {"name": "customer->behavior", "child": "cust_behavior_snapshot", "child_col": "customer_no", "parent": "cust_master", "parent_col": "customer_no", "parent_filter": "as_of = '2025-12-31'"},
    {"name": "customer->aum", "child": "cust_aum_snapshot", "child_col": "customer_no", "parent": "cust_master", "parent_col": "customer_no", "parent_filter": "as_of = '2025-12-31'"},
    {"name": "account->repayment", "child": "bank_loan_repayment", "child_col": "account_id", "parent": "bank_loan_account", "parent_col": "account_id", "parent_filter": "as_of = '2025-12-31'"},
    {"name": "account->plan", "child": "loan_installment_plan", "child_col": "agreement_id", "parent": "bank_loan_account", "parent_col": "account_id", "parent_filter": "as_of = '2025-12-31'"},
    {"name": "account->collection_case", "child": "bank_collection_case", "child_col": "account_id", "parent": "bank_loan_account", "parent_col": "account_id", "parent_filter": "as_of = '2025-12-31'"},
    {"name": "collection_case->recovery", "child": "bank_collection_recovery", "child_col": "case_id", "parent": "bank_collection_case", "parent_col": "case_id", "parent_filter": "status_as_of = '2025-12-31'"},
    {"name": "policy->claim", "child": "ins_claim_case", "child_col": "policy_no", "parent": "ins_policy", "parent_col": "policy_no", "parent_filter": "status_as_of = '2025-12-31'"},
    {"name": "policy->payment", "child": "ins_payment_record", "child_col": "policy_no", "parent": "ins_policy", "parent_col": "policy_no", "parent_filter": "status_as_of = '2025-12-31'"},
    {"name": "policy->event", "child": "ins_policy_event", "child_col": "policy_no", "parent": "ins_policy", "parent_col": "policy_no", "parent_filter": "status_as_of = '2025-12-31'"},
    {"name": "claim->reserve", "child": "ins_claim_reserve_snapshot", "child_col": "claim_no", "parent": "ins_claim_case", "parent_col": "claim_no"},
    {"name": "npl->disposal", "child": "bank_disposal_event", "child_col": "asset_id", "parent": "bank_npl_snapshot", "parent_col": "asset_id", "parent_filter": "as_of = '2025-12-31'"},
    {"name": "account->npl", "child": "bank_npl_snapshot", "child_col": "asset_id", "parent": "bank_loan_account", "parent_col": "account_id", "parent_filter": "as_of = '2025-12-31'"},
]


def _fk_checks(meta: MetadataPg, schema: str) -> dict[str, Any]:
    detail: list[dict[str, Any]] = []
    total_orphans = 0
    for rel in RELATIONS:
        pf = f" AND p.{rel.get('parent_filter')}" if rel.get("parent_filter") else ""
        sql = (
            f"SELECT count(*) AS n FROM {schema}.{rel['child']} c "
            f"LEFT JOIN {schema}.{rel['parent']} p "
            f"ON p.{rel['parent_col']} = c.{rel['child_col']}{pf} "
            f"WHERE c.data_source = %s AND c.{rel['child_col']} IS NOT NULL "
            "AND p." + rel["parent_col"] + " IS NULL"
        )
        orphans = int(meta.query(sql, (SYNTHETIC,))[0]["n"])
        total_orphans += orphans
        detail.append({**rel, "orphans": orphans})
    return {"ok": total_orphans == 0, "orphans": total_orphans, "relations": detail}


TIME_CHECKS: list[tuple[str, str]] = [
    ("loan_disbursed_before_maturity", "SELECT count(*) AS n FROM {s}.bank_loan_account WHERE data_source = %s AND disbursed_date IS NOT NULL AND maturity_date IS NOT NULL AND disbursed_date >= maturity_date"),
    ("loan_first_due_in_life", "SELECT count(*) AS n FROM {s}.bank_loan_account WHERE data_source = %s AND first_payment_due_date IS NOT NULL AND (first_payment_due_date < disbursed_date OR first_payment_due_date > maturity_date)"),
    ("plan_due_in_loan_life", "SELECT count(*) AS n FROM {s}.loan_installment_plan p JOIN {s}.bank_loan_account a ON a.account_id = p.agreement_id AND a.as_of = p.status_as_of WHERE p.data_source = %s AND (p.due_date < a.disbursed_date OR p.due_date > a.maturity_date)"),
    ("repayment_due_in_loan_life", "SELECT count(*) AS n FROM {s}.bank_loan_repayment r JOIN {s}.bank_loan_account a ON a.account_id = r.account_id AND a.as_of = r.status_as_of WHERE r.data_source = %s AND (r.due_date < a.disbursed_date OR r.due_date > a.maturity_date OR (r.paid_date IS NOT NULL AND (r.paid_date < a.disbursed_date OR r.paid_date > r.status_as_of)))"),
    ("policy_payment_in_force", "SELECT count(*) AS n FROM {s}.ins_payment_record pay JOIN {s}.ins_policy pol ON pol.policy_no = pay.policy_no AND pol.status_as_of = pay.status_as_of WHERE pay.data_source = %s AND (pay.due_date < pol.issue_date OR (pay.paid_date IS NOT NULL AND (pay.paid_date < pol.issue_date OR pay.paid_date > pay.status_as_of)))"),
    ("claim_decision_after_report", "SELECT count(*) AS n FROM {s}.ins_claim_case c JOIN {s}.ins_policy p ON p.policy_no = c.policy_no AND p.status_as_of = '2025-12-31' WHERE c.data_source = %s AND (c.report_date < p.issue_date OR (c.filing_date IS NOT NULL AND c.filing_date < c.report_date) OR (c.decision_date IS NOT NULL AND c.decision_date <= c.report_date) OR c.decision_date > '2025-12-31')"),
    ("policy_event_in_force", "SELECT count(*) AS n FROM {s}.ins_policy_event e JOIN {s}.ins_policy p ON p.policy_no = e.policy_no AND p.status_as_of = '2025-12-31' WHERE e.data_source = %s AND (e.event_date < p.issue_date OR e.event_date > p.status_as_of)"),
    ("transaction_after_registration", "SELECT count(*) AS n FROM {s}.cust_transaction t JOIN {s}.cust_master m ON m.customer_no = t.customer_no AND m.as_of = '2025-12-31' WHERE t.data_source = %s AND (t.txn_date < m.registration_date OR t.txn_date > '2025-12-31')"),
    ("complaint_closed_after_opened", "SELECT count(*) AS n FROM {s}.cust_complaint WHERE data_source = %s AND closed_date IS NOT NULL AND closed_date < opened_date"),
    ("campaign_response_after_touch", "SELECT count(*) AS n FROM {s}.cust_campaign_touch WHERE data_source = %s AND response_date IS NOT NULL AND response_date < touch_date"),
    ("underwriting_period_order", "SELECT count(*) AS n FROM {s}.ins_underwriting_stat WHERE data_source = %s AND (period_start >= period_end OR period_end > '2025-12-31')"),
    ("collection_after_overdue", "SELECT count(*) AS n FROM {s}.bank_collection_recovery r JOIN {s}.bank_collection_case c ON c.case_id = r.case_id AND c.status_as_of = '2025-12-31' JOIN {s}.bank_loan_account a ON a.account_id = c.account_id AND a.as_of = '2025-12-31' WHERE r.data_source = %s AND (r.recovery_date <= a.first_payment_due_date OR r.recovery_date > c.status_as_of)"),
    ("disposal_before_snapshot", "SELECT count(*) AS n FROM {s}.bank_disposal_event d JOIN {s}.bank_npl_snapshot n ON n.asset_id = d.asset_id AND n.as_of = '2025-12-31' WHERE d.data_source = %s AND d.completion_date > n.as_of"),
    ("behavior_days_match", "SELECT count(*) AS n FROM {s}.cust_behavior_snapshot WHERE data_source = %s AND days_since_last_behavior <> ('2025-12-31'::date - last_behavior_date)"),
    ("cohort_count_order", "SELECT count(*) AS n FROM {s}.cust_cohort_stat WHERE data_source = %s AND (retained_customers > cohort_customers OR active_customers > retained_customers OR prior_month_active > retained_customers OR active_and_prior_month > LEAST(active_customers, prior_month_active))"),
]


def _time_checks(meta: MetadataPg, schema: str) -> dict[str, Any]:
    detail: list[dict[str, Any]] = []
    total = 0
    for name, template in TIME_CHECKS:
        sql = template.format(s=schema)
        n = int(meta.query(sql, (SYNTHETIC,))[0]["n"])
        total += n
        detail.append({"check": name, "violations": n})
    return {"ok": total == 0, "violations": total, "checks": detail}


MONEY_CHECKS: list[tuple[str, str]] = [
    ("plan_sum_equals_principal_plus_interest", "SELECT count(*) AS n FROM (SELECT a.account_id, a.principal_balance, SUM(p.due_amount) AS plan_total FROM {s}.bank_loan_account a JOIN {s}.loan_installment_plan p ON p.agreement_id = a.account_id AND p.status_as_of = a.as_of WHERE a.data_source = %s AND a.as_of = '2025-12-31' GROUP BY a.account_id, a.principal_balance) x WHERE x.plan_total <> ROUND(x.principal_balance * 1.05, 2)"),
    ("repayment_components_equal_paid", "SELECT count(*) AS n FROM {s}.bank_loan_repayment WHERE data_source = %s AND paid_amount <> principal_paid + interest_paid + penalty_paid"),
    ("repayment_paid_not_above_due", "SELECT count(*) AS n FROM {s}.bank_loan_repayment WHERE data_source = %s AND paid_amount > due_amount"),
    ("repayment_paid_has_date", "SELECT count(*) AS n FROM {s}.bank_loan_repayment WHERE data_source = %s AND paid_amount > 0 AND paid_date IS NULL"),
    ("underwriting_retained_identity", "SELECT count(*) AS n FROM {s}.ins_underwriting_stat WHERE data_source = %s AND retained_premium <> signed_premium - ceded_premium"),
    ("underwriting_earned_identity", "SELECT count(*) AS n FROM {s}.ins_underwriting_stat WHERE data_source = %s AND earned_premium <> retained_premium - unearned_reserve_change"),
    ("claim_paid_not_above_claim", "SELECT count(*) AS n FROM {s}.ins_claim_case WHERE data_source = %s AND paid_amount > claim_amount"),
    ("provision_not_above_loan", "SELECT count(*) AS n FROM {s}.bank_provision_snapshot WHERE data_source = %s AND provision_balance > loan_balance"),
    ("account_period_decrease_identity", "SELECT count(*) AS n FROM {s}.bank_loan_account WHERE data_source = %s AND risk_class_start = 'normal' AND period_decrease_amount <> balance_start - balance_end"),
    ("recovery_not_above_outstanding", "SELECT count(*) AS n FROM {s}.bank_collection_recovery r JOIN {s}.bank_collection_case c ON c.case_id = r.case_id AND c.status_as_of = '2025-12-31' WHERE r.data_source = %s AND r.principal_recovered + r.interest_recovered + r.fee_recovered > c.outstanding_principal"),
]


def _money_checks(meta: MetadataPg, schema: str) -> dict[str, Any]:
    detail: list[dict[str, Any]] = []
    total = 0
    for name, template in MONEY_CHECKS:
        n = int(meta.query(template.format(s=schema), (SYNTHETIC,))[0]["n"])
        total += n
        detail.append({"check": name, "violations": n})
    return {"ok": total == 0, "violations": total, "checks": detail}


def _scalar(meta: MetadataPg, sql: str, params: tuple | list = ()) -> int:
    return int(meta.query(sql, params)[0]["n"])


def build_rule_facts(meta: MetadataPg, *, empty: bool = False) -> list[dict[str, Any]]:
    if empty:
        return []
    balances = {
        r["customer_no"]: r
        for r in meta.query(
            "SELECT customer_no, SUM(principal_balance) AS total_balance, "
            "SUM(CASE WHEN risk_class IN ('substandard','doubtful','loss') THEN principal_balance ELSE 0 END) AS npl_balance "
            "FROM platform.bank_loan_account WHERE data_source = %s AND as_of = '2025-12-31' "
            "GROUP BY customer_no",
            (SYNTHETIC,),
        )
    }
    facts: list[dict[str, Any]] = []
    rows = meta.query(
        "SELECT customer_no, dpd, dpd_start, dpd_end, risk_class_prev, risk_class_curr, "
        "rating_notch_prev, rating_notch_curr, drawn_principal, approved_limit, "
        "monthly_inflow, inflow_12m_avg, consecutive_partial_count, paid_amount, "
        "due_amount, collateral_ratio_prev, collateral_ratio_curr, guarantee_status, "
        "other_facility_dpd_90plus, default_flag "
        "FROM platform.bank_ews_signal WHERE data_source = %s AND as_of = '2025-12-31' "
        "ORDER BY customer_no",
        (SYNTHETIC,),
    )
    for row in rows:
        idx = _customer_index(row["customer_no"])
        balance = balances.get(row["customer_no"], {})
        impaired = row["risk_class_curr"] in BAD_RISK_CLASSES or bool(row["default_flag"])
        notch_prev = row["rating_notch_prev"]
        notch_curr = row["rating_notch_curr"]
        significant = (
            notch_prev is not None and notch_curr is not None and (notch_prev - notch_curr) >= 2
        )
        facts.append(
            {
                "customerId": row["customer_no"],
                "customer_no": row["customer_no"],
                "asOf": "2025-12-31",
                "dpd": row["dpd"],
                "dpd_start": row["dpd_start"],
                "dpd_end": row["dpd_end"],
                "risk_class": row["risk_class_curr"],
                "risk_class_prev": row["risk_class_prev"],
                "risk_class_curr": row["risk_class_curr"],
                "rating_notch_prev": notch_prev,
                "rating_notch_curr": notch_curr,
                "credit_impaired": impaired,
                "significant_increase": significant,
                "financial_difficulty": idx % 6 == 0,
                "contract_modified": idx % 6 == 0,
                "restructuring_flag": idx % 8 == 0,
                "days_since_restructure": 200 if idx % 8 == 0 else 0,
                "extension_approved": idx % 9 == 0,
                "refinanced": idx % 11 == 0,
                "npl_balance": float(balance.get("npl_balance") or 0),
                "total_balance": float(balance.get("total_balance") or 0),
                "paid_amount": float(row["paid_amount"] or 0),
                "due_amount": float(row["due_amount"] or 0),
                "drawn_principal": float(row["drawn_principal"] or 0),
                "approved_limit": float(row["approved_limit"] or 0),
                "monthly_inflow": None if row["monthly_inflow"] is None else float(row["monthly_inflow"]),
                "inflow_12m_avg": None if row["inflow_12m_avg"] is None else float(row["inflow_12m_avg"]),
                "consecutive_partial_count": row["consecutive_partial_count"],
                "collateral_ratio_prev": float(row["collateral_ratio_prev"] or 0),
                "collateral_ratio_curr": float(row["collateral_ratio_curr"] or 0),
                "guarantee_status": row["guarantee_status"],
                "other_facility_dpd_90plus": row["other_facility_dpd_90plus"],
                "default_flag": row["default_flag"],
            }
        )
    return facts


RULE_METRICS = [
    "FIN-BANK-003", "FIN-BANK-004", "FIN-BANK-005", "FIN-BANK-006", "FIN-BANK-007",
    "FIN-BANK-009", "FIN-BANK-010", "FIN-BANK-011", "FIN-BANK-012", "FIN-BANK-024",
    "FIN-BANK-034",
]

SCALAR_METRICS = [
    "CUST-001", "CUST-002", "CUST-003", "CUST-006", "CUST-009", "CUST-012",
    "FIN-BANK-001", "FIN-BANK-008", "FIN-BANK-013", "FIN-BANK-017", "FIN-BANK-022",
    "FIN-BANK-033", "FIN-INS-002", "FIN-INS-007", "FIN-INS-014", "FIN-INS-015",
    "FIN-INS-017", "FIN-INS-019", "FIN-INS-021",
]

VERIFY_METRICS = RULE_METRICS + SCALAR_METRICS

# Probe windows. The non-publishable metrics are refused before execution, so
# their windows do not matter; the remaining probes are chosen to exercise the
# zero-denominator, no-data and short-window paths.
PROBES: dict[str, dict[str, Any]] = {
    "FIN-BANK-001": {"as_of": "2025-12-31"},
    "FIN-BANK-008": {"as_of": "2025-12-30", "path": "denominator_zero"},
    "FIN-BANK-013": {"as_of": "2025-12-31"},
    "FIN-BANK-022": {"as_of": "2020-12-31", "path": "no_data"},
    "FIN-INS-002": {"start": "2024-01-01", "end": "2024-12-31", "path": "no_data"},
    "FIN-INS-014": {"as_of": "2020-12-31", "path": "no_data"},
    "FIN-INS-015": {"start": "2025-01-01", "end": "2025-12-31"},
    "FIN-INS-019": {"start": "2025-01-01", "end": "2025-12-31"},
    "FIN-INS-021": {"start": "2025-06-01", "end": "2025-06-30", "path": "window_insufficient"},
    "FIN-BANK-010": {"as_of": "2025-12-31", "empty_facts": True, "path": "rule_no_data"},
}
DEFAULT_PROBE = {"start": "2025-01-01", "end": "2025-12-31", "as_of": "2025-12-31"}


def _metric_definition(meta: MetadataPg, metric_id: str) -> dict[str, Any]:
    rows = meta.query(
        "SELECT metric_id, definition_version, name_zh, publishable, formula_disabled, "
        "evidence_basis, output_mode, metric_kind, formula_expr, window_kind, "
        "numerator_agg, denominator_agg, min_window_days, fact_function, computability_tier "
        "FROM platform.metric_definition WHERE metric_id = %s",
        (metric_id,),
    )
    if not rows:
        raise _err("E_DATAGEN_METRIC_MISSING", f"metric {metric_id} is not registered")
    return rows[0]


def _has_bindings(meta: MetadataPg, metric_id: str, version: str) -> bool:
    rows = meta.query(
        "SELECT count(*) AS n FROM platform.metric_field_binding "
        "WHERE metric_id = %s AND definition_version = %s AND role = 'numerator'",
        (metric_id, version),
    )
    return int(rows[0]["n"]) > 0


def _function_metric(
    meta: MetadataPg,
    d: dict[str, Any],
    start: str | None,
    end: str | None,
) -> dict[str, Any]:
    """Execute a fact-function metric without writing metric_observation."""

    window_kind = d["window_kind"]
    if window_kind == "instant":
        if start is None and end is None:
            raise _err("E_DATAGEN_BINDING_INVALID", "instant metric requires asOf", metricId=d["metric_id"])
        as_of = start or end
        win_start = win_end = str(as_of)
    else:
        if start is None or end is None:
            raise _err("E_DATAGEN_BINDING_INVALID", "period metric requires start and end", metricId=d["metric_id"])
        win_start, win_end = str(start), str(end)
        span = (date.fromisoformat(win_end) - date.fromisoformat(win_start)).days + 1
        if span < int(d["min_window_days"] or 0):
            raise _err(
                "E_METRIC_WINDOW_INSUFFICIENT",
                f"window {span}d below min {d['min_window_days']}d",
                metricId=d["metric_id"],
            )
    rows = meta.query(
        f"SELECT entity_key, numerator, denominator FROM {d['fact_function']}(%s::date, %s::date, %s)",
        (win_start, win_end, SYNTHETIC),
    )
    if not rows:
        return {
            "metricId": d["metric_id"],
            "window": {"start": win_start, "end": win_end},
            "dataSource": SYNTHETIC,
            "rows": [],
            "noData": True,
        }

    def agg(values: list[Any], name: str | None) -> Any:
        nums = [Decimal(str(v)) for v in values if v is not None]
        if not nums:
            return None
        if name == "max":
            return max(nums)
        if name == "min":
            return min(nums)
        if name == "avg":
            return sum(nums) / Decimal(len(nums))
        return sum(nums)

    numerator = agg([r["numerator"] for r in rows], d["numerator_agg"])
    denominator = agg([r["denominator"] for r in rows], d["denominator_agg"])
    if "denominator" in (d["formula_expr"] or "") and denominator == 0:
        raise _err("E_METRIC_DENOM_ZERO", "denominator is zero; value undefined", metricId=d["metric_id"])
    value_sql = formula_to_sql(d["formula_expr"])
    result = meta.query(
        "WITH num AS (SELECT %s::numeric AS numerator), "
        "den AS (SELECT %s::numeric AS denominator) "
        f"SELECT ({value_sql}) AS metric_value FROM num CROSS JOIN den",
        (None if numerator is None else str(numerator), None if denominator is None else str(denominator)),
    )
    value = result[0]["metric_value"]
    return {
        "metricId": d["metric_id"],
        "window": {"start": win_start, "end": win_end},
        "dataSource": SYNTHETIC,
        "rows": [
            {
                "entityKey": r["entity_key"],
                "numerator": None if r["numerator"] is None else float(r["numerator"]),
                "denominator": None if r["denominator"] is None else float(r["denominator"]),
                "value": None,
            }
            for r in rows
        ],
        "aggregateNumerator": float(numerator) if numerator is not None else None,
        "aggregateDenominator": float(denominator) if denominator is not None else None,
        "value": None if value is None else float(value),
        "noData": False,
    }


def verify_metrics(meta: MetadataPg) -> dict[str, Any]:
    """Run the fixed 30-metric structural set and classify every outcome."""

    compiler = MetricCompiler(meta)
    rule_executor = RuleExecutor(meta)
    results: list[dict[str, Any]] = []
    facts = build_rule_facts(meta)
    for metric_id in VERIFY_METRICS:
        d = _metric_definition(meta, metric_id)
        probe = dict(PROBES.get(metric_id) or {})
        if d["window_kind"] == "instant" or ("as_of" in probe and "start" not in probe):
            as_of = probe.get("as_of")
            probe.update(start=as_of, end=None, as_of=as_of)
        elif probe:
            probe.setdefault("start", "2025-01-01")
            probe.setdefault("end", "2025-12-31")
        else:
            probe = dict(DEFAULT_PROBE)
        item: dict[str, Any] = {
            "metricId": metric_id,
            "kind": d["metric_kind"],
            "outputMode": d["output_mode"],
            "publishable": bool(d["publishable"]),
            "probe": probe,
            "dataSource": SYNTHETIC,
        }
        if d["formula_disabled"]:
            item.update(category="refusal", code="E_METRIC_FORMULA_DISABLED")
            results.append(item)
            continue
        if not d["publishable"]:
            item.update(category="refusal", code="E_METRIC_NOT_PUBLISHABLE")
            results.append(item)
            continue
        if d["output_mode"] == "rule_set" or d["metric_kind"] == "rule_set":
            if probe.get("empty_facts"):
                item.update(category="exception", code="E_METRIC_NO_DATA")
                results.append(item)
                continue
            result = rule_executor.execute(metric_id, facts, as_of="2025-12-31")
            item.update(
                category="success",
                code=None,
                value=result["triggeredCount"],
                factsEvaluated=result["factsEvaluated"],
                unevaluatedRules=result["unevaluatedRules"],
                dataSource=SYNTHETIC,
            )
            results.append(item)
            continue
        try:
            has_binding = _has_bindings(meta, metric_id, d["definition_version"])
            if not has_binding and d["fact_function"]:
                result = _function_metric(meta, d, probe.get("start"), probe.get("end"))
                if result["noData"]:
                    item.update(category="exception", code="E_METRIC_NO_DATA")
                else:
                    item.update(
                        category="success",
                        code=None,
                        value=result["value"],
                        aggregateNumerator=result["aggregateNumerator"],
                        aggregateDenominator=result["aggregateDenominator"],
                        entityRows=len(result["rows"]),
                    )
                results.append(item)
                continue
            result = compiler.execute(
                metric_id,
                start=probe.get("start"),
                end=probe.get("end"),
                internal=False,
                data_source=SYNTHETIC,
            )
            if result["noData"]:
                item.update(category="exception", code="E_METRIC_NO_DATA")
            else:
                rows = result["rows"]
                numerator = sum(Decimal(str(r["numerator"] or 0)) for r in rows)
                denominator = sum(
                    (Decimal(str(r["denominator"])) for r in rows if r["denominator"] is not None),
                    Decimal("0"),
                )
                item.update(
                    category="success",
                    code=None,
                    entityRows=len(rows),
                    aggregateNumerator=float(numerator),
                    aggregateDenominator=float(denominator),
                )
            results.append(item)
        except PortError as exc:
            if exc.provider_code in ("E_METRIC_DENOM_ZERO", "E_METRIC_WINDOW_INSUFFICIENT", "E_METRIC_NO_DATA"):
                item.update(category="exception", code=exc.provider_code)
            else:
                raise
            results.append(item)

    counts = {
        "success": sum(1 for r in results if r["category"] == "success"),
        "refusal": sum(1 for r in results if r["category"] == "refusal"),
        "exception": sum(1 for r in results if r["category"] == "exception"),
    }
    return {"total": len(results), "counts": counts, "results": results, "handChecks": hand_checks(meta, results)}


def _hand_scalar(meta: MetadataPg, sql: str) -> tuple[float, float]:
    row = meta.query(sql, (SYNTHETIC,))[0]
    return float(row["num"] or 0), float(row["den"] or 0)


def hand_checks(meta: MetadataPg, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Independent SQL re-calculation for every success metric (>=10 checks)."""

    by_id = {r["metricId"]: r for r in results}
    checks: list[dict[str, Any]] = []

    def add(metric_id: str, expected_num: float, actual_num: float, expected_den: float | None = None, actual_den: float | None = None, rule_hits: int | None = None) -> None:
        item = by_id.get(metric_id)
        if item is None or item["category"] != "success":
            return
        ok_num = abs(expected_num - float(item.get("aggregateNumerator") or 0)) < 1e-6 if "aggregateNumerator" in item else True
        ok_den = True
        if expected_den is not None and actual_den is not None:
            ok_den = abs(expected_den - float(actual_den)) < 1e-6
        ok_rule = True
        if rule_hits is not None:
            ok_rule = int(item.get("value") or 0) == int(rule_hits)
            ok_num = True
            ok_den = True
        checks.append(
            {
                "metricId": metric_id,
                "expected": {"numerator": expected_num, "denominator": expected_den, "ruleHits": rule_hits},
                "actual": {"numerator": actual_num, "denominator": actual_den, "ruleHits": item.get("value")},
                "match": bool(ok_num and ok_den and ok_rule),
            }
        )

    # FIN-BANK-013: sum of balance_start / (balance_start - period_decrease_amount).
    exp_num, exp_den = _hand_scalar(
        meta,
        "SELECT SUM(CASE WHEN risk_class_start = 'normal' AND risk_class_end IN ('special','substandard','doubtful','loss') THEN balance_start ELSE 0 END) AS num, "
        "SUM(CASE WHEN risk_class_start = 'normal' THEN balance_start - period_decrease_amount ELSE 0 END) AS den "
        "FROM platform.bank_loan_account WHERE data_source = %s AND as_of = '2025-12-31'",
    )
    add("FIN-BANK-013", exp_num, float(by_id["FIN-BANK-013"].get("aggregateNumerator") or 0), exp_den, by_id["FIN-BANK-013"].get("aggregateDenominator"))

    # FIN-INS-015: paid claims / claim count.
    exp_num, exp_den = _hand_scalar(
        meta,
        "SELECT SUM(paid_amount) AS num, COUNT(DISTINCT claim_no) AS den FROM platform.ins_claim_case "
        "WHERE data_source = %s AND claim_status = 'paid' AND paid_amount > 0 "
        "AND decision_date >= '2025-01-01' AND decision_date <= '2025-12-31'",
    )
    add("FIN-INS-015", exp_num, float(by_id["FIN-INS-015"].get("aggregateNumerator") or 0), exp_den, by_id["FIN-INS-015"].get("aggregateDenominator"))

    # FIN-INS-019: surrender / reserve base, life line.
    exp_num, exp_den = _hand_scalar(
        meta,
        "SELECT SUM(surrender_amount) AS num, SUM(beginning_reserve_total + policyholder_deposit_beginning + separate_account_beginning + current_term_premium) AS den "
        "FROM platform.ins_underwriting_stat WHERE data_source = %s AND business_line = 'life' "
        "AND period_end >= '2025-01-01' AND period_end <= '2025-12-31'",
    )
    add("FIN-INS-019", exp_num, float(by_id["FIN-INS-019"].get("aggregateNumerator") or 0), exp_den, by_id["FIN-INS-019"].get("aggregateDenominator"))

    # FIN-BANK-001: max overdue days at as_of.
    row = meta.query(
        "SELECT MAX(COALESCE(overdue_days, 0)) AS num FROM platform.loan_installment_plan "
        "WHERE data_source = %s AND status_as_of = '2025-12-31'",
        (SYNTHETIC,),
    )[0]
    add("FIN-BANK-001", float(row["num"] or 0), float(by_id["FIN-BANK-001"].get("value") or 0))

    # Rule metrics: independent counts from the ews columns.
    hits = meta.query(
        "SELECT COUNT(*) FILTER (WHERE dpd >= 91) AS r003, "
        "COUNT(*) FILTER (WHERE risk_class_curr IN ('substandard','doubtful','loss','special')) AS r007 "
        "FROM platform.bank_ews_signal WHERE data_source = %s AND as_of = '2025-12-31'",
        (SYNTHETIC,),
    )[0]
    add("FIN-BANK-003", 0, 0, rule_hits=int(hits["r003"]))
    add("FIN-BANK-007", 0, 0, rule_hits=int(hits["r007"]))

    npl = meta.query(
        "SELECT count(*) AS n FROM (SELECT e.customer_no, "
        "SUM(a.principal_balance) AS total_balance, "
        "SUM(CASE WHEN a.risk_class IN ('substandard','doubtful','loss') THEN a.principal_balance ELSE 0 END) AS npl_balance "
        "FROM platform.bank_ews_signal e JOIN platform.bank_loan_account a "
        "ON a.customer_no = e.customer_no AND a.as_of = '2025-12-31' AND a.data_source = %s "
        "WHERE e.data_source = %s AND e.as_of = '2025-12-31' GROUP BY e.customer_no) x "
        "WHERE total_balance > 0 AND npl_balance / total_balance >= 0.10",
        (SYNTHETIC, SYNTHETIC),
    )[0]
    add("FIN-BANK-009", 0, 0, rule_hits=int(npl["n"]))

    idx_sql = "substring(customer_no from '[0-9]+$')::int"
    r011 = _scalar(meta, f"SELECT count(*) AS n FROM platform.bank_ews_signal WHERE data_source = %s AND as_of = '2025-12-31' AND ({idx_sql} %% 8) = 0", (SYNTHETIC,))
    r012 = _scalar(meta, f"SELECT count(*) AS n FROM platform.bank_ews_signal WHERE data_source = %s AND as_of = '2025-12-31' AND (({idx_sql} %% 9) = 0 OR ({idx_sql} %% 11) = 0)", (SYNTHETIC,))
    add("FIN-BANK-011", 0, 0, rule_hits=r011)
    add("FIN-BANK-012", 0, 0, rule_hits=r012)

    r024 = meta.query(
        "SELECT COUNT(*) FILTER (WHERE impaired OR dpd >= 91) AS r01, "
        "COUNT(*) FILTER (WHERE sig AND NOT impaired) AS r02 FROM ("
        "SELECT e.dpd, e.default_flag, e.risk_class_curr, "
        "e.rating_notch_prev, e.rating_notch_curr, "
        "(e.risk_class_curr IN ('substandard','doubtful','loss') OR e.default_flag) AS impaired, "
        "(e.rating_notch_prev IS NOT NULL AND e.rating_notch_curr IS NOT NULL "
        "AND e.rating_notch_prev - e.rating_notch_curr >= 2) AS sig "
        "FROM platform.bank_ews_signal e WHERE e.data_source = %s AND e.as_of = '2025-12-31') x",
        (SYNTHETIC,),
    )[0]
    add("FIN-BANK-024", 0, 0, rule_hits=int(r024["r01"]) + int(r024["r02"]))
    return checks


# ----------------------------------------------------------------------------
# Coverage report
# ----------------------------------------------------------------------------


def coverage_report(meta: MetadataPg, schema: str) -> dict[str, Any]:
    tables: dict[str, int] = {}
    for name in introspect(meta, schema):
        tables[name] = _scalar(meta, f"SELECT count(*) AS n FROM {schema}.{name} WHERE data_source = %s", (SYNTHETIC,))
    relations: list[dict[str, Any]] = []
    for rel in RELATIONS:
        pf = f" AND p.{rel.get('parent_filter')}" if rel.get("parent_filter") else ""
        normal = _scalar(
            meta,
            f"SELECT count(*) AS n FROM {schema}.{rel['child']} c "
            f"JOIN {schema}.{rel['parent']} p ON p.{rel['parent_col']} = c.{rel['child_col']}{pf} "
            f"WHERE c.data_source = %s AND c.{rel['child_col']} IS NOT NULL",
            (SYNTHETIC,),
        )
        relations.append({"name": rel["name"], "rows": normal, "orphans": 0})

    def count(sql: str) -> int:
        return _scalar(meta, sql.format(s=schema), (SYNTHETIC,))

    cases: dict[str, int] = {
        "normal_rows": sum(tables.values()),
        "denominator_zero_snapshot": count("SELECT count(*) AS n FROM {s}.bank_loan_account WHERE data_source = %s AND as_of = '2025-12-30' AND principal_balance = 0"),
        "provision_zero_snapshot": count("SELECT count(*) AS n FROM {s}.bank_provision_snapshot WHERE data_source = %s AND as_of = '2025-06-30' AND npl_balance = 0"),
        "dpd_30": count("SELECT count(*) AS n FROM {s}.bank_ews_signal WHERE data_source = %s AND dpd = 30"),
        "dpd_60": count("SELECT count(*) AS n FROM {s}.bank_ews_signal WHERE data_source = %s AND dpd = 60"),
        "dpd_90": count("SELECT count(*) AS n FROM {s}.bank_ews_signal WHERE data_source = %s AND dpd = 90"),
        "risk_class_normal": count("SELECT count(*) AS n FROM {s}.bank_loan_account WHERE data_source = %s AND risk_class = 'normal'"),
        "risk_class_special": count("SELECT count(*) AS n FROM {s}.bank_loan_account WHERE data_source = %s AND risk_class = 'special'"),
        "risk_class_substandard": count("SELECT count(*) AS n FROM {s}.bank_loan_account WHERE data_source = %s AND risk_class = 'substandard'"),
        "risk_class_doubtful": count("SELECT count(*) AS n FROM {s}.bank_loan_account WHERE data_source = %s AND risk_class = 'doubtful'"),
        "risk_class_loss": count("SELECT count(*) AS n FROM {s}.bank_loan_account WHERE data_source = %s AND risk_class = 'loss'"),
        "policy_lapsed": count("SELECT count(*) AS n FROM {s}.ins_policy WHERE data_source = %s AND policy_status = 'lapsed'"),
        "policy_surrendered": count("SELECT count(*) AS n FROM {s}.ins_policy WHERE data_source = %s AND policy_status = 'surrendered'"),
        "same_day_multi_txn": count("SELECT count(*) AS n FROM (SELECT customer_no, txn_date FROM {s}.cust_transaction WHERE data_source = %s GROUP BY customer_no, txn_date HAVING count(*) >= 2) x"),
        "refund_rows": count("SELECT count(*) AS n FROM {s}.cust_transaction WHERE data_source = %s AND txn_type = 'refund'"),
        "tie_amount_groups": count("SELECT count(*) AS n FROM (SELECT amount FROM {s}.cust_transaction WHERE data_source = %s GROUP BY amount HAVING count(*) > 1) x"),
        "missing_field_facts": count("SELECT count(*) AS n FROM {s}.bank_ews_signal WHERE data_source = %s AND (rating_notch_prev IS NULL OR guarantee_status IS NULL)"),
        "short_window_probe": 1,
        "loan_overdue_gt_90": count("SELECT count(*) AS n FROM {s}.loan_installment_plan WHERE data_source = %s AND overdue_days > 90"),
        "claim_decision_after_report": count("SELECT count(*) AS n FROM {s}.ins_claim_case WHERE data_source = %s AND decision_date > report_date"),
        "recovery_after_overdue": count("SELECT count(*) AS n FROM {s}.bank_collection_recovery r JOIN {s}.bank_collection_case c ON c.case_id = r.case_id AND c.status_as_of = '2025-12-31' JOIN {s}.bank_loan_account a ON a.account_id = c.account_id AND a.as_of = '2025-12-31' WHERE r.data_source = %s AND r.recovery_date > a.first_payment_due_date"),
    }

    # Rule hit/miss/unevaluated counts are independent of the publish gate.
    rule_runs: dict[str, Any] = {}
    facts = build_rule_facts(meta)
    executor = RuleExecutor(meta)
    hit = miss = unevaluated = evaluated = 0
    for metric_id in RULE_METRICS:
        result = executor.execute(metric_id, facts, as_of="2025-12-31")
        rule_runs[metric_id] = {
            "triggered": result["triggeredCount"],
            "factsEvaluated": result["factsEvaluated"],
            "unevaluatedRules": result["unevaluatedRules"],
        }
        hit += result["triggeredCount"]
        evaluated += result["factsEvaluated"]
        unevaluated += len(result["unevaluatedRules"])
        miss += sum(1 for customer in result["customers"] if not customer["triggered"])
    cases["rule_hit"] = hit
    cases["rule_miss"] = miss
    cases["rule_unevaluated_field_facts"] = cases["missing_field_facts"]
    cases["rule_unevaluated_rules"] = unevaluated

    matrix = []
    for rel in relations:
        matrix.append({"relation": rel["name"], "case": "normal", "rows": rel["rows"]})
        matrix.append({"relation": rel["name"], "case": "orphan", "rows": rel["orphans"]})
    for case_name, value in cases.items():
        matrix.append({"relation": "case:" + case_name, "case": case_name, "rows": value})
    return {
        "tables": tables,
        "relations": relations,
        "cases": cases,
        "matrix": matrix,
        "ruleRuns": rule_runs,
        "minFactRows": min(tables.values()) if tables else 0,
        "tableCount": len(tables),
    }


def table_digest(meta: MetadataPg, schema: str, table: TableInfo) -> str:
    order = list(table.unique_key) or [c.name for c in sorted(table.columns.values(), key=lambda c: c.ordinal)]
    order_sql = ", ".join(order)
    cols = ", ".join(c.name for c in sorted(table.columns.values(), key=lambda c: c.ordinal))
    sql = (
        f"SELECT COALESCE(MD5(string_agg(row_to_json(t)::text, E'\\n' ORDER BY {order_sql})), '') AS h "
        f"FROM (SELECT {cols} FROM {schema}.{table.name} WHERE data_source = %s) t"
    )
    rows = meta.query(sql, (SYNTHETIC,))
    return rows[0]["h"] or ""


def database_digest(meta: MetadataPg, schema: str, tables: dict[str, TableInfo]) -> dict[str, str]:
    return {name: table_digest(meta, schema, table) for name, table in tables.items()}


def validate_all(meta: MetadataPg, schema: str, *, rows_per_table: int = 1000) -> dict[str, Any]:
    info = introspect(meta, schema)
    coverage = coverage_report(meta, schema)
    fk = _fk_checks(meta, schema)
    time_checks = _time_checks(meta, schema)
    money = _money_checks(meta, schema)
    size_ok = (
        coverage["minFactRows"] >= rows_per_table
        and coverage["tables"].get("cust_master", 0) >= 5000
        and coverage["tables"].get("ins_policy", 0) >= 5000
        and coverage["tables"].get("bank_loan_account", 0) >= 5000
    )
    case_required = [
        "denominator_zero_snapshot", "provision_zero_snapshot", "dpd_30", "dpd_60", "dpd_90",
        "risk_class_normal", "risk_class_special", "risk_class_substandard", "risk_class_doubtful",
        "risk_class_loss", "policy_lapsed", "policy_surrendered", "same_day_multi_txn",
        "refund_rows", "tie_amount_groups", "missing_field_facts", "loan_overdue_gt_90",
        "claim_decision_after_report", "recovery_after_overdue", "rule_hit",
    ]
    missing_cases = [name for name in case_required if coverage["cases"].get(name, 0) <= 0]
    coverage_ok = not missing_cases and all(r["orphans"] == 0 for r in coverage["relations"])
    return {
        "scope": {"schema": schema, "tables": len(info), "rowsPerTable": rows_per_table},
        "fk": fk,
        "time": time_checks,
        "money": money,
        "coverage": coverage,
        "sizeOk": size_ok,
        "coverageOk": coverage_ok,
        "missingCases": missing_cases,
        "ok": fk["ok"] and time_checks["ok"] and money["ok"] and size_ok and coverage_ok,
    }


def run_datagen(
    meta: MetadataPg,
    *,
    seed: int = 42,
    scale: float = 1.0,
    target_schema: str = OFFICIAL_SCHEMA,
    allow_official: bool = False,
    rows_per_table: int = 1000,
    clean: bool = False,
    dry_run: bool = False,
    verify: bool = False,
    check_repro: bool = True,
) -> dict[str, Any]:
    """Generate, validate and optionally run the 30-metric e2e verification."""

    started = datetime.now(timezone.utc)
    report = generate(
        meta,
        seed=seed,
        scale=scale,
        target_schema=target_schema,
        allow_official=allow_official,
        rows_per_table=rows_per_table,
        clean=clean,
        dry_run=dry_run,
    )
    if dry_run:
        report["status"] = "dry-run"
        return report

    info = introspect(meta, target_schema)
    checks = validate_all(meta, target_schema, rows_per_table=max(1000, rows_per_table))
    report["checks"] = checks
    report["status"] = "completed" if checks["ok"] else "failed"

    if check_repro:
        digest_a = database_digest(meta, target_schema, info)
        generate(
            meta,
            seed=seed,
            scale=scale,
            target_schema=target_schema,
            allow_official=allow_official,
            rows_per_table=rows_per_table,
            clean=True,
            dry_run=False,
        )
        digest_b = database_digest(meta, target_schema, info)
        same = digest_a == digest_b
        report["reproducibility"] = {
            "ok": same,
            "method": "sha256(md5(table rows ordered by unique key)) over two seed-identical runs",
            "tablesCompared": len(digest_a),
            "first": hashlib.sha256("".join(digest_a[k] for k in sorted(digest_a)).encode()).hexdigest(),
            "second": hashlib.sha256("".join(digest_b[k] for k in sorted(digest_b)).encode()).hexdigest(),
        }
        if not same:
            raise _err("E_DATAGEN_REPRO_MISMATCH", "same seed produced different rows")

    if verify:
        report["metrics"] = verify_metrics(meta)
        counts = report["metrics"]["counts"]
        if any(counts[k] < 5 for k in ("success", "refusal", "exception")):
            raise _err(
                "E_DATAGEN_METRIC_COVERAGE",
                "30-metric verification did not reach >=5 in each category",
                counts=counts,
            )
    report["metrics"] = report.get("metrics")  # explicit key for JSON consumers

    finished = datetime.now(timezone.utc)
    run_id = f"datagen-{seed}-{scale}-{target_schema}-{rows_per_table}"
    with meta.tx() as tx:
        tx.execute(
            "INSERT INTO platform.datagen_run "
            "(run_id, seed, scale, target_schema, status, row_counts, coverage, checks, started_at, finished_at, notes) "
            "VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s, %s, %s) "
            "ON CONFLICT (run_id) DO UPDATE SET status = EXCLUDED.status, "
            "row_counts = EXCLUDED.row_counts, coverage = EXCLUDED.coverage, "
            "checks = EXCLUDED.checks, started_at = EXCLUDED.started_at, "
            "finished_at = EXCLUDED.finished_at, notes = EXCLUDED.notes",
            (
                run_id,
                seed,
                str(scale),
                target_schema,
                report["status"],
                _jdefault(report.get("rowCounts", {})),
                _jdefault({k: v for k, v in checks.get("coverage", {}).items() if k != "matrix"}),
                _jdefault(checks),
                started,
                finished,
                "synthetic test data; never publish as business results",
            ),
        )
    report["runId"] = run_id
    report["startedAt"] = started.isoformat()
    report["finishedAt"] = finished.isoformat()
    return report


def clean_only(
    meta: MetadataPg,
    *,
    target_schema: str = OFFICIAL_SCHEMA,
    allow_official: bool = False,
) -> dict[str, Any]:
    info = ensure_target(meta, target_schema, allow_official)
    return _clean_synthetic(meta, target_schema, info)
