# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Local ASGI bridge for the metric-service Lambda handler (development only).

Translates an HTTP request into the API Gateway proxy event that
``coa_metrics.api.metric_api_handler.handler`` expects, so the service can run
on a workstation under ``uvicorn``. The deployed entry point is unchanged; this
module is not referenced by any Lambda handler.

Run:
  uvicorn coa_metrics.local_asgi:app --host 127.0.0.1 --port 8011
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import Response

from coa_metrics.api.metric_api_handler import handler

app = FastAPI(title="metric-service (local)", version="local")


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe that never touches a backend."""
    return {"status": "ok"}


def _path_parameters(parts: list[str]) -> dict[str, str]:
    """Derive API Gateway pathParameters from the URL segments."""
    params: dict[str, str] = {}
    if len(parts) >= 2 and parts[0] == "namespaces":
        params["namespaceId"] = parts[1]
    if len(parts) >= 4 and parts[2] == "metrics":
        params["name"] = parts[3]
    if len(parts) >= 4 and parts[2] == "import-jobs":
        params["jobId"] = parts[3]
    return params


@app.api_route(
    "/{full_path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
)
async def dispatch(request: Request, full_path: str) -> Response:
    """Build the proxy event, call the Lambda handler, mirror its response."""
    path = "/" + full_path
    parts = [segment for segment in path.split("/") if segment]
    raw_body = await request.body()
    query = request.query_params

    event: dict[str, Any] = {
        "httpMethod": request.method,
        "resource": path,
        "path": path,
        "pathParameters": _path_parameters(parts) or None,
        "queryStringParameters": dict(query) or None,
        "multiValueQueryStringParameters": {key: query.getlist(key) for key in query} or None,
        "headers": dict(request.headers),
        "body": raw_body.decode("utf-8") if raw_body else None,
        "isBase64Encoded": False,
        # A stable identity keeps the idempotency decorator from failing closed
        # when a request carries clientToken.
        "requestContext": {"authorizer": {"principalId": "local-dev"}},
    }

    result = handler(event, None)
    return Response(
        content=result.get("body", ""),
        status_code=int(result.get("statusCode", 200)),
        headers=result.get("headers") or {},
    )


__all__ = ["app"]
