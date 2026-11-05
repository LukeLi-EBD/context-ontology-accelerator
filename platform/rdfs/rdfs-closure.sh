#!/usr/bin/env bash
# One-shot RDFS closure job (OQ-34). Driven by Apache Jena riot, not by
# platform code. `riot --rdfs=<vocab>` runs Jena's RDFS backward rule engine
# (subClassOf/subPropertyOf transitivity, domain and range); the probe on
# 2026-11-05 confirmed all four closures, unlike ROBOT/ELK.
# Exit codes:
#   0  closure written
#   2  input file missing      -> E_RDFS_INPUT_MISSING
#   3  riot failed             -> E_RDFS_FAILED
set -euo pipefail

input="${1:-/data/jobs/rdfs/in.ttl}"
output="${2:-/data/jobs/rdfs/out.nt}"
# Vocabulary defaults to the input itself (schema + data in one document).
vocab="${3:-$input}"

if [ ! -f "$input" ]; then
  echo "E_RDFS_INPUT_MISSING: $input" >&2
  exit 2
fi
if [ ! -f "$vocab" ]; then
  echo "E_RDFS_VOCAB_MISSING: $vocab" >&2
  exit 2
fi

mkdir -p "$(dirname "$output")"
tmp="${output}.tmp"
if ! /opt/jena/bin/riot --rdfs="$vocab" --output=nt "$input" > "$tmp"; then
  rm -f "$tmp"
  echo "E_RDFS_FAILED: riot --rdfs=$vocab --output=nt $input" >&2
  exit 3
fi
mv "$tmp" "$output"
echo "rdfs closure written: $output"
