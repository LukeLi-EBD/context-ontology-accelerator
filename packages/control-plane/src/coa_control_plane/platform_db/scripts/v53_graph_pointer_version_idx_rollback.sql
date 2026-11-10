-- V53 rollback: drop the graph_pointer version index.
--
-- The index only accelerates reverse lookup / FK checks; dropping it returns
-- the V52 shape and loses no data.

BEGIN;

DROP INDEX IF EXISTS platform.graph_pointer_version_idx;

COMMIT;
