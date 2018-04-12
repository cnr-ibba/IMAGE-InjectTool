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

SET search_path = apiis_admin, pg_catalog;

--
-- Data for Name: animal; Type: TABLE DATA; Schema: apiis_admin; Owner: apiis_admin
--

INSERT INTO animal (db_animal, db_sire, db_dam, db_sex, db_breed, db_species, birth_dt, birth_year, latitude, longitude, image_id, db_org, la_rep, la_rep_dt, last_change_dt, last_change_user, dirty, chk_lvl, guid, owner, version, synch, db_hybrid, comment, file_id) VALUES (438, 1, 2, 118, 317, 313, NULL, NULL, NULL, NULL, NULL, 112, NULL, NULL, '2007-06-14 14:54:36', 'jmoos', NULL, NULL, 1959, 'Germany', 1, NULL, NULL, NULL, NULL);
INSERT INTO animal (db_animal, db_sire, db_dam, db_sex, db_breed, db_species, birth_dt, birth_year, latitude, longitude, image_id, db_org, la_rep, la_rep_dt, last_change_dt, last_change_user, dirty, chk_lvl, guid, owner, version, synch, db_hybrid, comment, file_id) VALUES (439, 1, 2, 117, 317, 313, NULL, NULL, NULL, NULL, NULL, 112, NULL, NULL, '2007-06-14 14:55:05', 'jmoos', NULL, NULL, 1961, 'Germany', 1, NULL, NULL, NULL, NULL);
INSERT INTO animal (db_animal, db_sire, db_dam, db_sex, db_breed, db_species, birth_dt, birth_year, latitude, longitude, image_id, db_org, la_rep, la_rep_dt, last_change_dt, last_change_user, dirty, chk_lvl, guid, owner, version, synch, db_hybrid, comment, file_id) VALUES (440, 438, 439, 118, 317, 313, '2003-01-16', NULL, 52.0345050000000029, 8.9396640000000005, NULL, 112, NULL, NULL, '2008-01-16 16:18:14', 'jmoos', NULL, NULL, 1963, 'Germany', 2, NULL, NULL, NULL, NULL);


--
-- Data for Name: breeds_species; Type: TABLE DATA; Schema: apiis_admin; Owner: apiis_admin
--

INSERT INTO breeds_species (breed_id, db_breed, db_species, efabis_mcname, efabis_species, efabis_country, efabis_lang, chk_lvl, dirty, guid, last_change_dt, last_change_user, owner, synch, version) VALUES (328, 317, 313, 'Ostfriesisches Milchschaf', 'Sheep', 'Germany', 'en', NULL, NULL, 7945, '2008-12-15 10:57:00', 'manager', 'Germany', NULL, 1);
INSERT INTO breeds_species (breed_id, db_breed, db_species, efabis_mcname, efabis_species, efabis_country, efabis_lang, chk_lvl, dirty, guid, last_change_dt, last_change_user, owner, synch, version) VALUES (100, 358, 341, 'Aberdeen Angus', 'Cattle', 'Germany', 'en', NULL, NULL, 7500, '2008-12-08 11:49:16', 'manager', 'Germany', NULL, 2);


--
-- Data for Name: codes; Type: TABLE DATA; Schema: apiis_admin; Owner: apiis_admin
--

INSERT INTO codes (ext_code, class, db_code, short_name, long_name, description, opening_dt, closing_dt, last_change_dt, last_change_user, dirty, chk_lvl, guid, owner, version, synch) VALUES ('Straw 0.25', 'VESSEL_TYPE', 108, 'Straw 0.25', 'Straw 0.25', 'Mini Pailletten 0.25 ml', '2007-04-26', NULL, '2007-04-26 15:25:09', 'jmoos', NULL, NULL, 486, 'Germany', 2, NULL);
INSERT INTO codes (ext_code, class, db_code, short_name, long_name, description, opening_dt, closing_dt, last_change_dt, last_change_user, dirty, chk_lvl, guid, owner, version, synch) VALUES ('deutsch', 'LANGUAGE', 109, 'deutsch', 'deutsch', NULL, '2007-10-31', NULL, '2007-10-31 12:02:42', 'jmoos', NULL, NULL, 487, 'Germany', 3, NULL);
INSERT INTO codes (ext_code, class, db_code, short_name, long_name, description, opening_dt, closing_dt, last_change_dt, last_change_user, dirty, chk_lvl, guid, owner, version, synch) VALUES ('core', 'AVAILABILITY', 119, 'Kern', 'Kern', 'Material dieser Klasse gehört zum Kernbestand der Genbank und sollte nicht entnommen werden.', '2007-04-26', NULL, '2008-12-08 10:48:42', 'manager', NULL, NULL, 497, 'Germany', 11, NULL);
INSERT INTO codes (ext_code, class, db_code, short_name, long_name, description, opening_dt, closing_dt, last_change_dt, last_change_user, dirty, chk_lvl, guid, owner, version, synch) VALUES ('free', 'AVAILABILITY', 311, 'Frei', 'Frei', 'Material dieser Klasse gehört nicht zum Kernbestand der Genbank und kann deshalb entnommen werden.', '2007-04-26', NULL, '2008-12-08 10:49:28', 'manager', NULL, NULL, 735, 'Germany', 3, NULL);
INSERT INTO codes (ext_code, class, db_code, short_name, long_name, description, opening_dt, closing_dt, last_change_dt, last_change_user, dirty, chk_lvl, guid, owner, version, synch) VALUES ('Semen', 'CRYO_TYPE', 111, 'Sperma', 'Semen', NULL, '2007-04-26', NULL, '2008-12-08 10:51:19', 'manager', NULL, NULL, 489, 'Germany', 4, NULL);
INSERT INTO codes (ext_code, class, db_code, short_name, long_name, description, opening_dt, closing_dt, last_change_dt, last_change_user, dirty, chk_lvl, guid, owner, version, synch) VALUES ('f', 'SEX', 117, 'weiblich', 'female', NULL, '2007-04-26', NULL, '2008-12-08 10:56:08', 'manager', NULL, NULL, 495, 'Germany', 2, NULL);
INSERT INTO codes (ext_code, class, db_code, short_name, long_name, description, opening_dt, closing_dt, last_change_dt, last_change_user, dirty, chk_lvl, guid, owner, version, synch) VALUES ('Sheep', 'SPECIES', 313, 'Schaf', 'Sheep', NULL, '2007-04-26', NULL, '2008-12-08 11:01:35', 'manager', NULL, NULL, 737, 'Germany', 2, NULL);
INSERT INTO codes (ext_code, class, db_code, short_name, long_name, description, opening_dt, closing_dt, last_change_dt, last_change_user, dirty, chk_lvl, guid, owner, version, synch) VALUES ('Ostfr. Milchschaf', 'BREED', 317, 'OMS', 'Ostfr. Milchschaf', NULL, '2007-05-22', NULL, '2008-12-15 10:26:10', 'manager', NULL, NULL, 893, 'Germany', 3, NULL);
INSERT INTO codes (ext_code, class, db_code, short_name, long_name, description, opening_dt, closing_dt, last_change_dt, last_change_user, dirty, chk_lvl, guid, owner, version, synch) VALUES ('owned', 'AVAILABILITY', 312, 'Besitz', 'Besitz', 'Material dieser Klasse befindet sich nicht im Eigentum und der Verfügung der Genbank und kann somit nur mit Billigung des Besitzers entnommen werden.', '2007-04-26', NULL, '2008-12-15 11:06:54', 'manager', NULL, NULL, 736, 'Germany', 3, NULL);
INSERT INTO codes (ext_code, class, db_code, short_name, long_name, description, opening_dt, closing_dt, last_change_dt, last_change_user, dirty, chk_lvl, guid, owner, version, synch) VALUES ('Germany', 'COUNTRY', 107, 'Deutschland', 'Germany', NULL, '2007-04-26', NULL, '2009-01-15 13:34:25', 'manager', NULL, NULL, 485, 'Germany', 3, NULL);
INSERT INTO codes (ext_code, class, db_code, short_name, long_name, description, opening_dt, closing_dt, last_change_dt, last_change_user, dirty, chk_lvl, guid, owner, version, synch) VALUES ('m', 'SEX', 118, 'maennlich', 'male', NULL, '2007-04-26', NULL, '2016-08-08 14:37:08', 'mhenn', NULL, NULL, 496, 'Germany', 3, NULL);
INSERT INTO codes (ext_code, class, db_code, short_name, long_name, description, opening_dt, closing_dt, last_change_dt, last_change_user, dirty, chk_lvl, guid, owner, version, synch) VALUES ('Aberdeen Angus', 'BREED', 358, 'AA', 'Aberdeen Angus', NULL, '2008-12-08', NULL, '2008-12-08 11:10:31', 'manager', NULL, NULL, 7499, 'Germany', 1, NULL);
INSERT INTO codes (ext_code, class, db_code, short_name, long_name, description, opening_dt, closing_dt, last_change_dt, last_change_user, dirty, chk_lvl, guid, owner, version, synch) VALUES ('Cattle', 'SPECIES', 341, 'Rind', 'Cattle', NULL, '2007-10-31', NULL, '2008-12-08 11:01:00', 'manager', NULL, NULL, 2007, 'Germany', 2, NULL);


--
-- Data for Name: nodes; Type: TABLE DATA; Schema: apiis_admin; Owner: apiis_admin
--

INSERT INTO nodes (nodename, address, last_change_dt, last_change_user, dirty, chk_lvl, guid, owner, version, synch) VALUES ('Germany', '127.0.0.1', '2008-12-04 09:28:01', '', NULL, NULL, 143, 'Germany', 1, NULL);


--
-- Data for Name: protocols; Type: TABLE DATA; Schema: apiis_admin; Owner: apiis_admin
--

INSERT INTO protocols (protocol_id, protocol_name, db_material_type, comment, chk_lvl, dirty, guid, last_change_dt, last_change_user, owner, synch, version) VALUES (100, 'NHS_Kryoprotokoll_Schafe_2004', 111, 'Nebenhodenschwanzsperma Schafböcke', NULL, NULL, 760, '2010-05-19 11:17:18', 'mhenn', 'Germany', NULL, 11);


--
-- Name: seq_ar_constraints__cons_id; Type: SEQUENCE SET; Schema: apiis_admin; Owner: apiis_admin
--

SELECT pg_catalog.setval('seq_ar_constraints__cons_id', 101, false);


--
-- Name: seq_ar_dbtdescriptors__descriptor_id; Type: SEQUENCE SET; Schema: apiis_admin; Owner: apiis_admin
--

SELECT pg_catalog.setval('seq_ar_dbtdescriptors__descriptor_id', 101, false);


--
-- Name: seq_ar_dbtpolicies__dbtpolicy_id; Type: SEQUENCE SET; Schema: apiis_admin; Owner: apiis_admin
--

SELECT pg_catalog.setval('seq_ar_dbtpolicies__dbtpolicy_id', 144, false);


--
-- Name: seq_ar_dbttables__table_id; Type: SEQUENCE SET; Schema: apiis_admin; Owner: apiis_admin
--

SELECT pg_catalog.setval('seq_ar_dbttables__table_id', 101, false);


--
-- Name: seq_ar_roles__role_id; Type: SEQUENCE SET; Schema: apiis_admin; Owner: apiis_admin
--

SELECT pg_catalog.setval('seq_ar_roles__role_id', 124, true);


--
-- Name: seq_ar_stpolicies__stpolicy_id; Type: SEQUENCE SET; Schema: apiis_admin; Owner: apiis_admin
--

SELECT pg_catalog.setval('seq_ar_stpolicies__stpolicy_id', 101, false);


--
-- Name: seq_ar_users__user_id; Type: SEQUENCE SET; Schema: apiis_admin; Owner: apiis_admin
--

SELECT pg_catalog.setval('seq_ar_users__user_id', 109, true);


--
-- Name: seq_blobs__blob_id; Type: SEQUENCE SET; Schema: apiis_admin; Owner: apiis_admin
--

SELECT pg_catalog.setval('seq_blobs__blob_id', 129, true);


--
-- Name: seq_breeds_species__breed_id; Type: SEQUENCE SET; Schema: apiis_admin; Owner: apiis_admin
--

SELECT pg_catalog.setval('seq_breeds_species__breed_id', 601, true);


--
-- Name: seq_codes__db_code; Type: SEQUENCE SET; Schema: apiis_admin; Owner: apiis_admin
--

SELECT pg_catalog.setval('seq_codes__db_code', 837, true);


--
-- Name: seq_contacts__db_contact; Type: SEQUENCE SET; Schema: apiis_admin; Owner: apiis_admin
--

SELECT pg_catalog.setval('seq_contacts__db_contact', 127, true);


--
-- Name: seq_database__guid; Type: SEQUENCE SET; Schema: apiis_admin; Owner: apiis_admin
--

SELECT pg_catalog.setval('seq_database__guid', 18599, true);


--
-- Name: seq_event__event_id; Type: SEQUENCE SET; Schema: apiis_admin; Owner: apiis_admin
--

SELECT pg_catalog.setval('seq_event__event_id', 100, false);


--
-- Name: seq_inspool__record_seq; Type: SEQUENCE SET; Schema: apiis_admin; Owner: apiis_admin
--

SELECT pg_catalog.setval('seq_inspool__record_seq', 100, false);


--
-- Name: seq_languages__lang_id; Type: SEQUENCE SET; Schema: apiis_admin; Owner: apiis_admin
--

SELECT pg_catalog.setval('seq_languages__lang_id', 100, false);


--
-- Name: seq_movements__movements_id; Type: SEQUENCE SET; Schema: apiis_admin; Owner: apiis_admin
--

SELECT pg_catalog.setval('seq_movements__movements_id', 4827, true);


--
-- Name: seq_status_changes__status_change_id; Type: SEQUENCE SET; Schema: apiis_admin; Owner: apiis_admin
--

SELECT pg_catalog.setval('seq_status_changes__status_change_id', 100, false);


--
-- Name: seq_storage__storage_id; Type: SEQUENCE SET; Schema: apiis_admin; Owner: apiis_admin
--

SELECT pg_catalog.setval('seq_storage__storage_id', 5624, true);


--
-- Name: seq_transfer__db_animal; Type: SEQUENCE SET; Schema: apiis_admin; Owner: apiis_admin
--

SELECT pg_catalog.setval('seq_transfer__db_animal', 1134, true);


--
-- Name: seq_unit__db_unit; Type: SEQUENCE SET; Schema: apiis_admin; Owner: apiis_admin
--

SELECT pg_catalog.setval('seq_unit__db_unit', 147, true);


--
-- Name: seq_vessels__db_vessel; Type: SEQUENCE SET; Schema: apiis_admin; Owner: apiis_admin
--

SELECT pg_catalog.setval('seq_vessels__db_vessel', 1745, true);


--
-- Name: seq_vessels_storage__vessels_storage_id; Type: SEQUENCE SET; Schema: apiis_admin; Owner: apiis_admin
--

SELECT pg_catalog.setval('seq_vessels_storage__vessels_storage_id', 3663, true);


--
-- Data for Name: transfer; Type: TABLE DATA; Schema: apiis_admin; Owner: apiis_admin
--

INSERT INTO transfer (db_animal, ext_animal, db_unit, id_set, opening_dt, closing_dt, last_change_dt, last_change_user, dirty, chk_lvl, guid, owner, version, synch) VALUES (1, 'unknown_sire', 100, NULL, '2007-04-26', NULL, '2007-04-26 12:30:05', 'cryo', NULL, NULL, 480, 'Germany', 1, NULL);
INSERT INTO transfer (db_animal, ext_animal, db_unit, id_set, opening_dt, closing_dt, last_change_dt, last_change_user, dirty, chk_lvl, guid, owner, version, synch) VALUES (2, 'unknown_dam', 100, NULL, '2007-04-26', NULL, '2007-04-26 12:30:05', 'cryo', NULL, NULL, 481, 'Germany', 1, NULL);
INSERT INTO transfer (db_animal, ext_animal, db_unit, id_set, opening_dt, closing_dt, last_change_dt, last_change_user, dirty, chk_lvl, guid, owner, version, synch) VALUES (438, 'WF60/B0811', 100, NULL, '2007-06-14', NULL, '2007-06-14 14:54:36', 'jmoos', NULL, NULL, 1958, 'Germany', 1, NULL);
INSERT INTO transfer (db_animal, ext_animal, db_unit, id_set, opening_dt, closing_dt, last_change_dt, last_change_user, dirty, chk_lvl, guid, owner, version, synch) VALUES (439, 'WF60/6532', 100, NULL, '2007-06-14', NULL, '2007-06-14 14:55:05', 'jmoos', NULL, NULL, 1960, 'Germany', 1, NULL);
INSERT INTO transfer (db_animal, ext_animal, db_unit, id_set, opening_dt, closing_dt, last_change_dt, last_change_user, dirty, chk_lvl, guid, owner, version, synch) VALUES (440, 'WF001265', 100, NULL, '2008-01-16', NULL, '2008-01-16 16:18:14', 'jmoos', NULL, NULL, 1962, 'Germany', 2, NULL);


--
-- Data for Name: unit; Type: TABLE DATA; Schema: apiis_admin; Owner: apiis_admin
--

INSERT INTO unit (db_unit, ext_unit, ext_id, db_contact, db_member, opening_dt, closing_dt, last_change_dt, last_change_user, dirty, chk_lvl, guid, owner, version, synch) VALUES (100, 'ANIMAL', 'ID', NULL, NULL, '2007-04-26', NULL, '2007-04-26 12:30:05', 'cryo', NULL, NULL, 478, 'Germany', 1, NULL);


--
-- Data for Name: vessels; Type: TABLE DATA; Schema: apiis_admin; Owner: apiis_admin
--

INSERT INTO vessels (db_vessel, ext_vessel, db_animal, protocol_id, production_dt, freezing_dt, db_vessel_type, comment, chk_lvl, dirty, guid, last_change_dt, last_change_user, owner, synch, version, db_contributor) VALUES (1451, 'MA_052_KR_S_Snh_S03_Mariensee_WF001265_OMS_13.01.04', 440, 100, '2004-01-13', '2004-01-13', 108, 'Qualitätsrate (Mot) 87,5 %', NULL, NULL, 8417, '2008-12-15 18:29:57', 'jmoos', 'Germany', NULL, 1, NULL);


--
-- PostgreSQL database dump complete
--
