create schema if not exists running_corgium;

create table running_corgium.activities (
  id serial primary key,
  create_date  timestamptz,
  strava_response json,
  strava_id bigint
);

select * from activities;

-- SELECT datname FROM pg_database;
-- SELECT nspname FROM pg_catalog.pg_namespace;
--
-- SELECT table_schema, table_name
-- FROM information_schema.tables
-- WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
--   AND table_type = 'BASE TABLE';

-- ALTER TABLE running_corgium.activities ALTER COLUMN create_date TYPE timestamptz USING create_date AT TIME ZONE 'CTS';
