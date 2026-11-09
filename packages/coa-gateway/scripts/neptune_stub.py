"""Local HTTP stub that stands in for a Neptune SPARQL endpoint.

It does NOT implement Neptune. It only:
  1. asserts the request looks like a SigV4-signed Neptune query
     (``Authorization: AWS4-HMAC-SHA256 Credential=<ak>/<date>/<region>/neptune-db/aws4_request``,
     ``SignedHeaders``, 64-hex ``Signature``, ``X-Amz-Date``);
  2. replies with a canned SPARQL 1.1 JSON result set.

Usage: ``python neptune_stub.py [port]`` — binds 127.0.0.1 only.
"""

from __future__ import annotations

import json
import re
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

SIGV4 = re.compile(
    r"^AWS4-HMAC-SHA256 Credential=(\w+)/(\d{8})/([a-z0-9-]+)/neptune-db/aws4_request, "
    r"SignedHeaders=([a-z0-9;-]+), Signature=([0-9a-f]{64})$"
)

SEEN: list[dict[str, str]] = []


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: object) -> None:  # silence default access log
        return

    def do_POST(self) -> None:  # noqa: N802 - stdlib naming
        if self.path != "/sparql":
            self.send_error(404, "expected POST /sparql")
            return
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode()
        sparql = parse_qs(body).get("query", [""])[0]

        auth = self.headers.get("Authorization", "")
        match = SIGV4.match(auth)
        record = {
            "path": self.path,
            "authorization": auth,
            "sigv4_shape_ok": bool(match),
            "credential_scope": f"{match.group(2)}/{match.group(3)}/neptune-db/aws4_request" if match else "",
            "signed_headers": match.group(4) if match else "",
            "x_amz_date": self.headers.get("X-Amz-Date", ""),
            "accept": self.headers.get("Accept", ""),
            "content_type": self.headers.get("Content-Type", ""),
            "sparql": sparql,
        }
        SEEN.append(record)
        print("STUB_REQUEST " + json.dumps(record, ensure_ascii=False), flush=True)

        if not match:
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b'{"message":"signature shape rejected"}')
            return

        is_ask = bool(re.search(r"\bASK\b", sparql, re.IGNORECASE)) and "SELECT" not in sparql.upper()
        if is_ask:
            payload = {"head": {}, "boolean": True}
        else:
            payload = {
                "head": {"vars": ["s", "label"]},
                "results": {
                    "bindings": [
                        {"s": {"type": "uri", "value": "http://example.org/tbox#Department"},
                         "label": {"type": "literal", "value": "Department"}},
                        {"s": {"type": "uri", "value": "http://example.org/tbox#Organization"},
                         "label": {"type": "literal", "value": "Organization"}},
                    ]
                },
            }
        raw = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/sparql-results+json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 18099
    server = HTTPServer(("127.0.0.1", port), Handler)
    print(f"STUB_READY 127.0.0.1:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
