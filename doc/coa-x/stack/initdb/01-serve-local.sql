-- The platform-core runtime expects two databases:
--   platform    -> metadata / facts / metric catalogue (created by POSTGRES_DB)
--   serve_local -> the embedded lifecycle app's own database
-- Both are migrated to the code's schema version by the `migrate` service.
CREATE DATABASE serve_local OWNER platform;
