"""SQL statement splitter that is aware of literals and comments.

Migration files are split on ``;`` before being handed to the driver. A naive
``str.split(";")`` breaks on semicolons that live inside comments, quoted
literals, quoted identifiers or dollar-quoted bodies (function definitions).
This splitter walks the text once and only cuts on statement-level semicolons.

Rules honoured:
  * ``--`` line comments run to the end of the line
  * ``/* ... */`` block comments, including nested ones (PostgreSQL allows them)
  * ``'...'`` literals and ``"..."`` identifiers, with doubled-quote escapes
  * ``$tag$ ... $tag$`` dollar-quoted bodies (``$$`` has an empty tag)

Comment and literal text is preserved verbatim in the emitted statement; only
the split points change, so replaying the existing migrations yields the same
statements as before.
"""

from __future__ import annotations

import re

_DOLLAR_TAG = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)?\$")


def split_sql_statements(sql: str) -> list[str]:
    """Split ``sql`` into non-empty statements at statement-level semicolons."""
    statements: list[str] = []
    buffer: list[str] = []
    has_code = False
    index = 0
    length = len(sql)

    while index < length:
        char = sql[index]

        if char == "-" and sql.startswith("--", index):
            end = sql.find("\n", index)
            end = length if end < 0 else end
            buffer.append(sql[index:end])
            index = end
            continue

        if char == "/" and sql.startswith("/*", index):
            depth = 1
            cursor = index + 2
            while cursor < length and depth:
                if sql.startswith("/*", cursor):
                    depth += 1
                    cursor += 2
                elif sql.startswith("*/", cursor):
                    depth -= 1
                    cursor += 2
                else:
                    cursor += 1
            buffer.append(sql[index:cursor])
            index = cursor
            continue

        if char in ("'", '"'):
            has_code = True
            quote = char
            cursor = index + 1
            while cursor < length:
                if sql[cursor] == quote:
                    if cursor + 1 < length and sql[cursor + 1] == quote:
                        cursor += 2
                        continue
                    cursor += 1
                    break
                cursor += 1
            buffer.append(sql[index:cursor])
            index = cursor
            continue

        if char == "$":
            match = _DOLLAR_TAG.match(sql, index)
            if match:
                tag = match.group(0)
                end = sql.find(tag, match.end())
                cursor = length if end < 0 else end + len(tag)
                buffer.append(sql[index:cursor])
                has_code = True
                index = cursor
                continue

        if char == ";":
            statement = "".join(buffer).strip()
            if has_code and statement:
                statements.append(statement)
            buffer = []
            has_code = False
            index += 1
            continue

        if not char.isspace():
            has_code = True
        buffer.append(char)
        index += 1

    tail = "".join(buffer).strip()
    if has_code and tail:
        statements.append(tail)
    return statements
