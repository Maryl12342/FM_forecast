-- Database: trains

-- DROP DATABASE IF EXISTS trains;

CREATE DATABASE trains
    WITH
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'Polish_Poland.1250'
    LC_CTYPE = 'Polish_Poland.1250'
    LOCALE_PROVIDER = 'libc'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1
    IS_TEMPLATE = False;
	
	
-- SCHEMA: public

-- DROP SCHEMA IF EXISTS public ;

CREATE SCHEMA IF NOT EXISTS public
    AUTHORIZATION pg_database_owner;

COMMENT ON SCHEMA public
    IS 'standard public schema';

GRANT USAGE ON SCHEMA public TO PUBLIC;

GRANT ALL ON SCHEMA public TO pg_database_owner;


-- Table: public.train_arrivals

-- DROP TABLE IF EXISTS public.train_arrivals;

CREATE TABLE IF NOT EXISTS public.train_arrivals
(
    train_number character varying COLLATE pg_catalog."default" NOT NULL,
    station_short_code character varying COLLATE pg_catalog."default" NOT NULL,
    timetable_type character varying COLLATE pg_catalog."default",
    date date NOT NULL,
    scheduled_arrival timestamp without time zone,
    actual_arrival timestamp without time zone,
    delay_in_minutes integer,
    cancelled boolean,
    inserted_at timestamp without time zone,
    CONSTRAINT train_arrivals_pkey PRIMARY KEY (train_number, date, station_short_code)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.train_arrivals
    OWNER to postgres;
