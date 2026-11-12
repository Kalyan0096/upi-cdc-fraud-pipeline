--
-- PostgreSQL database dump
--

\restrict v7uZbNHTb0wi1kXjLtKhfXrJtogaIqQqrhj0DHuwYu0vhBLX1WWmd4pXle6IVwW

-- Dumped from database version 16.15 (Debian 16.15-1.pgdg13+2)
-- Dumped by pg_dump version 16.15 (Debian 16.15-1.pgdg13+2)

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

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: devices; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.devices (
    device_id text NOT NULL,
    user_id integer,
    first_seen timestamp with time zone DEFAULT now()
);


--
-- Name: fraud_alerts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.fraud_alerts (
    alert_id bigint NOT NULL,
    txn_id bigint,
    user_id integer,
    device_id text,
    amount numeric(12,2),
    merchant text,
    city text,
    reasons text,
    detected_at timestamp with time zone
);


--
-- Name: fraud_alerts_alert_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.fraud_alerts_alert_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: fraud_alerts_alert_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.fraud_alerts_alert_id_seq OWNED BY public.fraud_alerts.alert_id;


--
-- Name: transactions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.transactions (
    txn_id bigint NOT NULL,
    user_id integer NOT NULL,
    device_id text NOT NULL,
    amount numeric(12,2) NOT NULL,
    merchant text,
    city text,
    status text DEFAULT 'SUCCESS'::text,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: transactions_txn_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.transactions_txn_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: transactions_txn_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.transactions_txn_id_seq OWNED BY public.transactions.txn_id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    user_id integer NOT NULL,
    name text NOT NULL,
    city text
);


--
-- Name: users_user_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.users_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_user_id_seq OWNED BY public.users.user_id;


--
-- Name: v_alerts_by_rule; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_alerts_by_rule AS
 SELECT rule,
    count(*) AS alerts
   FROM ( SELECT unnest(string_to_array(fraud_alerts.reasons, ','::text)) AS rule
           FROM public.fraud_alerts) t
  GROUP BY rule
  ORDER BY (count(*)) DESC;


--
-- Name: v_fraud_by_hour; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_fraud_by_hour AS
 SELECT date_trunc('hour'::text, detected_at) AS hour,
    count(*) AS alerts,
    round(sum(amount), 2) AS amount_flagged
   FROM public.fraud_alerts
  GROUP BY (date_trunc('hour'::text, detected_at))
  ORDER BY (date_trunc('hour'::text, detected_at)) DESC;


--
-- Name: v_top_risky_users; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_top_risky_users AS
 SELECT user_id,
    count(*) AS alerts,
    round(sum(amount), 2) AS amount_flagged,
    string_agg(DISTINCT reasons, ' | '::text) AS patterns
   FROM public.fraud_alerts
  GROUP BY user_id
  ORDER BY (count(*)) DESC;


--
-- Name: fraud_alerts alert_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fraud_alerts ALTER COLUMN alert_id SET DEFAULT nextval('public.fraud_alerts_alert_id_seq'::regclass);


--
-- Name: transactions txn_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions ALTER COLUMN txn_id SET DEFAULT nextval('public.transactions_txn_id_seq'::regclass);


--
-- Name: users user_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN user_id SET DEFAULT nextval('public.users_user_id_seq'::regclass);


--
-- Name: devices devices_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.devices
    ADD CONSTRAINT devices_pkey PRIMARY KEY (device_id);


--
-- Name: fraud_alerts fraud_alerts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fraud_alerts
    ADD CONSTRAINT fraud_alerts_pkey PRIMARY KEY (alert_id);


--
-- Name: transactions transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_pkey PRIMARY KEY (txn_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- Name: devices devices_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.devices
    ADD CONSTRAINT devices_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);


--
-- Name: dbz_publication; Type: PUBLICATION; Schema: -; Owner: -
--

CREATE PUBLICATION dbz_publication FOR ALL TABLES WITH (publish = 'insert, update, delete, truncate');


--
-- PostgreSQL database dump complete
--

\unrestrict v7uZbNHTb0wi1kXjLtKhfXrJtogaIqQqrhj0DHuwYu0vhBLX1WWmd4pXle6IVwW

