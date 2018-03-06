--
-- PostgreSQL database dump
--

-- Dumped from database version 9.6.6
-- Dumped by pg_dump version 9.6.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

-- Already create by 01-init-user-db.sh
-- CREATE DATABASE imported_from_cryoweb WITH TEMPLATE = template0 ENCODING = 'UTF8' LC_COLLATE = 'en_US.utf8' LC_CTYPE = 'en_US.utf8';

-- change ownerships
ALTER DATABASE imported_from_cryoweb OWNER TO apiis_admin;

-- connect to imported_from_cryoweb
\connect imported_from_cryoweb

--
-- Name: apiis_admin; Type: SCHEMA; Schema: -; Owner: apiis_admin
--

CREATE SCHEMA apiis_admin;


ALTER SCHEMA apiis_admin OWNER TO apiis_admin;

SET search_path = apiis_admin, pg_catalog;

--
-- Name: get_storage_level(integer); Type: FUNCTION; Schema: apiis_admin; Owner: apiis_admin
--

CREATE FUNCTION get_storage_level(integer) RETURNS integer
    LANGUAGE plpgsql
    AS $_$
DECLARE
	pNodeId ALIAS FOR $1;
        ParentId integer;


BEGIN

    IF ( pNodeId = 0 ) THEN
	RETURN 0;
    END IF;

    SELECT parent_id
    INTO ParentId
    FROM   storage
    WHERE  storage_id=pNodeId;

    IF (ParentId is NULL) THEN
    	RETURN -1;
    ELSE
	    RETURN get_storage_level(ParentId)+1;
    END IF;

END;
$_$;


ALTER FUNCTION apiis_admin.get_storage_level(integer) OWNER TO apiis_admin;

--
-- Name: get_storage_path(integer); Type: FUNCTION; Schema: apiis_admin; Owner: apiis_admin
--

CREATE FUNCTION get_storage_path(integer) RETURNS text
    LANGUAGE plpgsql
    AS $_$
DECLARE
	pNodeId ALIAS FOR $1;
        ParentId integer;
	StorageName text;


BEGIN

    IF ( pNodeId = 0 ) THEN
	RETURN '';
    END IF;

    SELECT parent_id,storage_name
    INTO ParentId, StorageName
    FROM   storage
    WHERE  storage_id=pNodeId;

    IF (ParentId is NULL or ParentId=0) THEN
    	RETURN StorageName;
    ELSE
	    RETURN get_storage_path(ParentId)||'>'||StorageName;
    END IF;

END;
$_$;


ALTER FUNCTION apiis_admin.get_storage_path(integer) OWNER TO apiis_admin;

--
-- Name: is_child_of(integer, integer); Type: FUNCTION; Schema: apiis_admin; Owner: apiis_admin
--

CREATE FUNCTION is_child_of(integer, integer) RETURNS boolean
    LANGUAGE plpgsql
    AS $_$
DECLARE
	pChildNodeId ALIAS FOR $1;
	pParentNodeId ALIAS FOR $2;
	res boolean := false;
	s INTEGER[];
	top INTEGER;
        counter INTEGER;
        popped INTEGER;
        parent RECORD;

BEGIN
	top := 0;
--    	s := {};
	s[top] := pChildNodeId;
        counter := 1;

    IF ( pParentNodeId = pChildNodeId) THEN
	RETURN true;
    END IF;
    WHILE (counter <> 0) LOOP
	popped := s[top];
	top := top - 1;
	counter := counter - 1;

	FOR parent IN SELECT st.parent_id FROM storage AS st
	    WHERE st.storage_id = popped
	LOOP
	    IF (parent.parent_id = pParentNodeId) THEN
		res:=true;
		RETURN res;
	    ELSE
		top := top + 1;
		s[top] = parent.parent_id;
		counter := counter + 1;
	    END IF;
	END LOOP;
    END LOOP;

    RETURN res;

END;
$_$;


ALTER FUNCTION apiis_admin.is_child_of(integer, integer) OWNER TO apiis_admin;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: ar_dbtdescriptors; Type: TABLE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE TABLE ar_dbtdescriptors (
    descriptor_id integer,
    descriptor_name text,
    descriptor_value text,
    descriptor_desc text,
    last_change_dt timestamp without time zone,
    last_change_user text,
    dirty boolean,
    chk_lvl smallint,
    guid integer,
    owner text,
    version integer,
    synch boolean
);


ALTER TABLE ar_dbtdescriptors OWNER TO apiis_admin;

--
-- Name: ar_dbtpolicies; Type: TABLE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE TABLE ar_dbtpolicies (
    dbtpolicy_id integer,
    action_id integer,
    table_id integer,
    descriptor_id integer,
    last_change_dt timestamp without time zone,
    last_change_user text,
    dirty boolean,
    chk_lvl smallint,
    guid integer,
    owner text,
    version integer,
    synch boolean
);


ALTER TABLE ar_dbtpolicies OWNER TO apiis_admin;

--
-- Name: ar_dbttables; Type: TABLE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE TABLE ar_dbttables (
    table_id integer,
    table_name text,
    table_columns text,
    table_desc text,
    last_change_dt timestamp without time zone,
    last_change_user text,
    dirty boolean,
    chk_lvl smallint,
    guid integer,
    owner text,
    version integer,
    synch boolean
);


ALTER TABLE ar_dbttables OWNER TO apiis_admin;

--
-- Name: ar_role_dbtpolicies; Type: TABLE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE TABLE ar_role_dbtpolicies (
    role_id integer,
    dbtpolicy_id integer,
    last_change_dt timestamp without time zone,
    last_change_user text,
    dirty boolean,
    chk_lvl smallint,
    guid integer,
    owner text,
    version integer,
    synch boolean
);


ALTER TABLE ar_role_dbtpolicies OWNER TO apiis_admin;

--
-- Name: codes; Type: TABLE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE TABLE codes (
    ext_code text,
    class text,
    db_code integer,
    short_name text,
    long_name text,
    description text,
    opening_dt date,
    closing_dt date,
    last_change_dt timestamp without time zone,
    last_change_user text,
    dirty boolean,
    chk_lvl smallint,
    guid integer,
    owner text,
    version integer,
    synch boolean
);


ALTER TABLE codes OWNER TO apiis_admin;

--
-- Name: ar_role_stpolicies; Type: TABLE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE TABLE ar_role_stpolicies (
    role_id integer,
    stpolicy_id integer,
    last_change_dt timestamp without time zone,
    last_change_user text,
    dirty boolean,
    chk_lvl smallint,
    guid integer,
    owner text,
    version integer,
    synch boolean
);


ALTER TABLE ar_role_stpolicies OWNER TO apiis_admin;

--
-- Name: ar_stpolicies; Type: TABLE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE TABLE ar_stpolicies (
    stpolicy_id integer,
    stpolicy_name text,
    stpolicy_type text,
    stpolicy_desc text,
    last_change_dt timestamp without time zone,
    last_change_user text,
    dirty boolean,
    chk_lvl smallint,
    guid integer,
    owner text,
    version integer,
    synch boolean
);


ALTER TABLE ar_stpolicies OWNER TO apiis_admin;

--
-- Name: animal; Type: TABLE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE TABLE animal (
    db_animal integer,
    db_sire integer,
    db_dam integer,
    db_sex integer,
    db_breed integer,
    db_species integer,
    birth_dt date,
    birth_year text,
    latitude double precision,
    longitude double precision,
    image_id integer,
    db_org integer,
    la_rep text,
    la_rep_dt date,
    last_change_dt timestamp without time zone,
    last_change_user text,
    dirty boolean,
    chk_lvl smallint,
    guid integer,
    owner text,
    version integer,
    synch boolean,
    db_hybrid integer,
    comment text,
    file_id integer
);


ALTER TABLE animal OWNER TO apiis_admin;

--
-- Name: ar_constraints; Type: TABLE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE TABLE ar_constraints (
    cons_id integer,
    cons_name text,
    cons_type text,
    cons_desc text,
    last_change_dt timestamp without time zone,
    last_change_user text,
    dirty boolean,
    chk_lvl smallint,
    guid integer,
    owner text,
    version integer,
    synch boolean
);


ALTER TABLE ar_constraints OWNER TO apiis_admin;

--
-- Name: ar_role_constraints; Type: TABLE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE TABLE ar_role_constraints (
    cons_id integer,
    first_role_id integer,
    second_role_id integer,
    last_change_dt timestamp without time zone,
    last_change_user text,
    dirty boolean,
    chk_lvl smallint,
    guid integer,
    owner text,
    version integer,
    synch boolean
);


ALTER TABLE ar_role_constraints OWNER TO apiis_admin;

--
-- Name: ar_roles; Type: TABLE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE TABLE ar_roles (
    role_id integer,
    role_name text,
    role_long_name text,
    role_type text,
    role_subset text,
    role_descr text,
    last_change_dt timestamp without time zone,
    last_change_user text,
    dirty boolean,
    chk_lvl smallint,
    guid integer,
    owner text,
    version integer,
    synch boolean
);


ALTER TABLE ar_roles OWNER TO apiis_admin;

--
-- Name: ar_user_roles; Type: TABLE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE TABLE ar_user_roles (
    user_id integer,
    role_id integer,
    last_change_dt timestamp without time zone,
    last_change_user text,
    dirty boolean,
    chk_lvl smallint,
    guid integer,
    owner text,
    version integer,
    synch boolean
);


ALTER TABLE ar_user_roles OWNER TO apiis_admin;

--
-- Name: ar_users; Type: TABLE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE TABLE ar_users (
    user_id integer,
    user_login text,
    user_password text,
    user_language_id integer,
    user_marker text,
    user_disabled boolean,
    user_status boolean,
    user_last_login timestamp without time zone,
    user_last_activ_time time without time zone,
    user_session_id text,
    last_change_dt timestamp without time zone,
    last_change_user text,
    dirty boolean,
    chk_lvl smallint,
    guid integer,
    owner text,
    version integer,
    synch boolean
);


ALTER TABLE ar_users OWNER TO apiis_admin;

--
-- Name: ar_users_data; Type: TABLE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE TABLE ar_users_data (
    user_id integer,
    user_first_name text,
    user_second_name text,
    user_institution text,
    user_email text,
    user_country text,
    user_street text,
    user_town text,
    user_zip text,
    user_other_info text,
    opening_dt date,
    closing_dt date,
    last_change_dt timestamp without time zone,
    last_change_user text,
    creation_dt timestamp without time zone,
    creation_user text,
    end_dt timestamp without time zone,
    end_user text,
    dirty boolean,
    chk_lvl smallint,
    guid integer,
    owner text,
    version integer,
    synch boolean
);


ALTER TABLE ar_users_data OWNER TO apiis_admin;

--
-- Name: blobs; Type: TABLE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE TABLE blobs (
    blob_id integer,
    blob bytea,
    last_change_dt timestamp without time zone,
    last_change_user text,
    dirty boolean,
    chk_lvl smallint,
    guid integer,
    owner text,
    version integer,
    synch boolean,
    db_mimetype integer
);


ALTER TABLE blobs OWNER TO apiis_admin;

--
-- Name: breeds_species; Type: TABLE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE TABLE breeds_species (
    breed_id integer,
    db_breed integer,
    db_species integer,
    efabis_mcname text,
    efabis_species text,
    efabis_country text,
    efabis_lang text,
    chk_lvl smallint,
    dirty boolean,
    guid bigint,
    last_change_dt timestamp without time zone,
    last_change_user text,
    owner text,
    synch boolean,
    version smallint
);


ALTER TABLE breeds_species OWNER TO apiis_admin;

--
-- Name: contacts; Type: TABLE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE TABLE contacts (
    db_contact integer,
    title text,
    salutation text,
    first_name text,
    second_name text,
    third_name text,
    birth_dt date,
    db_language integer,
    street text,
    zip text,
    town text,
    db_country integer,
    label text,
    phone text,
    phone2 text,
    fax text,
    email text,
    bank_name text,
    bank_zip text,
    account text,
    comment text,
    opening_dt date,
    closing_dt date,
    chk_lvl smallint,
    dirty boolean,
    guid bigint,
    last_change_dt timestamp without time zone,
    last_change_user text,
    owner text,
    synch boolean,
    version smallint
);


ALTER TABLE contacts OWNER TO apiis_admin;

--
-- Name: entry_codes; Type: VIEW; Schema: apiis_admin; Owner: apiis_admin
--

CREATE VIEW entry_codes AS
 SELECT codes.ext_code,
    codes.class,
    codes.db_code,
    codes.short_name,
    codes.long_name,
    codes.description,
    codes.opening_dt,
    codes.closing_dt,
    codes.last_change_dt,
    codes.last_change_user,
    codes.dirty,
    codes.chk_lvl,
    codes.guid,
    codes.owner,
    codes.version,
    codes.synch
   FROM codes
  WHERE (codes.closing_dt IS NULL);


ALTER TABLE entry_codes OWNER TO apiis_admin;

--
-- Name: transfer; Type: TABLE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE TABLE transfer (
    db_animal integer,
    ext_animal text,
    db_unit integer,
    id_set integer,
    opening_dt date,
    closing_dt date,
    last_change_dt timestamp without time zone,
    last_change_user text,
    dirty boolean,
    chk_lvl smallint,
    guid integer,
    owner text,
    version integer,
    synch boolean
);


ALTER TABLE transfer OWNER TO apiis_admin;

--
-- Name: entry_transfer; Type: VIEW; Schema: apiis_admin; Owner: apiis_admin
--

CREATE VIEW entry_transfer AS
 SELECT transfer.db_animal,
    transfer.ext_animal,
    transfer.db_unit,
    transfer.id_set,
    transfer.opening_dt,
    transfer.closing_dt,
    transfer.last_change_dt,
    transfer.last_change_user,
    transfer.dirty,
    transfer.chk_lvl,
    transfer.guid,
    transfer.owner,
    transfer.version,
    transfer.synch
   FROM transfer
  WHERE (transfer.closing_dt IS NULL);


ALTER TABLE entry_transfer OWNER TO apiis_admin;

--
-- Name: unit; Type: TABLE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE TABLE unit (
    db_unit integer,
    ext_unit text,
    ext_id text,
    db_contact integer,
    db_member integer,
    opening_dt date,
    closing_dt date,
    last_change_dt timestamp without time zone,
    last_change_user text,
    dirty boolean,
    chk_lvl smallint,
    guid integer,
    owner text,
    version integer,
    synch boolean
);


ALTER TABLE unit OWNER TO apiis_admin;

--
-- Name: entry_unit; Type: VIEW; Schema: apiis_admin; Owner: apiis_admin
--

CREATE VIEW entry_unit AS
 SELECT unit.db_unit,
    unit.ext_unit,
    unit.ext_id,
    unit.db_contact,
    unit.db_member,
    unit.opening_dt,
    unit.closing_dt,
    unit.last_change_dt,
    unit.last_change_user,
    unit.dirty,
    unit.chk_lvl,
    unit.guid,
    unit.owner,
    unit.version,
    unit.synch
   FROM unit
  WHERE (unit.closing_dt IS NULL);


ALTER TABLE entry_unit OWNER TO apiis_admin;

--
-- Name: event; Type: TABLE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE TABLE event (
    event_id integer,
    db_event_type integer,
    db_sampler integer,
    event_dt date,
    db_location integer,
    last_change_dt timestamp without time zone,
    last_change_user text,
    dirty boolean,
    chk_lvl smallint,
    guid integer,
    owner text,
    version integer,
    synch boolean
);


ALTER TABLE event OWNER TO apiis_admin;

--
-- Name: inspool; Type: TABLE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE TABLE inspool (
    ds text,
    record_seq integer,
    in_date date,
    ext_unit integer,
    proc_dt date,
    status text,
    record text,
    last_change_dt timestamp without time zone,
    last_change_user text,
    dirty boolean,
    chk_lvl smallint,
    guid integer,
    owner text,
    version integer,
    synch boolean
);


ALTER TABLE inspool OWNER TO apiis_admin;

--
-- Name: inspool_err; Type: TABLE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE TABLE inspool_err (
    record_seq integer,
    err_type text,
    action text,
    dbtable text,
    dbcol text,
    err_source text,
    short_msg text,
    long_msg text,
    ext_col text,
    ext_val text,
    mod_val text,
    comp_val text,
    target_col text,
    ds text,
    ext_unit text,
    status text,
    err_dt timestamp without time zone,
    last_change_dt timestamp without time zone,
    last_change_user text,
    dirty boolean,
    chk_lvl smallint,
    guid integer,
    owner text,
    version integer,
    synch boolean
);


ALTER TABLE inspool_err OWNER TO apiis_admin;

--
-- Name: languages; Type: TABLE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE TABLE languages (
    lang_id integer,
    iso_lang text,
    lang text,
    last_change_dt timestamp without time zone,
    last_change_user text,
    creation_dt timestamp without time zone,
    creation_user text,
    end_dt timestamp without time zone,
    end_user text,
    dirty boolean,
    chk_lvl smallint,
    guid integer,
    owner text,
    version integer,
    synch boolean
);


ALTER TABLE languages OWNER TO apiis_admin;

--
-- Name: load_stat; Type: TABLE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE TABLE load_stat (
    ds text,
    job_start timestamp without time zone,
    job_end timestamp without time zone,
    status integer,
    rec_tot_no smallint,
    rec_err_no smallint,
    rec_ok_no smallint,
    last_change_dt timestamp without time zone,
    last_change_user text,
    dirty boolean,
    chk_lvl smallint,
    guid integer,
    owner text,
    version integer,
    synch boolean
);


ALTER TABLE load_stat OWNER TO apiis_admin;

--
-- Name: locations; Type: TABLE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE TABLE locations (
    db_animal integer,
    db_location integer,
    entry_dt date,
    db_entry_action integer,
    exit_dt date,
    db_exit_action integer,
    chk_lvl smallint,
    dirty boolean,
    guid bigint,
    last_change_dt timestamp without time zone,
    last_change_user text,
    owner text,
    synch boolean,
    version smallint
);


ALTER TABLE locations OWNER TO apiis_admin;

--
-- Name: movements; Type: TABLE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE TABLE movements (
    movements_id integer,
    from_storage integer,
    to_storage integer,
    no_units smallint,
    comment text,
    action_dt timestamp without time zone,
    action_type text,
    chk_lvl smallint,
    dirty boolean,
    guid bigint,
    last_change_dt timestamp without time zone,
    last_change_user text,
    owner text,
    synch boolean,
    version smallint
);


ALTER TABLE movements OWNER TO apiis_admin;

--
-- Name: new_pest; Type: TABLE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE TABLE new_pest (
    class text,
    key text,
    trait text,
    estimator double precision,
    pev double precision,
    last_change_dt timestamp without time zone,
    last_change_user text,
    dirty boolean,
    chk_lvl smallint,
    guid integer,
    owner text,
    version integer,
    synch boolean
);


ALTER TABLE new_pest OWNER TO apiis_admin;

--
-- Name: nodes; Type: TABLE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE TABLE nodes (
    nodename text,
    address text,
    last_change_dt timestamp without time zone,
    last_change_user text,
    dirty boolean,
    chk_lvl smallint,
    guid integer,
    owner text,
    version integer,
    synch boolean
);


ALTER TABLE nodes OWNER TO apiis_admin;

--
-- Name: protocols; Type: TABLE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE TABLE protocols (
    protocol_id integer,
    protocol_name text,
    db_material_type integer,
    comment text,
    chk_lvl smallint,
    dirty boolean,
    guid bigint,
    last_change_dt timestamp without time zone,
    last_change_user text,
    owner text,
    synch boolean,
    version smallint
);


ALTER TABLE protocols OWNER TO apiis_admin;

--
-- Name: seq_ar_constraints__cons_id; Type: SEQUENCE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE SEQUENCE seq_ar_constraints__cons_id
    START WITH 101
    INCREMENT BY 1
    MINVALUE 100
    MAXVALUE 100000000
    CACHE 1;


ALTER TABLE seq_ar_constraints__cons_id OWNER TO apiis_admin;

--
-- Name: seq_ar_dbtdescriptors__descriptor_id; Type: SEQUENCE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE SEQUENCE seq_ar_dbtdescriptors__descriptor_id
    START WITH 101
    INCREMENT BY 1
    MINVALUE 100
    MAXVALUE 100000000
    CACHE 1;


ALTER TABLE seq_ar_dbtdescriptors__descriptor_id OWNER TO apiis_admin;

--
-- Name: seq_ar_dbtpolicies__dbtpolicy_id; Type: SEQUENCE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE SEQUENCE seq_ar_dbtpolicies__dbtpolicy_id
    START WITH 144
    INCREMENT BY 1
    MINVALUE 100
    MAXVALUE 100000000
    CACHE 1;


ALTER TABLE seq_ar_dbtpolicies__dbtpolicy_id OWNER TO apiis_admin;

--
-- Name: seq_ar_dbttables__table_id; Type: SEQUENCE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE SEQUENCE seq_ar_dbttables__table_id
    START WITH 101
    INCREMENT BY 1
    MINVALUE 100
    MAXVALUE 100000000
    CACHE 1;


ALTER TABLE seq_ar_dbttables__table_id OWNER TO apiis_admin;

--
-- Name: seq_ar_roles__role_id; Type: SEQUENCE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE SEQUENCE seq_ar_roles__role_id
    START WITH 100
    INCREMENT BY 1
    MINVALUE 100
    MAXVALUE 100000000
    CACHE 1;


ALTER TABLE seq_ar_roles__role_id OWNER TO apiis_admin;

--
-- Name: seq_ar_stpolicies__stpolicy_id; Type: SEQUENCE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE SEQUENCE seq_ar_stpolicies__stpolicy_id
    START WITH 101
    INCREMENT BY 1
    MINVALUE 100
    MAXVALUE 100000000
    CACHE 1;


ALTER TABLE seq_ar_stpolicies__stpolicy_id OWNER TO apiis_admin;

--
-- Name: seq_ar_users__user_id; Type: SEQUENCE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE SEQUENCE seq_ar_users__user_id
    START WITH 100
    INCREMENT BY 1
    MINVALUE 100
    MAXVALUE 100000000
    CACHE 1;


ALTER TABLE seq_ar_users__user_id OWNER TO apiis_admin;

--
-- Name: seq_blobs__blob_id; Type: SEQUENCE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE SEQUENCE seq_blobs__blob_id
    START WITH 100
    INCREMENT BY 1
    MINVALUE 100
    MAXVALUE 100000000
    CACHE 1;


ALTER TABLE seq_blobs__blob_id OWNER TO apiis_admin;

--
-- Name: seq_breeds_species__breed_id; Type: SEQUENCE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE SEQUENCE seq_breeds_species__breed_id
    START WITH 100
    INCREMENT BY 1
    MINVALUE 100
    MAXVALUE 100000000
    CACHE 1;


ALTER TABLE seq_breeds_species__breed_id OWNER TO apiis_admin;

--
-- Name: seq_codes__db_code; Type: SEQUENCE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE SEQUENCE seq_codes__db_code
    START WITH 100
    INCREMENT BY 1
    MINVALUE 100
    MAXVALUE 100000000
    CACHE 1;


ALTER TABLE seq_codes__db_code OWNER TO apiis_admin;

--
-- Name: seq_contacts__db_contact; Type: SEQUENCE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE SEQUENCE seq_contacts__db_contact
    START WITH 100
    INCREMENT BY 1
    MINVALUE 100
    MAXVALUE 100000000
    CACHE 1;


ALTER TABLE seq_contacts__db_contact OWNER TO apiis_admin;

--
-- Name: seq_database__guid; Type: SEQUENCE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE SEQUENCE seq_database__guid
    START WITH 100
    INCREMENT BY 1
    MINVALUE 100
    MAXVALUE 100000000
    CACHE 1;


ALTER TABLE seq_database__guid OWNER TO apiis_admin;

--
-- Name: seq_event__event_id; Type: SEQUENCE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE SEQUENCE seq_event__event_id
    START WITH 100
    INCREMENT BY 1
    MINVALUE 100
    MAXVALUE 100000000
    CACHE 1;


ALTER TABLE seq_event__event_id OWNER TO apiis_admin;

--
-- Name: seq_inspool__record_seq; Type: SEQUENCE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE SEQUENCE seq_inspool__record_seq
    START WITH 100
    INCREMENT BY 1
    MINVALUE 100
    MAXVALUE 100000000
    CACHE 1;


ALTER TABLE seq_inspool__record_seq OWNER TO apiis_admin;

--
-- Name: seq_languages__lang_id; Type: SEQUENCE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE SEQUENCE seq_languages__lang_id
    START WITH 100
    INCREMENT BY 1
    MINVALUE 100
    MAXVALUE 100000000
    CACHE 1;


ALTER TABLE seq_languages__lang_id OWNER TO apiis_admin;

--
-- Name: seq_movements__movements_id; Type: SEQUENCE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE SEQUENCE seq_movements__movements_id
    START WITH 100
    INCREMENT BY 1
    MINVALUE 100
    MAXVALUE 100000000
    CACHE 1;


ALTER TABLE seq_movements__movements_id OWNER TO apiis_admin;

--
-- Name: seq_status_changes__status_change_id; Type: SEQUENCE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE SEQUENCE seq_status_changes__status_change_id
    START WITH 100
    INCREMENT BY 1
    MINVALUE 100
    MAXVALUE 100000000
    CACHE 1;


ALTER TABLE seq_status_changes__status_change_id OWNER TO apiis_admin;

--
-- Name: seq_storage__storage_id; Type: SEQUENCE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE SEQUENCE seq_storage__storage_id
    START WITH 100
    INCREMENT BY 1
    MINVALUE 100
    MAXVALUE 100000000
    CACHE 1;


ALTER TABLE seq_storage__storage_id OWNER TO apiis_admin;

--
-- Name: seq_transfer__db_animal; Type: SEQUENCE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE SEQUENCE seq_transfer__db_animal
    START WITH 100
    INCREMENT BY 1
    MINVALUE 100
    MAXVALUE 100000000
    CACHE 1;


ALTER TABLE seq_transfer__db_animal OWNER TO apiis_admin;

--
-- Name: seq_unit__db_unit; Type: SEQUENCE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE SEQUENCE seq_unit__db_unit
    START WITH 100
    INCREMENT BY 1
    MINVALUE 100
    MAXVALUE 100000000
    CACHE 1;


ALTER TABLE seq_unit__db_unit OWNER TO apiis_admin;

--
-- Name: seq_vessels__db_vessel; Type: SEQUENCE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE SEQUENCE seq_vessels__db_vessel
    START WITH 100
    INCREMENT BY 1
    MINVALUE 100
    MAXVALUE 100000000
    CACHE 1;


ALTER TABLE seq_vessels__db_vessel OWNER TO apiis_admin;

--
-- Name: seq_vessels_storage__vessels_storage_id; Type: SEQUENCE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE SEQUENCE seq_vessels_storage__vessels_storage_id
    START WITH 100
    INCREMENT BY 1
    MINVALUE 100
    MAXVALUE 100000000
    CACHE 1;


ALTER TABLE seq_vessels_storage__vessels_storage_id OWNER TO apiis_admin;

--
-- Name: sources; Type: TABLE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE TABLE sources (
    source text,
    tablename text,
    class text,
    columnnames text,
    last_change_dt timestamp without time zone,
    last_change_user text,
    dirty boolean,
    chk_lvl smallint,
    guid integer,
    owner text,
    version integer,
    synch boolean
);


ALTER TABLE sources OWNER TO apiis_admin;

--
-- Name: status_changes; Type: TABLE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE TABLE status_changes (
    status_change_id integer,
    vessels_storage_id integer,
    old_status integer,
    new_status integer,
    action_dt timestamp without time zone,
    comment text,
    chk_lvl smallint,
    dirty boolean,
    guid bigint,
    last_change_dt timestamp without time zone,
    last_change_user text,
    owner text,
    synch boolean,
    version smallint
);


ALTER TABLE status_changes OWNER TO apiis_admin;

--
-- Name: storage; Type: TABLE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE TABLE storage (
    storage_id integer,
    storage_name text,
    parent_id integer,
    comment text,
    chk_lvl smallint,
    dirty boolean,
    guid bigint,
    last_change_dt timestamp without time zone,
    last_change_user text,
    owner text,
    synch boolean,
    version smallint
);


ALTER TABLE storage OWNER TO apiis_admin;

--
-- Name: storage_history; Type: TABLE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE TABLE storage_history (
    storage_id integer,
    old_storage_name text,
    new_storage_name text,
    old_parent_id integer,
    new_parent_id integer,
    old_comment text,
    new_comment text,
    action_type text,
    action_date date,
    chk_lvl smallint,
    dirty boolean,
    guid bigint,
    last_change_dt timestamp without time zone,
    last_change_user text,
    owner text,
    synch boolean,
    version smallint
);


ALTER TABLE storage_history OWNER TO apiis_admin;

--
-- Name: targets; Type: TABLE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE TABLE targets (
    target text,
    tablename text,
    class text,
    columnnames text,
    last_change_dt timestamp without time zone,
    last_change_user text,
    dirty boolean,
    chk_lvl smallint,
    guid integer,
    owner text,
    version integer,
    synch boolean
);


ALTER TABLE targets OWNER TO apiis_admin;

--
-- Name: v_animal; Type: VIEW; Schema: apiis_admin; Owner: apiis_admin
--

CREATE VIEW v_animal AS
 SELECT a.guid AS v_guid,
    a.db_animal,
    ((((c.ext_unit || ':::'::text) || c.ext_id) || ':::'::text) || b.ext_animal) AS ext_animal,
    a.db_sire,
    ((((e.ext_unit || ':::'::text) || e.ext_id) || ':::'::text) || d.ext_animal) AS ext_sire,
    a.db_dam,
    ((((g.ext_unit || ':::'::text) || g.ext_id) || ':::'::text) || f.ext_animal) AS ext_dam,
    a.db_sex,
    h.ext_code AS ext_sex,
    a.db_breed,
    i.ext_code AS ext_breed,
    a.db_species,
    j.ext_code AS ext_species,
    a.birth_dt,
    a.birth_year,
    a.latitude,
    a.longitude,
    a.image_id,
    a.db_org,
    ((k.ext_unit || ':::'::text) || k.ext_id) AS ext_org,
    a.la_rep,
    a.la_rep_dt,
    a.last_change_dt,
    a.last_change_user,
    a.dirty,
    a.chk_lvl,
    a.guid,
    a.owner,
    a.version,
    a.synch,
    a.db_hybrid,
    l.ext_code AS ext_hybrid,
    a.comment
   FROM (((((((((((animal a
     LEFT JOIN transfer b ON ((a.db_animal = b.db_animal)))
     LEFT JOIN unit c ON ((b.db_unit = c.db_unit)))
     LEFT JOIN transfer d ON ((a.db_sire = d.db_animal)))
     LEFT JOIN unit e ON ((d.db_unit = e.db_unit)))
     LEFT JOIN transfer f ON ((a.db_dam = f.db_animal)))
     LEFT JOIN unit g ON ((f.db_unit = g.db_unit)))
     LEFT JOIN codes h ON ((a.db_sex = h.db_code)))
     LEFT JOIN codes i ON ((a.db_breed = i.db_code)))
     LEFT JOIN codes j ON ((a.db_species = j.db_code)))
     LEFT JOIN unit k ON ((a.db_org = k.db_unit)))
     LEFT JOIN codes l ON ((a.db_hybrid = l.db_code)));


ALTER TABLE v_animal OWNER TO apiis_admin;

--
-- Name: v_ar_constraints; Type: VIEW; Schema: apiis_admin; Owner: apiis_admin
--

CREATE VIEW v_ar_constraints AS
 SELECT a.guid AS v_guid,
    a.cons_id,
    a.cons_name,
    a.cons_type,
    a.cons_desc,
    a.last_change_dt,
    a.last_change_user,
    a.dirty,
    a.chk_lvl,
    a.guid,
    a.owner,
    a.version,
    a.synch
   FROM ar_constraints a;


ALTER TABLE v_ar_constraints OWNER TO apiis_admin;

--
-- Name: v_ar_dbtdescriptors; Type: VIEW; Schema: apiis_admin; Owner: apiis_admin
--

CREATE VIEW v_ar_dbtdescriptors AS
 SELECT a.guid AS v_guid,
    a.descriptor_id,
    a.descriptor_name,
    a.descriptor_value,
    a.descriptor_desc,
    a.last_change_dt,
    a.last_change_user,
    a.dirty,
    a.chk_lvl,
    a.guid,
    a.owner,
    a.version,
    a.synch
   FROM ar_dbtdescriptors a;


ALTER TABLE v_ar_dbtdescriptors OWNER TO apiis_admin;

--
-- Name: v_ar_dbtpolicies; Type: VIEW; Schema: apiis_admin; Owner: apiis_admin
--

CREATE VIEW v_ar_dbtpolicies AS
 SELECT a.guid AS v_guid,
    a.dbtpolicy_id,
    a.action_id,
    b.ext_code AS ext_action_id,
    a.table_id,
    a.descriptor_id,
    a.last_change_dt,
    a.last_change_user,
    a.dirty,
    a.chk_lvl,
    a.guid,
    a.owner,
    a.version,
    a.synch
   FROM (ar_dbtpolicies a
     LEFT JOIN codes b ON ((a.action_id = b.db_code)));


ALTER TABLE v_ar_dbtpolicies OWNER TO apiis_admin;

--
-- Name: v_ar_dbttables; Type: VIEW; Schema: apiis_admin; Owner: apiis_admin
--

CREATE VIEW v_ar_dbttables AS
 SELECT a.guid AS v_guid,
    a.table_id,
    a.table_name,
    a.table_columns,
    a.table_desc,
    a.last_change_dt,
    a.last_change_user,
    a.dirty,
    a.chk_lvl,
    a.guid,
    a.owner,
    a.version,
    a.synch
   FROM ar_dbttables a;


ALTER TABLE v_ar_dbttables OWNER TO apiis_admin;

--
-- Name: v_ar_role_constraints; Type: VIEW; Schema: apiis_admin; Owner: apiis_admin
--

CREATE VIEW v_ar_role_constraints AS
 SELECT a.guid AS v_guid,
    a.cons_id,
    a.first_role_id,
    a.second_role_id,
    a.last_change_dt,
    a.last_change_user,
    a.dirty,
    a.chk_lvl,
    a.guid,
    a.owner,
    a.version,
    a.synch
   FROM ar_role_constraints a;


ALTER TABLE v_ar_role_constraints OWNER TO apiis_admin;

--
-- Name: v_ar_role_dbtpolicies; Type: VIEW; Schema: apiis_admin; Owner: apiis_admin
--

CREATE VIEW v_ar_role_dbtpolicies AS
 SELECT a.guid AS v_guid,
    a.role_id,
    a.dbtpolicy_id,
    a.last_change_dt,
    a.last_change_user,
    a.dirty,
    a.chk_lvl,
    a.guid,
    a.owner,
    a.version,
    a.synch
   FROM ar_role_dbtpolicies a;


ALTER TABLE v_ar_role_dbtpolicies OWNER TO apiis_admin;

--
-- Name: v_ar_role_stpolicies; Type: VIEW; Schema: apiis_admin; Owner: apiis_admin
--

CREATE VIEW v_ar_role_stpolicies AS
 SELECT a.guid AS v_guid,
    a.role_id,
    a.stpolicy_id,
    a.last_change_dt,
    a.last_change_user,
    a.dirty,
    a.chk_lvl,
    a.guid,
    a.owner,
    a.version,
    a.synch
   FROM ar_role_stpolicies a;


ALTER TABLE v_ar_role_stpolicies OWNER TO apiis_admin;

--
-- Name: v_ar_roles; Type: VIEW; Schema: apiis_admin; Owner: apiis_admin
--

CREATE VIEW v_ar_roles AS
 SELECT a.guid AS v_guid,
    a.role_id,
    a.role_name,
    a.role_long_name,
    a.role_type,
    a.role_subset,
    a.role_descr,
    a.last_change_dt,
    a.last_change_user,
    a.dirty,
    a.chk_lvl,
    a.guid,
    a.owner,
    a.version,
    a.synch
   FROM ar_roles a;


ALTER TABLE v_ar_roles OWNER TO apiis_admin;

--
-- Name: v_ar_stpolicies; Type: VIEW; Schema: apiis_admin; Owner: apiis_admin
--

CREATE VIEW v_ar_stpolicies AS
 SELECT a.guid AS v_guid,
    a.stpolicy_id,
    a.stpolicy_name,
    a.stpolicy_type,
    a.stpolicy_desc,
    a.last_change_dt,
    a.last_change_user,
    a.dirty,
    a.chk_lvl,
    a.guid,
    a.owner,
    a.version,
    a.synch
   FROM ar_stpolicies a;


ALTER TABLE v_ar_stpolicies OWNER TO apiis_admin;

--
-- Name: v_ar_user_roles; Type: VIEW; Schema: apiis_admin; Owner: apiis_admin
--

CREATE VIEW v_ar_user_roles AS
 SELECT a.guid AS v_guid,
    a.user_id,
    a.role_id,
    a.last_change_dt,
    a.last_change_user,
    a.dirty,
    a.chk_lvl,
    a.guid,
    a.owner,
    a.version,
    a.synch
   FROM ar_user_roles a;


ALTER TABLE v_ar_user_roles OWNER TO apiis_admin;

--
-- Name: v_ar_users; Type: VIEW; Schema: apiis_admin; Owner: apiis_admin
--

CREATE VIEW v_ar_users AS
 SELECT a.guid AS v_guid,
    a.user_id,
    a.user_login,
    a.user_password,
    a.user_language_id,
    a.user_marker,
    a.user_disabled,
    a.user_status,
    a.user_last_login,
    a.user_last_activ_time,
    a.user_session_id,
    a.last_change_dt,
    a.last_change_user,
    a.dirty,
    a.chk_lvl,
    a.guid,
    a.owner,
    a.version,
    a.synch
   FROM ar_users a;


ALTER TABLE v_ar_users OWNER TO apiis_admin;

--
-- Name: v_ar_users_data; Type: VIEW; Schema: apiis_admin; Owner: apiis_admin
--

CREATE VIEW v_ar_users_data AS
 SELECT a.guid AS v_guid,
    a.user_id,
    a.user_first_name,
    a.user_second_name,
    a.user_institution,
    a.user_email,
    a.user_country,
    a.user_street,
    a.user_town,
    a.user_zip,
    a.user_other_info,
    a.opening_dt,
    a.closing_dt,
    a.last_change_dt,
    a.last_change_user,
    a.creation_dt,
    a.creation_user,
    a.end_dt,
    a.end_user,
    a.dirty,
    a.chk_lvl,
    a.guid,
    a.owner,
    a.version,
    a.synch
   FROM ar_users_data a;


ALTER TABLE v_ar_users_data OWNER TO apiis_admin;

--
-- Name: v_blobs; Type: VIEW; Schema: apiis_admin; Owner: apiis_admin
--

CREATE VIEW v_blobs AS
 SELECT a.guid AS v_guid,
    a.blob_id,
    a.blob,
    a.last_change_dt,
    a.last_change_user,
    a.dirty,
    a.chk_lvl,
    a.guid,
    a.owner,
    a.version,
    a.synch,
    a.db_mimetype,
    b.ext_code AS ext_mimetype
   FROM (blobs a
     LEFT JOIN codes b ON ((a.db_mimetype = b.db_code)));


ALTER TABLE v_blobs OWNER TO apiis_admin;

--
-- Name: v_breeds_species; Type: VIEW; Schema: apiis_admin; Owner: apiis_admin
--

CREATE VIEW v_breeds_species AS
 SELECT a.guid AS v_guid,
    a.breed_id,
    a.db_breed,
    b.ext_code AS ext_breed,
    a.db_species,
    c.ext_code AS ext_species,
    a.efabis_mcname,
    a.efabis_species,
    a.efabis_country,
    a.efabis_lang,
    a.chk_lvl,
    a.dirty,
    a.guid,
    a.last_change_dt,
    a.last_change_user,
    a.owner,
    a.synch,
    a.version
   FROM ((breeds_species a
     LEFT JOIN codes b ON ((a.db_breed = b.db_code)))
     LEFT JOIN codes c ON ((a.db_species = c.db_code)));


ALTER TABLE v_breeds_species OWNER TO apiis_admin;

--
-- Name: v_codes; Type: VIEW; Schema: apiis_admin; Owner: apiis_admin
--

CREATE VIEW v_codes AS
 SELECT a.guid AS v_guid,
    a.ext_code,
    a.class,
    a.db_code,
    a.short_name,
    a.long_name,
    a.description,
    a.opening_dt,
    a.closing_dt,
    a.last_change_dt,
    a.last_change_user,
    a.dirty,
    a.chk_lvl,
    a.guid,
    a.owner,
    a.version,
    a.synch
   FROM codes a;


ALTER TABLE v_codes OWNER TO apiis_admin;

--
-- Name: v_contacts; Type: VIEW; Schema: apiis_admin; Owner: apiis_admin
--

CREATE VIEW v_contacts AS
 SELECT a.guid AS v_guid,
    a.db_contact,
    a.title,
    a.salutation,
    a.first_name,
    a.second_name,
    a.third_name,
    a.birth_dt,
    a.db_language,
    a.street,
    a.zip,
    a.town,
    a.db_country,
    b.ext_code AS ext_country,
    a.label,
    a.phone,
    a.phone2,
    a.fax,
    a.email,
    a.bank_name,
    a.bank_zip,
    a.account,
    a.comment,
    a.opening_dt,
    a.closing_dt,
    a.chk_lvl,
    a.dirty,
    a.guid,
    a.last_change_dt,
    a.last_change_user,
    a.owner,
    a.synch,
    a.version
   FROM (contacts a
     LEFT JOIN codes b ON ((a.db_country = b.db_code)));


ALTER TABLE v_contacts OWNER TO apiis_admin;

--
-- Name: v_event; Type: VIEW; Schema: apiis_admin; Owner: apiis_admin
--

CREATE VIEW v_event AS
 SELECT a.guid AS v_guid,
    a.event_id,
    a.db_event_type,
    b.ext_code AS ext_event_type,
    a.db_sampler,
    ((c.ext_unit || ':::'::text) || c.ext_id) AS ext_sampler,
    a.event_dt,
    a.db_location,
    ((d.ext_unit || ':::'::text) || d.ext_id) AS ext_location,
    a.last_change_dt,
    a.last_change_user,
    a.dirty,
    a.chk_lvl,
    a.guid,
    a.owner,
    a.version,
    a.synch
   FROM (((event a
     LEFT JOIN codes b ON ((a.db_event_type = b.db_code)))
     LEFT JOIN unit c ON ((a.db_sampler = c.db_unit)))
     LEFT JOIN unit d ON ((a.db_location = d.db_unit)));


ALTER TABLE v_event OWNER TO apiis_admin;

--
-- Name: v_inspool; Type: VIEW; Schema: apiis_admin; Owner: apiis_admin
--

CREATE VIEW v_inspool AS
 SELECT a.guid AS v_guid,
    a.ds,
    a.record_seq,
    a.in_date,
    a.ext_unit,
    a.proc_dt,
    a.status,
    a.record,
    a.last_change_dt,
    a.last_change_user,
    a.dirty,
    a.chk_lvl,
    a.guid,
    a.owner,
    a.version,
    a.synch
   FROM inspool a;


ALTER TABLE v_inspool OWNER TO apiis_admin;

--
-- Name: v_inspool_err; Type: VIEW; Schema: apiis_admin; Owner: apiis_admin
--

CREATE VIEW v_inspool_err AS
 SELECT a.guid AS v_guid,
    a.record_seq,
    a.err_type,
    a.action,
    a.dbtable,
    a.dbcol,
    a.err_source,
    a.short_msg,
    a.long_msg,
    a.ext_col,
    a.ext_val,
    a.mod_val,
    a.comp_val,
    a.target_col,
    a.ds,
    a.ext_unit,
    a.status,
    a.err_dt,
    a.last_change_dt,
    a.last_change_user,
    a.dirty,
    a.chk_lvl,
    a.guid,
    a.owner,
    a.version,
    a.synch
   FROM inspool_err a;


ALTER TABLE v_inspool_err OWNER TO apiis_admin;

--
-- Name: v_languages; Type: VIEW; Schema: apiis_admin; Owner: apiis_admin
--

CREATE VIEW v_languages AS
 SELECT a.guid AS v_guid,
    a.lang_id,
    a.iso_lang,
    a.lang,
    a.last_change_dt,
    a.last_change_user,
    a.creation_dt,
    a.creation_user,
    a.end_dt,
    a.end_user,
    a.dirty,
    a.chk_lvl,
    a.guid,
    a.owner,
    a.version,
    a.synch
   FROM languages a;


ALTER TABLE v_languages OWNER TO apiis_admin;

--
-- Name: v_load_stat; Type: VIEW; Schema: apiis_admin; Owner: apiis_admin
--

CREATE VIEW v_load_stat AS
 SELECT a.guid AS v_guid,
    a.ds,
    a.job_start,
    a.job_end,
    a.status,
    a.rec_tot_no,
    a.rec_err_no,
    a.rec_ok_no,
    a.last_change_dt,
    a.last_change_user,
    a.dirty,
    a.chk_lvl,
    a.guid,
    a.owner,
    a.version,
    a.synch
   FROM load_stat a;


ALTER TABLE v_load_stat OWNER TO apiis_admin;

--
-- Name: v_locations; Type: VIEW; Schema: apiis_admin; Owner: apiis_admin
--

CREATE VIEW v_locations AS
 SELECT a.guid AS v_guid,
    a.db_animal,
    ((((c.ext_unit || ':::'::text) || c.ext_id) || ':::'::text) || b.ext_animal) AS ext_animal,
    a.db_location,
    ((d.ext_unit || ':::'::text) || d.ext_id) AS ext_location,
    a.entry_dt,
    a.db_entry_action,
    e.ext_code AS ext_entry_action,
    a.exit_dt,
    a.db_exit_action,
    f.ext_code AS ext_exit_action,
    a.chk_lvl,
    a.dirty,
    a.guid,
    a.last_change_dt,
    a.last_change_user,
    a.owner,
    a.synch,
    a.version
   FROM (((((locations a
     LEFT JOIN transfer b ON ((a.db_animal = b.db_animal)))
     LEFT JOIN unit c ON ((b.db_unit = c.db_unit)))
     LEFT JOIN unit d ON ((a.db_location = d.db_unit)))
     LEFT JOIN codes e ON ((a.db_entry_action = e.db_code)))
     LEFT JOIN codes f ON ((a.db_exit_action = f.db_code)));


ALTER TABLE v_locations OWNER TO apiis_admin;

--
-- Name: v_movements; Type: VIEW; Schema: apiis_admin; Owner: apiis_admin
--

CREATE VIEW v_movements AS
 SELECT a.guid AS v_guid,
    a.movements_id,
    a.from_storage,
    a.to_storage,
    a.no_units,
    a.comment,
    a.action_dt,
    a.action_type,
    a.chk_lvl,
    a.dirty,
    a.guid,
    a.last_change_dt,
    a.last_change_user,
    a.owner,
    a.synch,
    a.version
   FROM movements a;


ALTER TABLE v_movements OWNER TO apiis_admin;

--
-- Name: v_new_pest; Type: VIEW; Schema: apiis_admin; Owner: apiis_admin
--

CREATE VIEW v_new_pest AS
 SELECT a.guid AS v_guid,
    a.class,
    a.key,
    a.trait,
    a.estimator,
    a.pev,
    a.last_change_dt,
    a.last_change_user,
    a.dirty,
    a.chk_lvl,
    a.guid,
    a.owner,
    a.version,
    a.synch
   FROM new_pest a;


ALTER TABLE v_new_pest OWNER TO apiis_admin;

--
-- Name: v_nodes; Type: VIEW; Schema: apiis_admin; Owner: apiis_admin
--

CREATE VIEW v_nodes AS
 SELECT a.guid AS v_guid,
    a.nodename,
    a.address,
    a.last_change_dt,
    a.last_change_user,
    a.dirty,
    a.chk_lvl,
    a.guid,
    a.owner,
    a.version,
    a.synch
   FROM nodes a;


ALTER TABLE v_nodes OWNER TO apiis_admin;

--
-- Name: v_protocols; Type: VIEW; Schema: apiis_admin; Owner: apiis_admin
--

CREATE VIEW v_protocols AS
 SELECT a.guid AS v_guid,
    a.protocol_id,
    a.protocol_name,
    a.db_material_type,
    b.ext_code AS ext_material_type,
    a.comment,
    a.chk_lvl,
    a.dirty,
    a.guid,
    a.last_change_dt,
    a.last_change_user,
    a.owner,
    a.synch,
    a.version
   FROM (protocols a
     LEFT JOIN codes b ON ((a.db_material_type = b.db_code)));


ALTER TABLE v_protocols OWNER TO apiis_admin;

--
-- Name: v_sources; Type: VIEW; Schema: apiis_admin; Owner: apiis_admin
--

CREATE VIEW v_sources AS
 SELECT a.guid AS v_guid,
    a.source,
    a.tablename,
    a.class,
    a.columnnames,
    a.last_change_dt,
    a.last_change_user,
    a.dirty,
    a.chk_lvl,
    a.guid,
    a.owner,
    a.version,
    a.synch
   FROM sources a;


ALTER TABLE v_sources OWNER TO apiis_admin;

--
-- Name: v_status_changes; Type: VIEW; Schema: apiis_admin; Owner: apiis_admin
--

CREATE VIEW v_status_changes AS
 SELECT a.guid AS v_guid,
    a.status_change_id,
    a.vessels_storage_id,
    a.old_status,
    b.ext_code AS ext_old_status,
    a.new_status,
    c.ext_code AS ext_new_status,
    a.action_dt,
    a.comment,
    a.chk_lvl,
    a.dirty,
    a.guid,
    a.last_change_dt,
    a.last_change_user,
    a.owner,
    a.synch,
    a.version
   FROM ((status_changes a
     LEFT JOIN codes b ON ((a.old_status = b.db_code)))
     LEFT JOIN codes c ON ((a.new_status = c.db_code)));


ALTER TABLE v_status_changes OWNER TO apiis_admin;

--
-- Name: v_storage; Type: VIEW; Schema: apiis_admin; Owner: apiis_admin
--

CREATE VIEW v_storage AS
 SELECT a.guid AS v_guid,
    a.storage_id,
    a.storage_name,
    a.parent_id,
    a.comment,
    a.chk_lvl,
    a.dirty,
    a.guid,
    a.last_change_dt,
    a.last_change_user,
    a.owner,
    a.synch,
    a.version
   FROM storage a;


ALTER TABLE v_storage OWNER TO apiis_admin;

--
-- Name: v_storage_history; Type: VIEW; Schema: apiis_admin; Owner: apiis_admin
--

CREATE VIEW v_storage_history AS
 SELECT a.guid AS v_guid,
    a.storage_id,
    a.old_storage_name,
    a.new_storage_name,
    a.old_parent_id,
    a.new_parent_id,
    a.old_comment,
    a.new_comment,
    a.action_type,
    a.action_date,
    a.chk_lvl,
    a.dirty,
    a.guid,
    a.last_change_dt,
    a.last_change_user,
    a.owner,
    a.synch,
    a.version
   FROM storage_history a;


ALTER TABLE v_storage_history OWNER TO apiis_admin;

--
-- Name: v_targets; Type: VIEW; Schema: apiis_admin; Owner: apiis_admin
--

CREATE VIEW v_targets AS
 SELECT a.guid AS v_guid,
    a.target,
    a.tablename,
    a.class,
    a.columnnames,
    a.last_change_dt,
    a.last_change_user,
    a.dirty,
    a.chk_lvl,
    a.guid,
    a.owner,
    a.version,
    a.synch
   FROM targets a;


ALTER TABLE v_targets OWNER TO apiis_admin;

--
-- Name: v_transfer; Type: VIEW; Schema: apiis_admin; Owner: apiis_admin
--

CREATE VIEW v_transfer AS
 SELECT a.guid AS v_guid,
    a.db_animal,
    a.ext_animal,
    a.db_unit,
    ((b.ext_unit || ':::'::text) || b.ext_id) AS ext_unit,
    a.id_set,
    c.ext_code AS ext_id_set,
    a.opening_dt,
    a.closing_dt,
    a.last_change_dt,
    a.last_change_user,
    a.dirty,
    a.chk_lvl,
    a.guid,
    a.owner,
    a.version,
    a.synch
   FROM ((transfer a
     LEFT JOIN unit b ON ((a.db_unit = b.db_unit)))
     LEFT JOIN codes c ON ((a.id_set = c.db_code)));


ALTER TABLE v_transfer OWNER TO apiis_admin;

--
-- Name: v_unit; Type: VIEW; Schema: apiis_admin; Owner: apiis_admin
--

CREATE VIEW v_unit AS
 SELECT a.guid AS v_guid,
    a.db_unit,
    a.ext_unit,
    a.ext_id,
    a.db_contact,
    a.db_member,
    ((b.ext_unit || ':::'::text) || b.ext_id) AS ext_member,
    b.opening_dt,
    b.closing_dt,
    b.last_change_dt,
    b.last_change_user,
    b.dirty,
    b.chk_lvl,
    b.guid,
    b.owner,
    b.version,
    b.synch
   FROM (unit a
     LEFT JOIN unit b ON ((b.db_member = b.db_unit)));


ALTER TABLE v_unit OWNER TO apiis_admin;

--
-- Name: vessels; Type: TABLE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE TABLE vessels (
    db_vessel integer,
    ext_vessel text,
    db_animal integer,
    protocol_id integer,
    production_dt date,
    freezing_dt date,
    db_vessel_type integer,
    comment text,
    chk_lvl smallint,
    dirty boolean,
    guid bigint,
    last_change_dt timestamp without time zone,
    last_change_user text,
    owner text,
    synch boolean,
    version smallint,
    db_contributor integer
);


ALTER TABLE vessels OWNER TO apiis_admin;

--
-- Name: v_vessels; Type: VIEW; Schema: apiis_admin; Owner: apiis_admin
--

CREATE VIEW v_vessels AS
 SELECT a.guid AS v_guid,
    a.db_vessel,
    a.ext_vessel,
    a.db_animal,
    ((((c.ext_unit || ':::'::text) || c.ext_id) || ':::'::text) || b.ext_animal) AS ext_animal,
    a.protocol_id,
    d.protocol_id AS ext_protocol_id,
    a.production_dt,
    a.freezing_dt,
    a.db_vessel_type,
    e.ext_code AS ext_vessel_type,
    a.comment,
    a.chk_lvl,
    a.dirty,
    a.guid,
    a.last_change_dt,
    a.last_change_user,
    a.owner,
    a.synch,
    a.version
   FROM ((((vessels a
     LEFT JOIN transfer b ON ((a.db_animal = b.db_animal)))
     LEFT JOIN unit c ON ((b.db_unit = c.db_unit)))
     LEFT JOIN protocols d ON ((a.protocol_id = d.protocol_id)))
     LEFT JOIN codes e ON ((a.db_vessel_type = e.db_code)));


ALTER TABLE v_vessels OWNER TO apiis_admin;

--
-- Name: vessels_storage; Type: TABLE; Schema: apiis_admin; Owner: apiis_admin
--

CREATE TABLE vessels_storage (
    vessels_storage_id integer,
    db_vessel integer,
    storage_id integer,
    no_units smallint,
    db_status integer,
    comment text,
    chk_lvl smallint,
    dirty boolean,
    guid bigint,
    last_change_dt timestamp without time zone,
    last_change_user text,
    owner text,
    synch boolean,
    version smallint
);


ALTER TABLE vessels_storage OWNER TO apiis_admin;

--
-- Name: v_vessels_storage; Type: VIEW; Schema: apiis_admin; Owner: apiis_admin
--

CREATE VIEW v_vessels_storage AS
 SELECT a.guid AS v_guid,
    a.vessels_storage_id,
    a.db_vessel,
    a.storage_id,
    a.no_units,
    a.db_status,
    b.ext_code AS ext_status,
    a.comment,
    a.chk_lvl,
    a.dirty,
    a.guid,
    a.last_change_dt,
    a.last_change_user,
    a.owner,
    a.synch,
    a.version
   FROM (vessels_storage a
     LEFT JOIN codes b ON ((a.db_status = b.db_code)));


ALTER TABLE v_vessels_storage OWNER TO apiis_admin;

--
-- Name: idx_inspool_err_1; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE INDEX idx_inspool_err_1 ON inspool_err USING btree (record_seq);


--
-- Name: idx_transfer_1; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE INDEX idx_transfer_1 ON transfer USING btree (db_animal);


--
-- Name: idx_transfer_2; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE INDEX idx_transfer_2 ON transfer USING btree (ext_animal, db_unit);


--
-- Name: uidx_animal_1; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_animal_1 ON animal USING btree (db_animal);


--
-- Name: uidx_animal_rowid; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_animal_rowid ON animal USING btree (guid);


--
-- Name: uidx_ar_constraints_1; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_ar_constraints_1 ON ar_constraints USING btree (cons_id);


--
-- Name: uidx_ar_constraints_2; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_ar_constraints_2 ON ar_constraints USING btree (cons_name, cons_type);


--
-- Name: uidx_ar_constraints_3; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_ar_constraints_3 ON ar_constraints USING btree (guid);


--
-- Name: uidx_ar_constraints_rowid; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_ar_constraints_rowid ON ar_constraints USING btree (guid);


--
-- Name: uidx_ar_dbtdescriptors_1; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_ar_dbtdescriptors_1 ON ar_dbtdescriptors USING btree (descriptor_id);


--
-- Name: uidx_ar_dbtdescriptors_2; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_ar_dbtdescriptors_2 ON ar_dbtdescriptors USING btree (descriptor_name, descriptor_value);


--
-- Name: uidx_ar_dbtdescriptors_3; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_ar_dbtdescriptors_3 ON ar_dbtdescriptors USING btree (guid);


--
-- Name: uidx_ar_dbtdescriptors_rowid; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_ar_dbtdescriptors_rowid ON ar_dbtdescriptors USING btree (guid);


--
-- Name: uidx_ar_dbtpolicies_1; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_ar_dbtpolicies_1 ON ar_dbtpolicies USING btree (dbtpolicy_id);


--
-- Name: uidx_ar_dbtpolicies_2; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_ar_dbtpolicies_2 ON ar_dbtpolicies USING btree (action_id, table_id, descriptor_id);


--
-- Name: uidx_ar_dbtpolicies_3; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_ar_dbtpolicies_3 ON ar_dbtpolicies USING btree (guid);


--
-- Name: uidx_ar_dbtpolicies_rowid; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_ar_dbtpolicies_rowid ON ar_dbtpolicies USING btree (guid);


--
-- Name: uidx_ar_dbttables_1; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_ar_dbttables_1 ON ar_dbttables USING btree (table_id);


--
-- Name: uidx_ar_dbttables_2; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_ar_dbttables_2 ON ar_dbttables USING btree (table_name, table_columns);


--
-- Name: uidx_ar_dbttables_3; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_ar_dbttables_3 ON ar_dbttables USING btree (guid);


--
-- Name: uidx_ar_dbttables_rowid; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_ar_dbttables_rowid ON ar_dbttables USING btree (guid);


--
-- Name: uidx_ar_role_constraints_1; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_ar_role_constraints_1 ON ar_role_constraints USING btree (cons_id, first_role_id, second_role_id);


--
-- Name: uidx_ar_role_constraints_2; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_ar_role_constraints_2 ON ar_role_constraints USING btree (guid);


--
-- Name: uidx_ar_role_constraints_rowid; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_ar_role_constraints_rowid ON ar_role_constraints USING btree (guid);


--
-- Name: uidx_ar_role_dbtpolicies_1; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_ar_role_dbtpolicies_1 ON ar_role_dbtpolicies USING btree (role_id, dbtpolicy_id);


--
-- Name: uidx_ar_role_dbtpolicies_2; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_ar_role_dbtpolicies_2 ON ar_role_dbtpolicies USING btree (guid);


--
-- Name: uidx_ar_role_dbtpolicies_rowid; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_ar_role_dbtpolicies_rowid ON ar_role_dbtpolicies USING btree (guid);


--
-- Name: uidx_ar_role_stpolicies_1; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_ar_role_stpolicies_1 ON ar_role_stpolicies USING btree (role_id, stpolicy_id);


--
-- Name: uidx_ar_role_stpolicies_2; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_ar_role_stpolicies_2 ON ar_role_stpolicies USING btree (guid);


--
-- Name: uidx_ar_role_stpolicies_rowid; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_ar_role_stpolicies_rowid ON ar_role_stpolicies USING btree (guid);


--
-- Name: uidx_ar_roles_1; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_ar_roles_1 ON ar_roles USING btree (role_id);


--
-- Name: uidx_ar_roles_2; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_ar_roles_2 ON ar_roles USING btree (role_name, role_type);


--
-- Name: uidx_ar_roles_3; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_ar_roles_3 ON ar_roles USING btree (guid);


--
-- Name: uidx_ar_roles_rowid; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_ar_roles_rowid ON ar_roles USING btree (guid);


--
-- Name: uidx_ar_stpolicies_1; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_ar_stpolicies_1 ON ar_stpolicies USING btree (stpolicy_id);


--
-- Name: uidx_ar_stpolicies_2; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_ar_stpolicies_2 ON ar_stpolicies USING btree (stpolicy_name, stpolicy_type);


--
-- Name: uidx_ar_stpolicies_3; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_ar_stpolicies_3 ON ar_stpolicies USING btree (guid);


--
-- Name: uidx_ar_stpolicies_rowid; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_ar_stpolicies_rowid ON ar_stpolicies USING btree (guid);


--
-- Name: uidx_ar_user_roles_1; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_ar_user_roles_1 ON ar_user_roles USING btree (user_id, role_id);


--
-- Name: uidx_ar_user_roles_2; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_ar_user_roles_2 ON ar_user_roles USING btree (guid);


--
-- Name: uidx_ar_user_roles_rowid; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_ar_user_roles_rowid ON ar_user_roles USING btree (guid);


--
-- Name: uidx_ar_users_1; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_ar_users_1 ON ar_users USING btree (user_id);


--
-- Name: uidx_ar_users_2; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_ar_users_2 ON ar_users USING btree (user_login);


--
-- Name: uidx_ar_users_3; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_ar_users_3 ON ar_users USING btree (guid);


--
-- Name: uidx_ar_users_data_1; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_ar_users_data_1 ON ar_users_data USING btree (user_id);


--
-- Name: uidx_ar_users_data_2; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_ar_users_data_2 ON ar_users_data USING btree (guid);


--
-- Name: uidx_ar_users_data_rowid; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_ar_users_data_rowid ON ar_users_data USING btree (guid);


--
-- Name: uidx_ar_users_rowid; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_ar_users_rowid ON ar_users USING btree (guid);


--
-- Name: uidx_blobs_rowid; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_blobs_rowid ON blobs USING btree (guid);


--
-- Name: uidx_breeds_species_1; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_breeds_species_1 ON breeds_species USING btree (breed_id);


--
-- Name: uidx_breeds_species_2; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_breeds_species_2 ON breeds_species USING btree (db_species, db_breed);


--
-- Name: uidx_breeds_species_rowid; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_breeds_species_rowid ON breeds_species USING btree (guid);


--
-- Name: uidx_codes_1; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_codes_1 ON codes USING btree (db_code);


--
-- Name: uidx_codes_2; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_codes_2 ON codes USING btree (class, ext_code, closing_dt);


--
-- Name: uidx_codes_rowid; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_codes_rowid ON codes USING btree (guid);


--
-- Name: uidx_contacts_1; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_contacts_1 ON contacts USING btree (db_contact);


--
-- Name: uidx_contacts_rowid; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_contacts_rowid ON contacts USING btree (guid);


--
-- Name: uidx_event_1; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_event_1 ON event USING btree (event_id, db_event_type, db_location, event_dt);


--
-- Name: uidx_event_rowid; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_event_rowid ON event USING btree (guid);


--
-- Name: uidx_inspool_1; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_inspool_1 ON inspool USING btree (record_seq);


--
-- Name: uidx_inspool_err_rowid; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_inspool_err_rowid ON inspool_err USING btree (guid);


--
-- Name: uidx_inspool_rowid; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_inspool_rowid ON inspool USING btree (guid);


--
-- Name: uidx_languages_1; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_languages_1 ON languages USING btree (lang_id);


--
-- Name: uidx_languages_2; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_languages_2 ON languages USING btree (iso_lang);


--
-- Name: uidx_languages_3; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_languages_3 ON languages USING btree (guid);


--
-- Name: uidx_languages_rowid; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_languages_rowid ON languages USING btree (guid);


--
-- Name: uidx_load_stat_rowid; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_load_stat_rowid ON load_stat USING btree (guid);


--
-- Name: uidx_locations_rowid; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_locations_rowid ON locations USING btree (guid);


--
-- Name: uidx_movements_1; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_movements_1 ON movements USING btree (movements_id);


--
-- Name: uidx_movements_rowid; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_movements_rowid ON movements USING btree (guid);


--
-- Name: uidx_new_pest_1; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_new_pest_1 ON new_pest USING btree (class, key, trait);


--
-- Name: uidx_new_pest_rowid; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_new_pest_rowid ON new_pest USING btree (guid);


--
-- Name: uidx_nodes_1; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_nodes_1 ON nodes USING btree (guid);


--
-- Name: uidx_nodes_rowid; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_nodes_rowid ON nodes USING btree (guid);


--
-- Name: uidx_pk_codes; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_pk_codes ON codes USING btree (class, ext_code) WHERE (closing_dt IS NULL);


--
-- Name: uidx_pk_transfer; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_pk_transfer ON transfer USING btree (db_unit, ext_animal) WHERE (closing_dt IS NULL);


--
-- Name: uidx_pk_unit; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_pk_unit ON unit USING btree (ext_unit, ext_id) WHERE (closing_dt IS NULL);


--
-- Name: uidx_protocols_rowid; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_protocols_rowid ON protocols USING btree (guid);


--
-- Name: uidx_sources_1; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_sources_1 ON sources USING btree (guid);


--
-- Name: uidx_sources_rowid; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_sources_rowid ON sources USING btree (guid);


--
-- Name: uidx_status_changes_rowid; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_status_changes_rowid ON status_changes USING btree (guid);


--
-- Name: uidx_storage_1; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_storage_1 ON storage USING btree (storage_id);


--
-- Name: uidx_storage_history_rowid; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_storage_history_rowid ON storage_history USING btree (guid);


--
-- Name: uidx_storage_rowid; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_storage_rowid ON storage USING btree (guid);


--
-- Name: uidx_targets_1; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_targets_1 ON targets USING btree (guid);


--
-- Name: uidx_targets_rowid; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_targets_rowid ON targets USING btree (guid);


--
-- Name: uidx_transfer_rowid; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_transfer_rowid ON transfer USING btree (guid);


--
-- Name: uidx_unit_1; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_unit_1 ON unit USING btree (db_unit);


--
-- Name: uidx_unit_2; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_unit_2 ON unit USING btree (ext_unit, ext_id, closing_dt);


--
-- Name: uidx_unit_rowid; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_unit_rowid ON unit USING btree (guid);


--
-- Name: uidx_vessels_1; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_vessels_1 ON vessels USING btree (db_vessel);


--
-- Name: uidx_vessels_2; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_vessels_2 ON vessels USING btree (ext_vessel);


--
-- Name: uidx_vessels_rowid; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_vessels_rowid ON vessels USING btree (guid);


--
-- Name: uidx_vessels_storage_1; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_vessels_storage_1 ON vessels_storage USING btree (db_vessel, storage_id, db_status);


--
-- Name: uidx_vessels_storage_rowid; Type: INDEX; Schema: apiis_admin; Owner: apiis_admin
--

CREATE UNIQUE INDEX uidx_vessels_storage_rowid ON vessels_storage USING btree (guid);


--
-- PostgreSQL database dump complete
--
