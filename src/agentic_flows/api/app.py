# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from typing import Annotated

from fastapi import Body, FastAPI, Header, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.routing import Match

from agentic_flows.api.v1.schemas import (
    FailureEnvelope,
    FlowRunRequest,
    ReplayRequest,
)

app = FastAPI(
    title="agentic-flows",
    description="HTTP API exposing the same contracts as the CLI.",
    version="0.1",
)


@app.middleware("http")
async def method_guard(request: Request, call_next) -> JSONResponse:
    scope = request.scope
    if scope.get("type") == "http":
        matched = False
        allowed_methods: set[str] = set()
        for route in app.router.routes:
            match, _ = route.matches(scope)
            if match in {Match.FULL, Match.PARTIAL}:
                matched = True
                if route.methods:
                    allowed_methods.update(route.methods)
        if matched and request.method not in allowed_methods:
            allow_header = ", ".join(sorted(allowed_methods))
            return JSONResponse(
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                content={"detail": "Method Not Allowed"},
                headers={"Allow": allow_header},
            )
    return await call_next(request)


@app.exception_handler(RequestValidationError)
def handle_validation_error(_: Request, __: RequestValidationError) -> JSONResponse:
    payload = FailureEnvelope(
        failure_class="structural",
        reason_code="contradiction_detected",
        violated_contract="request_validation",
        evidence_ids=[],
        determinism_impact="structural",
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=payload.model_dump(),
    )


@app.exception_handler(StarletteHTTPException)
def handle_starlette_http_exception(
    _: Request, exc: StarletteHTTPException
) -> JSONResponse:
    if exc.status_code != status.HTTP_400_BAD_REQUEST:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    payload = FailureEnvelope(
        failure_class="structural",
        reason_code="contradiction_detected",
        violated_contract="request_parse",
        evidence_ids=[],
        determinism_impact="structural",
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=payload.model_dump(),
    )


@app.get("/health")
@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
@app.get("/api/v1/ready")
def ready() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/flows/run")
def run_flow(
    _: Annotated[FlowRunRequest, Body(...)],
    x_agentic_gate: str | None = Header(None, alias="X-Agentic-Gate"),
    x_determinism_level: str | None = Header(None, alias="X-Determinism-Level"),
    x_policy_fingerprint: str | None = Header(None, alias="X-Policy-Fingerprint"),
) -> JSONResponse:
    allowed_levels = {"strict", "bounded", "probabilistic", "unconstrained"}
    if (
        x_agentic_gate is None
        or x_determinism_level is None
        or x_policy_fingerprint is None
    ):
        payload = FailureEnvelope(
            failure_class="authority",
            reason_code="contradiction_detected",
            violated_contract="headers_required",
            evidence_ids=[],
            determinism_impact="structural",
        )
        return JSONResponse(status_code=406, content=payload.model_dump())
    if x_determinism_level not in allowed_levels:
        payload = FailureEnvelope(
            failure_class="authority",
            reason_code="contradiction_detected",
            violated_contract="determinism_level_invalid",
            evidence_ids=[],
            determinism_impact="structural",
        )
        return JSONResponse(status_code=406, content=payload.model_dump())
    payload = {
        "run_id": "run-unimplemented",
        "flow_id": "flow-unimplemented",
        "status": "failed",
        "determinism_class": "structural",
        "replay_acceptability": "exact_match",
        "artifact_count": 0,
    }
    return JSONResponse(status_code=200, content=payload)


@app.post("/api/v1/flows/replay")
def replay_flow(
    _: Annotated[ReplayRequest, Body(...)],
    x_agentic_gate: str | None = Header(None, alias="X-Agentic-Gate"),
    x_determinism_level: str | None = Header(None, alias="X-Determinism-Level"),
    x_policy_fingerprint: str | None = Header(None, alias="X-Policy-Fingerprint"),
) -> JSONResponse:
    allowed_levels = {"strict", "bounded", "probabilistic", "unconstrained"}
    if (
        x_agentic_gate is None
        or x_determinism_level is None
        or x_policy_fingerprint is None
    ):
        payload = FailureEnvelope(
            failure_class="authority",
            reason_code="contradiction_detected",
            violated_contract="headers_required",
            evidence_ids=[],
            determinism_impact="structural",
        )
        return JSONResponse(status_code=406, content=payload.model_dump())
    if x_determinism_level not in allowed_levels:
        payload = FailureEnvelope(
            failure_class="authority",
            reason_code="contradiction_detected",
            violated_contract="determinism_level_invalid",
            evidence_ids=[],
            determinism_impact="structural",
        )
        return JSONResponse(status_code=406, content=payload.model_dump())
    payload = {
        "run_id": "run-unimplemented",
        "flow_id": "flow-unimplemented",
        "status": "failed",
        "determinism_class": "structural",
        "replay_acceptability": "exact_match",
        "artifact_count": 0,
    }
    return JSONResponse(status_code=200, content=payload)
