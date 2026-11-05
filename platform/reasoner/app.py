"""Reasoner service (S5): thin HTTP wrapper around ROBOT and Jena.

Boundary (D18): this service adds no reasoning of its own. It concatenates the
two source graphs (N-Triples is a Turtle subset), runs `robot reason` or
`riot --rdfs` in a subprocess, and returns the reasoned graph.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict

ROBOT_JAR = os.environ.get("ROBOT_JAR", "/opt/robot/robot.jar")
RIOT_BIN = os.environ.get("RIOT_BIN", "/opt/jena/bin/riot")
JAVA_OPTS = os.environ.get("JAVA_OPTS", "-Xmx2g")
REASON_TIMEOUT = int(os.environ.get("REASON_TIMEOUT_SECONDS", "600"))
PROFILE_REASONER = {
    # ROBOT's `reason` exposes ELK/HermiT/JFact only; RDFS closure is not offered.
    "EL": "ELK",
    "OWL2EL": "ELK",
}

app = FastAPI(title="Platform Reasoner", version="s5.1")

_version_cache: str | None = None


def robot_version() -> str:
    global _version_cache
    if _version_cache is not None:
        return _version_cache
    try:
        completed = subprocess.run(
            ["java", "-jar", ROBOT_JAR, "--version"],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (OSError, subprocess.SubprocessError):
        return "unavailable"
    text = (completed.stdout or completed.stderr or "").strip()
    _version_cache = text.splitlines()[0] if text else "unknown"
    return _version_cache


@app.get("/healthz")
def healthz() -> dict[str, object]:
    version = robot_version()
    ok = (
        version not in ("unavailable", "unknown")
        and Path(ROBOT_JAR).is_file()
        and Path(RIOT_BIN).is_file()
    )
    if not ok:
        raise HTTPException(
            status_code=503,
            detail={"status": "fail", "robot": version, "riot": Path(RIOT_BIN).is_file()},
        )
    return {
        "status": "ok",
        "robotVersion": version,
        "engine": "robot",
        "rdfs": "jena-riot",
    }


class ReasonRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tbox: str
    abox: str = ""
    profile: str = "EL"
    consistencyFirst: bool = True


@app.post("/v1/reason")
def reason(request: ReasonRequest) -> dict[str, object]:
    reasoner = PROFILE_REASONER.get(request.profile)
    if reasoner is None:
        raise HTTPException(
            status_code=400,
            detail=f"unsupported profile {request.profile!r}; allowed {sorted(PROFILE_REASONER)}",
        )
    if not Path(ROBOT_JAR).is_file():
        raise HTTPException(status_code=503, detail="robot.jar is missing")

    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="reason-") as tmp:
        merged = Path(tmp) / "merged.ttl"
        output = Path(tmp) / "reasoned.ttl"
        merged.write_text(request.tbox + "\n" + request.abox, encoding="utf-8")
        command = [
            "java",
            *JAVA_OPTS.split(),
            "-jar",
            ROBOT_JAR,
            "reason",
            "--reasoner",
            reasoner,
            # ROBOT only emits inferred axioms that a generator requests. ELK
            # classifies individuals only with ClassAssertion; -d true adds the
            # indirect (transitive) types so `alice a Person, Thing` is entailed.
            "--axiom-generators",
            "SubClass ClassAssertion",
            "-d",
            "true",
            "--input",
            merged.as_posix(),
            "--output",
            output.as_posix(),
        ]
        try:
            completed = subprocess.run(
                command, capture_output=True, text=True, timeout=REASON_TIMEOUT
            )
        except subprocess.TimeoutExpired as exc:
            raise HTTPException(
                status_code=504,
                detail=f"robot reason timed out after {REASON_TIMEOUT}s",
            ) from exc

        ms = int((time.monotonic() - started) * 1000)
        if completed.returncode != 0:
            blob = f"{completed.stdout}\n{completed.stderr}".lower()
            if "inconsisten" in blob:
                return {
                    "consistent": False,
                    "reasoned": "",
                    "ms": ms,
                    "robotVersion": robot_version(),
                }
            raise HTTPException(
                status_code=500,
                detail={
                    "message": "robot reason failed",
                    "exit": completed.returncode,
                    "stderr": (completed.stderr or completed.stdout or "")[-800:],
                },
            )
        if not output.is_file():
            return {
                "consistent": True,
                "reasoned": "",
                "ms": ms,
                "robotVersion": robot_version(),
            }
        return {
            "consistent": True,
            "reasoned": output.read_text(encoding="utf-8"),
            "ms": ms,
            "robotVersion": robot_version(),
        }


class RdfsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tbox: str
    abox: str = ""


@app.post("/v1/rdfs")
def rdfs(request: RdfsRequest) -> dict[str, object]:
    """OQ-39: RDFS closure stage of materialize, delegated to Jena `riot --rdfs`.

    Jena's backward RDFS rules cover subClassOf/subPropertyOf transitivity
    plus domain/range typing, which ROBOT/ELK does not (S5 design section 9.4).
    This is still a mature external tool invoked as a one-shot batch per request.
    """
    if not Path(RIOT_BIN).is_file():
        raise HTTPException(status_code=503, detail="jena riot is missing")

    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="rdfs-") as tmp:
        merged = Path(tmp) / "merged.nt"
        merged.write_text(request.tbox + "\n" + request.abox, encoding="utf-8")
        command = [
            RIOT_BIN,
            f"--rdfs={merged.as_posix()}",
            "--output=nt",
            merged.as_posix(),
        ]
        try:
            completed = subprocess.run(
                command, capture_output=True, text=True, timeout=REASON_TIMEOUT
            )
        except subprocess.TimeoutExpired as exc:
            raise HTTPException(
                status_code=504,
                detail=f"jena riot timed out after {REASON_TIMEOUT}s",
            ) from exc
        ms = int((time.monotonic() - started) * 1000)
        if completed.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail={
                    "message": "jena rdfs closure failed",
                    "exit": completed.returncode,
                    "stderr": (completed.stderr or completed.stdout or "")[-800:],
                },
            )
        return {
            "reasoned": completed.stdout,
            "ms": ms,
            "stages": {"rdfs": ms},
        }
