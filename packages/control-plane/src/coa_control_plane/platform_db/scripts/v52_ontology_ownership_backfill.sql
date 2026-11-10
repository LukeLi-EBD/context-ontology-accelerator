-- V52 backfill: attribute namespace_id from an EXPLICIT version -> namespace map.
--
-- V52 adds namespace_id as NULLable because no V1..V51 table records which
-- namespace authored an ontology row. This script never guesses: it reads the
-- mapping the operator supplies and updates only the listed versions. Run it
-- against a copy first, then compare the printed NULL inventory with the
-- expected count.
--
-- Usage (psql):
--   psql "$DSN" -f v52_ontology_ownership_backfill.sql -v map_csv=C:/path/version-namespace.csv
--
-- map_csv is a CSV with a header and exactly two columns:
--   version_id,namespace_id
--   ont-abc...,ed70a15c-2d42-4dc9-8c61-33b2584f05fd
--
-- Every version in the CSV must exist in platform.ontology_version; a typo
-- aborts the transaction instead of silently leaving a row unattributed.

\set ON_ERROR_STOP on

BEGIN;

CREATE TEMP TABLE v52_namespace_map (
  version_id   text PRIMARY KEY,
  namespace_id uuid NOT NULL
) ON COMMIT DROP;

\copy v52_namespace_map (version_id, namespace_id) FROM :'map_csv' WITH (FORMAT csv, HEADER true)

DO $$
DECLARE
  missing bigint;
BEGIN
  SELECT count(*) INTO missing
    FROM v52_namespace_map m
    LEFT JOIN platform.ontology_version v USING (version_id)
   WHERE v.version_id IS NULL;
  IF missing > 0 THEN
    RAISE EXCEPTION 'V52 backfill: % version_id(s) in the map do not exist', missing;
  END IF;
END $$;

UPDATE platform.ontology_version v
   SET namespace_id = m.namespace_id
  FROM v52_namespace_map m
 WHERE m.version_id = v.version_id
   AND v.namespace_id IS DISTINCT FROM m.namespace_id;

UPDATE platform.ontology_proposal p
   SET namespace_id = v.namespace_id
  FROM platform.ontology_version v
 WHERE v.version_id = p.version_id
   AND p.namespace_id IS DISTINCT FROM v.namespace_id;

UPDATE platform.ontology_event e
   SET namespace_id = v.namespace_id
  FROM platform.ontology_version v
 WHERE v.version_id = e.version_id
   AND e.namespace_id IS DISTINCT FROM v.namespace_id;

COMMIT;

-- Post-backfill inventory: these rows still have no namespace on purpose.
SELECT 'ontology_version' AS table_name, count(*) AS rows_without_namespace
  FROM platform.ontology_version WHERE namespace_id IS NULL
UNION ALL
SELECT 'ontology_proposal', count(*)
  FROM platform.ontology_proposal WHERE namespace_id IS NULL
UNION ALL
SELECT 'ontology_event', count(*)
  FROM platform.ontology_event WHERE namespace_id IS NULL;
