"""Run one local process of the COA query chain (no AWS).

    python run_local.py context-manager --port 8091
    python run_local.py data-layer      --port 8092

Both roles take their whole configuration from the environment; see
``05-本地链路复验.md`` for the configuration keys the caller must export.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

REPO = r"D:\agentABC\coa"
_SRC = (
    "packages/coa-ports/src",
    "packages/coa-runtime/src",
    "packages/local-providers/src",
    "packages/metric-service/src",
    "packages/platform-core/src",
    "libs/common/src",
    "packages/context-manager/src",
)
for _rel in _SRC:
    _path = f"{REPO}/{_rel}"
    if _path not in sys.path:
        sys.path.insert(0, _path)


def run_context_manager(host: str, port: int) -> None:
    # `resource` is a POSIX-only module imported at package import time; the
    # shim must land before coa_common is imported.
    spec = importlib.util.spec_from_file_location(
        "win_compat", f"{REPO}/packages/local-providers/src/coa_local_providers/win_compat.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ensure_resource_module()

    from coa_serve.main import app

    app.run(host=host, port=port)


def run_data_layer(host: str, port: int) -> None:
    dl_src = f"{REPO}/packages/data-layer/src"
    if dl_src not in sys.path:
        sys.path.insert(0, dl_src)

    from coa_data_layer.handler import handler

    class ApiGatewayProxy(BaseHTTPRequestHandler):
        """API Gateway REST proxy event shape, one route: POST .../query."""

        protocol_version = "HTTP/1.1"

        def do_POST(self) -> None:  # noqa: N802 - http.server API
            length = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(length).decode("utf-8") if length else ""
            parts = self.path.strip("/").split("/")
            namespace = parts[1] if len(parts) > 1 else ""
            event = {
                "httpMethod": "POST",
                "resource": "/namespaces/{namespaceId}/query",
                "pathParameters": {"namespaceId": namespace},
                "headers": dict(self.headers.items()),
                "body": body,
                "requestContext": {
                    "authorizer": {
                        "principalId": "alice",
                        "email": "alice@example.com",
                        "groups": "",
                        "globalRoles": "",
                    }
                },
            }
            result = handler(event, None)
            raw = (result.get("body") or json.dumps({"message": "empty"})).encode("utf-8")
            self.send_response(int(result.get("statusCode") or 200))
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def log_message(self, fmt: str, *args) -> None:
            sys.stderr.write("DL " + fmt % args + "\n")

    HTTPServer((host, port), ApiGatewayProxy).serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("role", choices=("context-manager", "data-layer"))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args()
    if args.role == "context-manager":
        run_context_manager(args.host, args.port)
    else:
        run_data_layer(args.host, args.port)


if __name__ == "__main__":
    main()
