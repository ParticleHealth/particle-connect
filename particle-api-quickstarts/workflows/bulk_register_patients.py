"""Bulk-register patients from a CSV via POST /api/v2/patients.

Reuses the SDK (auth, retries, validation, PatientService). Adds only what a bulk load needs:
CSV parsing, pacing, resume, and results/rejects files. No PHI is written to either file or
printed: only your patient_id, the Particle patient ID and an error summary.

Safe by default: without --execute the script only validates the CSV and calls no API.

Usage:
    python workflows/bulk_register_patients.py patients.csv                      # validate only
    python workflows/bulk_register_patients.py patients.csv --execute --limit 5  # small trial
    python workflows/bulk_register_patients.py patients.csv --execute --per-minute 120

Projects: patients are registered into the project in PARTICLE_SCOPE_ID. To load several
projects in one run, add a `project_id` column; rows with a value use that project, rows without
use PARTICLE_SCOPE_ID. The credential must have access to every project listed (the project is
chosen when the access token is requested, so the script keeps one token per project).

Resume: rerun the same command. A patient already in the results file for the same API URL and
project is skipped.
Accepted CSV: a header row, optionally preceded by a Postman-style "Body Params" row; column
names may carry hints in parentheses, e.g. "gender(MALE/FEMALE)".
"""

from __future__ import annotations

import argparse
import csv
import itertools
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import httpx
from pydantic import ValidationError

from particle.core import (
    ParticleAPIError,
    ParticleAuthError,
    ParticleError,
    ParticleHTTPClient,
    ParticleNotFoundError,
    ParticleRateLimitError,
    ParticleSettings,
    configure_logging,
)
from particle.patient import PatientRegistration, PatientService

RESULT_FIELDS = ["patient_id", "scope", "base_url", "particle_patient_id", "registered_at"]
REJECT_FIELDS = ["row", "patient_id", "scope", "stage", "error"]
MAX_RATE_LIMIT_RETRIES = 5
VERIFY_ATTEMPTS = 3  # a read right after the write may briefly miss; retry before failing
VERIFY_FIELDS = (
    "patient_id",
    "given_name",
    "family_name",
    "date_of_birth",
    "gender",
    "postal_code",
    "address_city",
    "address_state",
)
THROUGHPUT_INTERVAL_S = 60  # seconds between throughput lines
MAX_CONSECUTIVE_FAILURES = 10  # stop rather than write thousands of rejects on an outage
EXIT_INTERRUPTED = 130
FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def normalize_header(name: str) -> str:
    """'gender(MALE/FEMALE)' -> 'gender'."""
    return re.sub(r"\(.*\)$", "", name.strip().lstrip("﻿")).strip()


def read_rows(path: Path):
    """Yield (row_number, dict) with normalized headers. Row numbers are CSV line numbers."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        lines = f.readlines()
    start = 1 if lines and lines[0].lower().startswith("body params") else 0
    reader = csv.reader(lines[start:])
    headers = [normalize_header(h) for h in next(reader)]
    for i, row in enumerate(reader, start=start + 2):
        yield i, dict(zip(headers, row))


def normalize_scope(raw: str, default: str) -> str:
    """'<id>' or 'projects/<id>' -> 'projects/<id>' (lowercase); blank -> the default scope."""
    scope = (raw or "").strip().lower() or default
    if scope.startswith("organizations/"):
        raise ValueError("project_id: an organization scope cannot register patients")
    if scope and not scope.startswith("projects/"):
        scope = f"projects/{scope}"
    return scope


def to_registration(row: dict) -> PatientRegistration:
    """Map a CSV row to a validated PatientRegistration. Empty optional fields become None."""
    street = row.get("address_lines", "").strip()
    return PatientRegistration(
        patient_id=row.get("patient_id", ""),
        given_name=row.get("given_name", ""),
        family_name=row.get("family_name", ""),
        date_of_birth=row.get("date_of_birth", ""),
        gender=row.get("gender", "").strip().upper(),
        postal_code=row.get("postal_code", "").strip(),
        address_city=row.get("address_city", ""),
        address_state=row.get("address_state", "").strip(),
        address_lines=[street] if street else None,
        telephone=row.get("telephone", "").strip() or None,
        ssn=row.get("ssn", "").strip() or None,
        email=row.get("email", "").strip() or None,
    )


def validation_summary(e: ValidationError) -> str:
    """Field names and messages only: pydantic's str(e) echoes input values (PHI)."""
    return "; ".join(f"{'.'.join(map(str, err['loc']))}: {err['msg']}" for err in e.errors())


def safe_cell(value):
    """Defuse spreadsheet formulas in user-supplied text (CSV injection)."""
    if isinstance(value, str) and value.startswith(FORMULA_PREFIXES):
        return "'" + value
    return value


def unsafe_cell(value: str) -> str:
    """Inverse of safe_cell, so resume sees the original patient_id."""
    if value.startswith("'") and value[1:].startswith(FORMULA_PREFIXES):
        return value[1:]
    return value


def check_header(path: Path, fields: list[str]) -> None:
    """Refuse to append to a file written with a different column layout."""
    if not path.exists() or path.stat().st_size == 0:
        return
    with open(path, newline="") as f:
        header = next(csv.reader(f), [])
    if header != fields:
        sys.exit(
            f"{path} has a different column layout (written by an older version?). "
            "Move it aside or choose a new path with --results / --rejects."
        )


def load_done(results: Path, base_url: str) -> tuple[set[tuple[str, str]], int]:
    """Return ({(scope, patient_id)} already registered at base_url, rows for other targets)."""
    if not results.exists():
        return set(), 0
    done, other = set(), 0
    with open(results, newline="") as f:
        for r in csv.DictReader(f):
            if r["base_url"] == base_url:
                done.add((r["scope"], unsafe_cell(r["patient_id"])))
            else:
                other += 1
    return done, other


def append_writer(path: Path, fields: list[str]):
    new = not path.exists() or path.stat().st_size == 0
    f = open(path, "a", newline="")
    w = csv.DictWriter(f, fieldnames=fields)
    if new:
        w.writeheader()
        f.flush()
    return f, w


def write_row(f, writer, row: dict) -> None:
    writer.writerow({k: safe_cell(v) for k, v in row.items()})
    f.flush()


class _Stopped(Exception):
    """Raised inside a worker when the run was stopped while it waited for a slot."""


class Pacer:
    """Request pacing shared by all workers.

    wait() takes the next paced slot (at most --per-minute registrations across all workers).
    pause() makes every worker hold off after a 429, not just the one that received it.
    """

    def __init__(self, per_minute: float):
        self._lock = threading.Lock()
        self._interval = 60.0 / per_minute
        self._next = time.monotonic()
        self._pause_until = 0.0

    def wait(self) -> None:
        with self._lock:
            slot = max(self._next, self._pause_until, time.monotonic())
            self._next = slot + self._interval
        delay = slot - time.monotonic()
        if delay > 0:
            time.sleep(delay)

    def idle(self) -> None:
        """Honor a pause without taking a paced slot (used for read-back GETs)."""
        delay = self._pause_until - time.monotonic()
        if delay > 0:
            time.sleep(delay)

    def pause(self, seconds: float) -> None:
        with self._lock:
            self._pause_until = max(self._pause_until, time.monotonic() + seconds)


def with_backoff(call, on_limit=None, prefix=""):
    """Run call(), sleeping out 429s (the SDK raises them rather than retrying)."""
    for attempt in range(MAX_RATE_LIMIT_RETRIES + 1):
        try:
            return call()
        except ParticleRateLimitError as e:
            if attempt == MAX_RATE_LIMIT_RETRIES:
                raise
            retry_after = getattr(e, "retry_after", None)
            wait = retry_after if retry_after and retry_after > 0 else 30  # ignore <= 0
            if on_limit:
                on_limit(wait)
            print(f"{prefix}rate limited; sleeping {wait}s", flush=True)
            time.sleep(wait)


def register_with_backoff(service: PatientService, patient: PatientRegistration):
    return with_backoff(lambda: service.register(patient))


def _norm(value) -> str:
    return str(getattr(value, "value", value)).strip().casefold()


def compare_stored(posted, stored) -> list[str]:
    """Names of fields where the stored record differs from what the API accepted.

    `posted` is the POST response (the request as the API normalized it) and `stored` is the
    record read back with GET, so server-side normalization (state codes, lower-cased IDs) does
    not cause false mismatches. Returns field names only, never values.
    """
    fields = ("particle_patient_id", *VERIFY_FIELDS)
    return [f for f in fields if _norm(getattr(posted, f, None)) != _norm(getattr(stored, f, None))]


def verify_registered(service: PatientService, posted, on_limit=None, prefix="") -> list[str]:
    """Read the patient back and return mismatched field names (empty list = verified)."""
    for attempt in range(VERIFY_ATTEMPTS):
        try:
            stored = with_backoff(lambda: service.get(posted.particle_patient_id), on_limit, prefix)
        except ParticleNotFoundError:
            if attempt == VERIFY_ATTEMPTS - 1:
                return ["not found on read-back"]
            time.sleep(1)
            continue
        return compare_stored(posted, stored)
    return ["not found on read-back"]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("csv", type=Path)
    p.add_argument(
        "--execute", action="store_true", help="actually call the API (default: validate only)"
    )
    p.add_argument(
        "--per-minute", type=float, default=60, help="max patients per minute (default 60)"
    )
    p.add_argument(
        "--workers",
        type=int,
        default=2,
        help="concurrent registrations (default 2); --per-minute still caps the total rate",
    )
    p.add_argument("--limit", type=int, help="stop after N API registrations this run")
    p.add_argument(
        "--no-verify",
        dest="verify",
        action="store_false",
        help="skip reading each patient back after registering (one extra GET per patient)",
    )
    p.add_argument("--results", type=Path, default=Path("bulk_results.csv"))
    p.add_argument("--rejects", type=Path, default=Path("bulk_rejects.csv"))
    args = p.parse_args(argv)
    if args.per_minute <= 0:
        p.error("--per-minute must be > 0")
    if args.limit is not None and args.limit < 0:
        p.error("--limit must be >= 0")
    if args.workers < 1:
        p.error("--workers must be >= 1")

    configure_logging()
    try:
        settings = ParticleSettings()
    except ValidationError:
        if args.execute:
            raise
        settings = None  # validate-only works without credentials
    base_url = settings.base_url if settings else ""
    default_scope = normalize_scope(settings.scope_id, "") if settings else ""

    check_header(args.results, RESULT_FIELDS)
    check_header(args.rejects, REJECT_FIELDS)
    done, other_target = load_done(args.results, base_url) if settings else (set(), 0)
    rejects_f, rejects = append_writer(args.rejects, REJECT_FIELDS)
    results_f, results = append_writer(args.results, RESULT_FIELDS)

    total = skipped = invalid = 0
    ok = failed = consecutive_failures = 0
    exit_code = None  # first fatal condition wins
    interrupted = False
    lock = threading.Lock()  # guards the counters, the output files and printing
    stop = threading.Event()
    pacer = Pacer(args.per_minute)
    local = threading.local()  # one client per worker thread (each keeps its own tokens)
    clients: list[ParticleHTTPClient] = []

    worker_ids = itertools.count(1)

    def wtag() -> str:
        if not hasattr(local, "wid"):
            local.wid = next(worker_ids)  # numbered in order of first use
        return f"[w{local.wid}]"

    def service_for(scope: str) -> PatientService:
        if not hasattr(local, "services"):
            local.services = {}
        if scope not in local.services:
            client = ParticleHTTPClient(settings.model_copy(update={"scope_id": scope}))
            with lock:
                clients.append(client)
            local.services[scope] = PatientService(client)
        return local.services[scope]

    # Pass 1: validate everything up front so we can report "i/N" during the run.
    pending: list[tuple[int, str, str, PatientRegistration]] = []
    for rownum, row in read_rows(args.csv):
        total += 1
        raw_pid = row.get("patient_id", "").strip()
        try:
            scope = normalize_scope(row.get("project_id", ""), default_scope)
            patient = to_registration(row)
        except (ValidationError, ValueError) as e:
            invalid += 1
            msg = validation_summary(e) if isinstance(e, ValidationError) else str(e)
            write_row(
                rejects_f,
                rejects,
                {
                    "row": rownum,
                    "patient_id": raw_pid,
                    "scope": row.get("project_id", ""),
                    "stage": "validate",
                    "error": msg,
                },
            )
            print(f"INVALID row {rownum} patient_id={raw_pid}: {msg}", flush=True)
            continue
        if (scope, patient.patient_id) in done:
            skipped += 1
            continue
        pending.append((rownum, patient.patient_id, scope, patient))
    if args.limit is not None:
        pending = pending[: args.limit]
    n = len(pending)
    scopes = sorted({s for _, _, s, _ in pending})
    multi = len(scopes) > 1
    print(
        f"CSV rows={total} already_done={skipped} invalid={invalid} to_register_this_run={n}",
        flush=True,
    )
    if other_target:
        print(
            f"Note: {other_target} results rows belong to a different API URL and are ignored.",
            flush=True,
        )

    def fail(i, rownum, pid, scope, tag, stage, detail, label):
        """Record a failed patient. Caller must not hold `lock`."""
        nonlocal failed, consecutive_failures, exit_code
        with lock:
            failed += 1
            consecutive_failures += 1
            write_row(
                rejects_f,
                rejects,
                {"row": rownum, "patient_id": pid, "scope": scope, "stage": stage, "error": detail},
            )
            print(f"{wtag()} {label} {i}/{n}{tag} patient_id={pid}: {detail}", flush=True)
            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES and exit_code is None:
                exit_code = 3
                stop.set()
                print(
                    f"{consecutive_failures} consecutive failures, stopping.",
                    file=sys.stderr,
                    flush=True,
                )

    def stop_for_auth(scope, i, e):
        """Bad credentials: stop every worker and exit 2. Caller must not hold `lock`."""
        nonlocal exit_code
        with lock:
            if exit_code is None:
                exit_code = 2
                print(
                    f"AUTH FAILURE for scope={scope}, stopping at {i}/{n}: {e}",
                    file=sys.stderr,
                    flush=True,
                )
            stop.set()

    def process(i, item):
        nonlocal ok, consecutive_failures
        rownum, pid, scope, patient = item
        if stop.is_set():
            return
        tag = f" scope={scope}" if multi else ""
        timing: dict[str, float] = {}  # last create / get latency in ms
        try:
            service = service_for(scope)

            def paced_register():
                pacer.wait()
                if stop.is_set():
                    raise _Stopped
                t0 = time.perf_counter()
                try:
                    return service.register(patient)
                finally:
                    timing["create"] = (time.perf_counter() - t0) * 1000

            try:
                resp = with_backoff(paced_register, pacer.pause, f"{wtag()} ")
            except _Stopped:
                return
        except ParticleAuthError as e:
            stop_for_auth(scope, i, e)
            return
        except (ParticleError, httpx.TransportError) as e:
            status = e.status_code if isinstance(e, ParticleAPIError) else type(e).__name__
            fail(
                i, rownum, pid, scope, tag, "api", f"{status}: {getattr(e, 'message', e)}", "FAILED"
            )
            return
        if args.verify:
            try:
                pacer.idle()
                t0 = time.perf_counter()
                try:
                    mismatches = verify_registered(service, resp, pacer.pause, f"{wtag()} ")
                finally:
                    timing["get"] = (time.perf_counter() - t0) * 1000
            except ParticleAuthError as e:
                stop_for_auth(scope, i, e)
                return
            except (ParticleError, httpx.TransportError) as e:
                mismatches = [f"{type(e).__name__}: {getattr(e, 'message', e)}"]
            if mismatches:
                detail = (
                    f"registered as {resp.particle_patient_id[:8]}... but read-back check failed: "
                    + ", ".join(mismatches)
                )
                fail(i, rownum, pid, scope, tag, "verify", detail, "VERIFY FAILED")
                return
        with lock:
            consecutive_failures = 0
            ok += 1
            write_row(
                results_f,
                results,
                {
                    "patient_id": pid,
                    "scope": scope,
                    "base_url": base_url,
                    "particle_patient_id": resp.particle_patient_id,
                    "registered_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            print(
                f"{wtag()} {i}/{n}{tag} patient_id={pid} PPID={resp.particle_patient_id[:8]}... "
                f"create={timing['create']:.0f}ms"
                + (f" get={timing['get']:.0f}ms (verified)" if args.verify else ""),
                flush=True,
            )

    try:
        if not args.execute:
            print("Validate-only run (no API calls). Use --execute to register.", flush=True)
            ok = n
        else:
            print(
                f"Registering against {base_url} projects={scopes or ['(none)']} "
                f"at {args.per_minute:g}/min with {args.workers} worker(s)",
                flush=True,
            )
            executor = ThreadPoolExecutor(max_workers=args.workers)
            done_evt = threading.Event()
            started = time.monotonic()

            def report_throughput():
                last = 0
                while not done_evt.wait(THROUGHPUT_INTERVAL_S):
                    with lock:
                        now_ok, now_failed = ok, failed
                    print(
                        f"THROUGHPUT last {THROUGHPUT_INTERVAL_S}s: {now_ok - last} registered "
                        f"({now_ok}/{n} done, {now_failed} failed, "
                        f"{(time.monotonic() - started) / 60:.0f} min elapsed)",
                        flush=True,
                    )
                    last = now_ok

            threading.Thread(target=report_throughput, daemon=True).start()
            try:
                futures = [executor.submit(process, i, it) for i, it in enumerate(pending, 1)]
                for fut in as_completed(futures):
                    fut.result()  # surface unexpected errors from workers
            except KeyboardInterrupt:
                interrupted = True
                stop.set()
                print(
                    "Interrupted; finishing in-flight requests. Rerun the same command to resume.",
                    file=sys.stderr,
                    flush=True,
                )
            except BaseException:
                stop.set()
                raise
            finally:
                executor.shutdown(wait=True, cancel_futures=True)
                done_evt.set()
    finally:
        for client in clients:
            client.close()
        results_f.close()
        rejects_f.close()

    label = "registered" if args.execute else "valid"
    print(
        f"rows={total} already_done={skipped} {label}={ok} api_failed={failed} "
        f"invalid={invalid} results={args.results} rejects={args.rejects}",
        flush=True,
    )
    if interrupted:
        return EXIT_INTERRUPTED
    if exit_code is not None:
        return exit_code
    return 0 if failed == 0 and invalid == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
