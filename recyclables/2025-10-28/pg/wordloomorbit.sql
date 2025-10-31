--
-- PostgreSQL database dump
--

\restrict U0TxhzhWATdcGJHVzkqMdg5BSj3owTJIXp0zp863HbVpEXWGJbZT2AM9t6mFacu

-- Dumped from database version 16.10 (Debian 16.10-1.pgdg13+1)
-- Dumped by pg_dump version 16.10

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: activity; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.activity (
    id uuid NOT NULL,
    bookmark_id uuid NOT NULL,
    action text,
    meta jsonb,
    ts timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: bookmarks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.bookmarks (
    id uuid NOT NULL,
    title character varying(255) NOT NULL,
    text text NOT NULL,
    tags character varying[] DEFAULT '{}'::character varying[] NOT NULL,
    links character varying[] DEFAULT '{}'::character varying[] NOT NULL,
    urgency integer NOT NULL,
    daily integer NOT NULL,
    status character varying(20) NOT NULL,
    pinned boolean NOT NULL,
    image_path character varying(1024),
    next_action text,
    due_at timestamp with time zone,
    blocked_reason text,
    snooze_until timestamp with time zone,
    last_nudged_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    done_at timestamp with time zone,
    archived_at timestamp with time zone
);


--
-- Data for Name: activity; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.activity (id, bookmark_id, action, meta, ts) FROM stdin;
\.


--
-- Data for Name: bookmarks; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.bookmarks (id, title, text, tags, links, urgency, daily, status, pinned, image_path, next_action, due_at, blocked_reason, snooze_until, last_nudged_at, created_at, updated_at, done_at, archived_at) FROM stdin;
\.


--
-- Name: activity activity_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.activity
    ADD CONSTRAINT activity_pkey PRIMARY KEY (id);


--
-- Name: bookmarks bookmarks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bookmarks
    ADD CONSTRAINT bookmarks_pkey PRIMARY KEY (id);


--
-- Name: idx_activity_bookmark_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_activity_bookmark_id ON public.activity USING btree (bookmark_id);


--
-- Name: idx_bookmarks_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_bookmarks_created_at ON public.bookmarks USING btree (created_at DESC);


--
-- Name: idx_bookmarks_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_bookmarks_status ON public.bookmarks USING btree (status);


--
-- Name: ix_activity_bookmark_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_activity_bookmark_id ON public.activity USING btree (bookmark_id);


--
-- Name: activity activity_bookmark_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.activity
    ADD CONSTRAINT activity_bookmark_id_fkey FOREIGN KEY (bookmark_id) REFERENCES public.bookmarks(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict U0TxhzhWATdcGJHVzkqMdg5BSj3owTJIXp0zp863HbVpEXWGJbZT2AM9t6mFacu

