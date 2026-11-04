"""Offline tests for workflows/bulk_register_patients.py (no network)."""

import csv
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
import pytest

from particle.core import (
    ParticleAPIError,
    ParticleAuthError,
    ParticleNotFoundError,
    ParticleRateLimitError,
)
from particle.patient import PatientResponse

ROOT = Path(__file__).parent.parent
_spec = importlib.util.spec_from_file_location(
    "bulk", ROOT / "workflows" / "bulk_register_patients.py"
)
bulk = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bulk)

HEADER = (
    "address_city,address_lines(street address),address_state,date_of_birth(YYYY-MM-DD),"
    "family_name,gender(MALE/FEMALE),given_name,patient_id(external uuid),"
    '"postal_code(postal1, postal2)",telephone,ssn(optional)\n'
)
PROJECT_HEADER = "project_id," + HEADER


def write_csv(path, rows, postman=True, header=HEADER):
    path.write_text(("Body Params,,,,,,,,,,\n" if postman else "") + header + "".join(rows))


def row(pid, zip_="78624", tel="", project=None):
    r = f"AUSTIN,1 MAIN ST,TX,1947-09-29,DOE,FEMALE, JANE,{pid},{zip_},{tel},\n"
    return f"{project}," + r if project is not None else r


GOOD = row("ext-1")
OTHER = row("ext-2", tel="5128680033")
BAD_ZIP = row("ext-3", zip_="786")
BLANK_ID = row("")


@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.setenv("PARTICLE_CLIENT_ID", "x")
    monkeypatch.setenv("PARTICLE_CLIENT_SECRET", "x")
    monkeypatch.setenv("PARTICLE_SCOPE_ID", "projects/default")
    monkeypatch.setenv("PARTICLE_BASE_URL", "https://api.example.test")


@pytest.fixture
def fake_api(monkeypatch):
    """Fake HTTP client/service with a real read-back.

    Returns a namespace: .calls = [(scope, patient_id)] registered, .store = {ppid: response},
    .gets = number of GETs, .tamper = {field: value} applied to read-backs, .missing = True makes
    GET raise not-found.
    """
    api = SimpleNamespace(calls=[], store={}, gets=0, tamper={}, missing=False, get_error=None)

    def client(settings):
        return SimpleNamespace(settings=settings, close=lambda: None)

    def service(c):
        def register(p):
            api.calls.append((c.settings.scope_id, p.patient_id))
            resp = PatientResponse(
                particle_patient_id=f"pp-{p.patient_id}", **p.model_dump(mode="json")
            )
            api.store[resp.particle_patient_id] = resp
            return resp

        def get(ppid):
            api.gets += 1
            if api.get_error:
                raise api.get_error
            if api.missing or ppid not in api.store:
                raise ParticleNotFoundError("Patient", ppid)
            return api.store[ppid].model_copy(update=api.tamper)

        return SimpleNamespace(register=register, get=get)

    monkeypatch.setattr(bulk, "ParticleHTTPClient", client)
    monkeypatch.setattr(bulk, "PatientService", service)
    monkeypatch.setattr(bulk.time, "sleep", lambda s: None)
    return api


def run(tmp_path, f, *extra):
    argv = [
        str(f),
        "--results",
        str(tmp_path / "r.csv"),
        "--rejects",
        str(tmp_path / "x.csv"),
        *extra,
    ]
    if "--workers" not in extra:
        argv += ["--workers", "1"]  # deterministic order unless a test asks for concurrency
    return bulk.main(argv)


def read(path):
    return list(csv.DictReader(open(path)))


@pytest.mark.parametrize("postman", [True, False])
def test_read_rows_handles_postman_header(tmp_path, postman):
    f = tmp_path / "m.csv"
    write_csv(f, [GOOD], postman)
    ((n, r),) = list(bulk.read_rows(f))
    assert r["patient_id"] == "ext-1" and r["gender"] == "FEMALE"
    assert n == (3 if postman else 2)


def test_to_registration_maps_empty_optionals_and_strips(tmp_path):
    f = tmp_path / "m.csv"
    write_csv(f, [GOOD])
    ((_, r),) = list(bulk.read_rows(f))
    p = bulk.to_registration(r)
    assert p.given_name == "JANE" and p.telephone is None and p.address_lines == ["1 MAIN ST"]


def test_validation_summary_has_no_input_values(tmp_path):
    f = tmp_path / "m.csv"
    write_csv(f, [BAD_ZIP])
    ((_, r),) = list(bulk.read_rows(f))
    with pytest.raises(Exception) as ei:
        bulk.to_registration(r)
    s = bulk.validation_summary(ei.value)
    assert "postal_code" in s and "786" not in s.replace("postal_code", "")


def test_validate_only_rejects_bad_rows_and_calls_no_api(tmp_path, monkeypatch):
    f = tmp_path / "m.csv"
    write_csv(f, [GOOD, OTHER, BAD_ZIP, BLANK_ID])
    monkeypatch.setattr(bulk, "ParticleHTTPClient", MagicMock(side_effect=AssertionError("API")))
    assert run(tmp_path, f) == 1
    rejects = read(tmp_path / "x.csv")
    assert [r["patient_id"] for r in rejects] == ["ext-3", ""]
    assert "patient_id" in rejects[1]["error"]  # blank patient_id is rejected, field named


def test_validate_only_works_without_credentials(tmp_path, monkeypatch):
    for k in ("PARTICLE_CLIENT_ID", "PARTICLE_CLIENT_SECRET", "PARTICLE_SCOPE_ID"):
        monkeypatch.delenv(k)
    monkeypatch.chdir(tmp_path)  # no .env here
    f = tmp_path / "m.csv"
    write_csv(f, [GOOD])
    assert run(tmp_path, f) == 0


def test_execute_records_ids_and_resumes(tmp_path, fake_api):
    f = tmp_path / "m.csv"
    write_csv(f, [GOOD, OTHER])
    assert run(tmp_path, f, "--execute", "--per-minute", "6000", "--limit", "1") == 0
    assert fake_api.calls == [("projects/default", "ext-1")]
    assert run(tmp_path, f, "--execute", "--per-minute", "6000") == 0  # resumes: only ext-2
    assert fake_api.calls[1:] == [("projects/default", "ext-2")]
    got = {r["patient_id"]: r for r in read(tmp_path / "r.csv")}
    assert got["ext-1"]["particle_patient_id"] == "pp-ext-1"
    assert got["ext-2"]["scope"] == "projects/default"
    assert got["ext-2"]["base_url"] == "https://api.example.test"


def test_resume_is_bound_to_api_url(tmp_path, fake_api, monkeypatch):
    f = tmp_path / "m.csv"
    write_csv(f, [GOOD])
    assert run(tmp_path, f, "--execute", "--per-minute", "6000") == 0
    monkeypatch.setenv("PARTICLE_BASE_URL", "https://other.example.test")
    assert run(tmp_path, f, "--execute", "--per-minute", "6000") == 0
    assert len(fake_api.calls) == 2  # a different target does not count as already done


def test_multi_project_rows_use_their_own_scope(tmp_path, fake_api):
    f = tmp_path / "m.csv"
    write_csv(
        f,
        [row("a", project="PRJ-A"), row("b", project="projects/prj-b"), row("c", project="")],
        header=PROJECT_HEADER,
    )
    assert run(tmp_path, f, "--execute", "--per-minute", "6000") == 0
    assert fake_api.calls == [
        ("projects/prj-a", "a"),
        ("projects/prj-b", "b"),
        ("projects/default", "c"),
    ]
    assert {r["scope"] for r in read(tmp_path / "r.csv")} == {
        "projects/prj-a",
        "projects/prj-b",
        "projects/default",
    }


def test_same_patient_id_in_two_projects_is_not_a_duplicate(tmp_path, fake_api):
    f = tmp_path / "m.csv"
    write_csv(f, [row("a", project="p1"), row("a", project="p2")], header=PROJECT_HEADER)
    assert run(tmp_path, f, "--execute", "--per-minute", "6000") == 0
    assert len(fake_api.calls) == 2


def test_organization_scope_is_rejected(tmp_path, fake_api):
    f = tmp_path / "m.csv"
    write_csv(f, [row("a", project="organizations/o1")], header=PROJECT_HEADER)
    assert run(tmp_path, f, "--execute", "--per-minute", "6000") == 1
    assert fake_api.calls == []
    assert "organization" in read(tmp_path / "x.csv")[0]["error"]


def test_formula_like_ids_are_escaped_and_still_resume(tmp_path, fake_api):
    f = tmp_path / "m.csv"
    write_csv(f, [row("=cmd|x")])
    assert run(tmp_path, f, "--execute", "--per-minute", "6000") == 0
    assert read(tmp_path / "r.csv")[0]["patient_id"] == "'=cmd|x"  # defused on disk
    assert run(tmp_path, f, "--execute", "--per-minute", "6000") == 0
    assert len(fake_api.calls) == 1  # original ID recovered on resume, not re-registered


def test_negative_limit_is_rejected(tmp_path):
    f = tmp_path / "m.csv"
    write_csv(f, [GOOD])
    with pytest.raises(SystemExit):
        run(tmp_path, f, "--limit", "-1")


def test_interrupt_returns_nonzero(tmp_path, monkeypatch):
    f = tmp_path / "m.csv"
    write_csv(f, [GOOD])

    def boom(p):
        raise KeyboardInterrupt

    monkeypatch.setattr(bulk, "ParticleHTTPClient", lambda s: SimpleNamespace(close=lambda: None))
    monkeypatch.setattr(bulk, "PatientService", lambda c: SimpleNamespace(register=boom))
    assert run(tmp_path, f, "--execute", "--per-minute", "6000") == bulk.EXIT_INTERRUPTED


def test_results_file_from_older_layout_is_refused(tmp_path):
    f = tmp_path / "m.csv"
    write_csv(f, [GOOD])
    (tmp_path / "r.csv").write_text("patient_id,particle_patient_id,registered_at\n")
    with pytest.raises(SystemExit):
        run(tmp_path, f)


def test_rate_limit_is_slept_out(monkeypatch):
    monkeypatch.setattr(bulk.time, "sleep", lambda s: None)
    svc = MagicMock()
    svc.register.side_effect = [ParticleRateLimitError(retry_after=1), "ok"]
    assert bulk.register_with_backoff(svc, object()) == "ok"


def test_csv_template_validates():
    template = ROOT / "sample-data" / "bulk_patients_template.csv"
    rows = list(bulk.read_rows(template))
    assert len(rows) == 3
    for _, r in rows:
        bulk.normalize_scope(r["project_id"], "")
        bulk.to_registration(r)


def test_registered_patients_are_read_back_and_verified(tmp_path, fake_api):
    f = tmp_path / "m.csv"
    write_csv(f, [GOOD, OTHER])
    assert run(tmp_path, f, "--execute", "--per-minute", "6000") == 0
    assert fake_api.gets == 2
    assert len(read(tmp_path / "r.csv")) == 2


def test_read_back_mismatch_is_rejected_and_not_recorded(tmp_path, fake_api):
    f = tmp_path / "m.csv"
    write_csv(f, [GOOD])
    fake_api.tamper = {"family_name": "SOMEONE ELSE"}
    assert run(tmp_path, f, "--execute", "--per-minute", "6000") == 1
    assert read(tmp_path / "r.csv") == []  # not recorded, so a rerun re-submits and re-checks
    (rej,) = read(tmp_path / "x.csv")
    assert rej["stage"] == "verify" and "family_name" in rej["error"]
    assert "pp-ext-1" in rej["error"] and "SOMEONE" not in rej["error"]  # no values leak


def test_patient_missing_on_read_back_is_rejected(tmp_path, fake_api):
    f = tmp_path / "m.csv"
    write_csv(f, [GOOD])
    fake_api.missing = True
    assert run(tmp_path, f, "--execute", "--per-minute", "6000") == 1
    assert fake_api.gets == bulk.VERIFY_ATTEMPTS
    assert read(tmp_path / "x.csv")[0]["stage"] == "verify"


def test_no_verify_skips_the_read_back(tmp_path, fake_api):
    f = tmp_path / "m.csv"
    write_csv(f, [GOOD])
    assert run(tmp_path, f, "--execute", "--per-minute", "6000", "--no-verify") == 0
    assert fake_api.gets == 0 and len(read(tmp_path / "r.csv")) == 1


def many(n, project=None):
    return [row(f"id-{i:03d}", project=project) for i in range(n)]


def test_parallel_registers_each_patient_exactly_once(tmp_path, fake_api):
    f = tmp_path / "m.csv"
    write_csv(f, many(60))
    assert run(tmp_path, f, "--execute", "--per-minute", "60000", "--workers", "4") == 0
    ids = [pid for _, pid in fake_api.calls]
    assert sorted(ids) == [f"id-{i:03d}" for i in range(60)]  # none missed, none duplicated
    rows = read(tmp_path / "r.csv")
    assert len(rows) == 60 and len({r["patient_id"] for r in rows}) == 60
    assert fake_api.gets == 60


def test_parallel_multi_project_uses_each_projects_client(tmp_path, fake_api):
    f = tmp_path / "m.csv"
    rows = [row(f"a{i}", project="p1") for i in range(10)] + [
        row(f"b{i}", project="p2") for i in range(10)
    ]
    write_csv(f, rows, header=PROJECT_HEADER)
    assert run(tmp_path, f, "--execute", "--per-minute", "60000", "--workers", "4") == 0
    by_scope = {}
    for scope, pid in fake_api.calls:
        by_scope.setdefault(scope, []).append(pid[0])
    assert set(by_scope) == {"projects/p1", "projects/p2"}
    assert set(by_scope["projects/p1"]) == {"a"} and set(by_scope["projects/p2"]) == {"b"}


def test_default_is_two_workers(tmp_path, fake_api, capsys):
    f = tmp_path / "m.csv"
    write_csv(f, [GOOD])
    argv = [str(f), "--execute", "--per-minute", "60000"]
    argv += ["--results", str(tmp_path / "r.csv"), "--rejects", str(tmp_path / "x.csv")]
    assert bulk.main(argv) == 0
    assert "with 2 worker(s)" in capsys.readouterr().out


def test_invalid_worker_count_is_rejected(tmp_path):
    f = tmp_path / "m.csv"
    write_csv(f, [GOOD])
    with pytest.raises(SystemExit):
        run(tmp_path, f, "--workers", "0")


def test_repeated_failures_stop_the_run(tmp_path, monkeypatch):
    f = tmp_path / "m.csv"
    write_csv(f, many(100))

    def register(p):
        raise ParticleAPIError("boom", 500)

    monkeypatch.setattr(bulk, "ParticleHTTPClient", lambda s: SimpleNamespace(close=lambda: None))
    monkeypatch.setattr(bulk, "PatientService", lambda c: SimpleNamespace(register=register))
    assert run(tmp_path, f, "--execute", "--per-minute", "60000", "--workers", "4") == 3
    failed = len(read(tmp_path / "x.csv"))
    assert bulk.MAX_CONSECUTIVE_FAILURES <= failed < 100  # stopped early, not after all 100


def test_auth_failure_stops_the_run(tmp_path, monkeypatch):
    f = tmp_path / "m.csv"
    write_csv(f, many(20))

    def register(p):
        raise ParticleAuthError("bad credentials")

    monkeypatch.setattr(bulk, "ParticleHTTPClient", lambda s: SimpleNamespace(close=lambda: None))
    monkeypatch.setattr(bulk, "PatientService", lambda c: SimpleNamespace(register=register))
    assert run(tmp_path, f, "--execute", "--per-minute", "60000", "--workers", "3") == 2
    assert read(tmp_path / "r.csv") == []


def test_rate_limit_pauses_every_worker():
    slept = []
    pacer = bulk.Pacer(per_minute=6000)
    real_sleep = bulk.time.sleep
    bulk.time.sleep = slept.append
    try:
        pacer.pause(5)  # as if one worker received a 429 with Retry-After: 5
        pacer.wait()  # a different worker asks for its next slot
    finally:
        bulk.time.sleep = real_sleep
    assert slept and slept[0] >= 4.5


def test_transport_error_is_recorded_as_a_failure(tmp_path, monkeypatch):
    f = tmp_path / "m.csv"
    write_csv(f, many(3))

    def register(p):
        raise httpx.ReadTimeout("timed out")

    monkeypatch.setattr(bulk, "ParticleHTTPClient", lambda s: SimpleNamespace(close=lambda: None))
    monkeypatch.setattr(bulk, "PatientService", lambda c: SimpleNamespace(register=register))
    assert run(tmp_path, f, "--execute", "--per-minute", "60000") == 1  # no traceback
    rejects = read(tmp_path / "x.csv")
    assert len(rejects) == 3 and rejects[0]["stage"] == "api"
    assert "ReadTimeout" in rejects[0]["error"]


def test_transport_error_on_read_back_is_a_verify_failure(tmp_path, fake_api):
    f = tmp_path / "m.csv"
    write_csv(f, [GOOD])
    fake_api.get_error = httpx.ConnectError("down")
    assert run(tmp_path, f, "--execute", "--per-minute", "6000") == 1
    assert read(tmp_path / "x.csv")[0]["stage"] == "verify"


def test_auth_failure_on_read_back_stops_the_run(tmp_path, fake_api):
    f = tmp_path / "m.csv"
    write_csv(f, many(10))
    fake_api.get_error = ParticleAuthError("expired")
    assert run(tmp_path, f, "--execute", "--per-minute", "60000", "--workers", "1") == 2
    assert len(fake_api.calls) == 1  # stopped before the second registration


@pytest.mark.parametrize("retry_after", [0, -5])
def test_non_positive_retry_after_uses_the_default_wait(monkeypatch, retry_after):
    slept = []
    monkeypatch.setattr(bulk.time, "sleep", slept.append)
    svc = MagicMock()
    svc.register.side_effect = [ParticleRateLimitError(retry_after=retry_after), "ok"]
    assert bulk.register_with_backoff(svc, object()) == "ok"
    assert slept == [30]
