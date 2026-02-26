--
-- PostgreSQL database dump
--

\restrict iHxUCaMZrYfkc5TAbyqawDVbiWbCWdbiR2OgseZcleBxnUrZZhwTn1tDTKDXMXL

-- Dumped from database version 15.16 (cd0aa6c)
-- Dumped by pg_dump version 16.11 (Ubuntu 16.11-0ubuntu0.24.04.1)

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
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.alembic_version (version_num) VALUES ('bb04cbdbc713');


--
-- Data for Name: user; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public."user" (id, email, full_name, password_hash, role, resume_text, profile_image, profile_image_bytes, face_embedding) VALUES (6, 'sakshama2@test.com', 'Sakshama2', '$pbkdf2-sha256$29000$e.8dQ2gthVBqjVFqDWFs7Q$RgC3uSKxf0Tmwf1DI6Um2rSTOUbdpM2Sss5/NW5oEc4', 'ADMIN', NULL, NULL, NULL, NULL);
INSERT INTO public."user" (id, email, full_name, password_hash, role, resume_text, profile_image, profile_image_bytes, face_embedding) VALUES (9, 'sakshamsa2@test.com', 'Sakshamsa2', '$pbkdf2-sha256$29000$lDKGEMLYW6tVai2FkNLauw$3zKsvAOBe/SJBS9Haeib7Srbu7Vij7.26pwRfvwgGBA', 'SUPER_ADMIN', NULL, NULL, NULL, NULL);
INSERT INTO public."user" (id, email, full_name, password_hash, role, resume_text, profile_image, profile_image_bytes, face_embedding) VALUES (23, 'tushar@chicmicstudios.in', 'Tushar', '$pbkdf2-sha256$29000$dG4tRchZC2Hs/T9nLEWolQ$Oci2x0mZNwTux5yzRqfXQamYBXVS7Q6TuuHsQ3ENfcc', 'CANDIDATE', NULL, NULL, NULL, NULL);
INSERT INTO public."user" (id, email, full_name, password_hash, role, resume_text, profile_image, profile_image_bytes, face_embedding) VALUES (24, 'sarthak@chicmicstudios.in', 'Sarthak', '$pbkdf2-sha256$29000$nPNea02pdc6Z836PkdL6/w$.75vbbvlN6CZsRbYSQ.Z68.xavwJ6nWwUw/.msBYXUU', 'CANDIDATE', NULL, NULL, NULL, NULL);
INSERT INTO public."user" (id, email, full_name, password_hash, role, resume_text, profile_image, profile_image_bytes, face_embedding) VALUES (25, 'sameer.chandra@chicmicstudios.in', 'Sameer', '$pbkdf2-sha256$29000$yXlvzZkzxrjXek9J6b0Xog$DrSNxBWOCgEi3L42yxY0z9wYLruocACUPegCNh5vXo0', 'CANDIDATE', NULL, NULL, NULL, NULL);
INSERT INTO public."user" (id, email, full_name, password_hash, role, resume_text, profile_image, profile_image_bytes, face_embedding) VALUES (27, 'tushargoyal253@gmail.com', 'Tushar Local', '$pbkdf2-sha256$29000$mxOidG4tJeQcQ6gV4tz7vw$YZ7uyBU0yqN6/Qj9OcmyvtpKdTfqrsfKO216Xm6yqdg', 'CANDIDATE', NULL, NULL, NULL, NULL);
INSERT INTO public."user" (id, email, full_name, password_hash, role, resume_text, profile_image, profile_image_bytes, face_embedding) VALUES (26, 'kaashif.matto@chicmicstudios.in', 'Kaashif', '$pbkdf2-sha256$29000$6x3jnFOqlRJijLFWytmbEw$HGYM2HK2/TnIEPiW6qPEZtaPkS6EiVv36Zzr6hQm1wE', 'CANDIDATE', NULL, NULL, NULL, NULL);
INSERT INTO public."user" (id, email, full_name, password_hash, role, resume_text, profile_image, profile_image_bytes, face_embedding) VALUES (29, 'saksham.garg@chicmicstudios.in', 'Saksham Garg', '$pbkdf2-sha256$29000$nhOC8N6bE.K8l3KOsfa.Vw$jy4L0wmjxQb2qos7O9XIARjiEHAStuSSPruwK80VtNs', 'CANDIDATE', NULL, NULL, NULL, NULL);
INSERT INTO public."user" (id, email, full_name, password_hash, role, resume_text, profile_image, profile_image_bytes, face_embedding) VALUES (7, 'sakshamc1@test.com', 'Sakshamc1', '$pbkdf2-sha256$29000$M0YIIeT8vxfinLM2ZgzhXA$z3KNuheXkF7l7Jg2FgBA9SV3d4k4PGIZG9gcpZ4iqUg', 'CANDIDATE', NULL, NULL, NULL, NULL);
INSERT INTO public."user" (id, email, full_name, password_hash, role, resume_text, profile_image, profile_image_bytes, face_embedding) VALUES (30, 'audit_0315a5@test.com', 'Audit User', '$pbkdf2-sha256$29000$WKuVEmLsnfMeoxQCQGgt5Q$IpAWsZA5H64eiA5YECs1iEIEXK8L5zof4Y3fN.R4IKU', 'CANDIDATE', NULL, NULL, NULL, NULL);
INSERT INTO public."user" (id, email, full_name, password_hash, role, resume_text, profile_image, profile_image_bytes, face_embedding) VALUES (5, 'sakshama1@test.com', 'Sakshama1', '$pbkdf2-sha256$29000$3ru39h6j9D6n1Nq7d.4dww$pjuvabF89CzzdAXxJjULlaFskaoX3Uesl7YcBmgyPjQ', 'ADMIN', NULL, NULL, NULL, NULL);
INSERT INTO public."user" (id, email, full_name, password_hash, role, resume_text, profile_image, profile_image_bytes, face_embedding) VALUES (32, 'audit_73f01d@test.com', 'Audit User', '$pbkdf2-sha256$29000$xhjj3Puf8/5fy7lXSiklpA$/26xOeptDOra4cRcaSuTRLI20vz0Wa98IpV9qeB4O4g', 'CANDIDATE', NULL, NULL, NULL, NULL);
INSERT INTO public."user" (id, email, full_name, password_hash, role, resume_text, profile_image, profile_image_bytes, face_embedding) VALUES (1, 'admin@test.com', 'Super Admin', '$pbkdf2-sha256$29000$yJmzthZijDFmbI3xnrPW.g$ljiIHBEC9PlIBhGJk4McP9fg0plvidOPTC9qAam91wg', 'SUPER_ADMIN', NULL, NULL, NULL, NULL);
INSERT INTO public."user" (id, email, full_name, password_hash, role, resume_text, profile_image, profile_image_bytes, face_embedding) VALUES (8, 'sakshamc2@test.com', 'Sakshamc2', '$pbkdf2-sha256$29000$zRkjRKh1rlWKcW7N2XtvbQ$tz4v4wsV6gY065zAnWO4XUOeBL7U8lkDnTIwQL.xbDA', 'CANDIDATE', NULL, NULL, NULL, NULL);


--
-- Data for Name: questionpaper; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.questionpaper (id, name, description, admin_id, created_at) VALUES (1, 'ReactJs Test', 'Frontend Development', 1, '2026-02-14 08:08:39.339001');
INSERT INTO public.questionpaper (id, name, description, admin_id, created_at) VALUES (2, 'NodeJs Test', 'Backend Development', 1, '2026-02-14 11:10:26.561974');
INSERT INTO public.questionpaper (id, name, description, admin_id, created_at) VALUES (3, 'NodeJs Interview', 'Backend Development', 5, '2026-02-14 13:12:21.213832');
INSERT INTO public.questionpaper (id, name, description, admin_id, created_at) VALUES (4, 'ReactJs Interview', 'Frontend Development', 5, '2026-02-16 05:23:21.761221');
INSERT INTO public.questionpaper (id, name, description, admin_id, created_at) VALUES (11, 'Devops Team', 'Cloud', 5, '2026-02-19 09:49:27.831249');
INSERT INTO public.questionpaper (id, name, description, admin_id, created_at) VALUES (12, 'Sim Paper 1863', 'E2E Test Paper', 1, '2026-02-19 10:30:56.871272');
INSERT INTO public.questionpaper (id, name, description, admin_id, created_at) VALUES (13, 'Sim Paper fb91', 'E2E Test Paper', 1, '2026-02-19 10:36:20.302402');
INSERT INTO public.questionpaper (id, name, description, admin_id, created_at) VALUES (14, 'Sim Paper bc6c', 'E2E Test Paper', 1, '2026-02-19 10:39:24.099534');
INSERT INTO public.questionpaper (id, name, description, admin_id, created_at) VALUES (15, 'Sim Paper fa76', 'E2E Test Paper', 1, '2026-02-19 10:45:07.301561');
INSERT INTO public.questionpaper (id, name, description, admin_id, created_at) VALUES (17, 'Audit Master Paper', 'End-to-end testing paper', 1, '2026-02-19 11:55:35.203029');
INSERT INTO public.questionpaper (id, name, description, admin_id, created_at) VALUES (18, 'Audit Paper x66r', 'Verification paper for cloud audit', 1, '2026-02-20 05:57:08.207318');
INSERT INTO public.questionpaper (id, name, description, admin_id, created_at) VALUES (19, 'Audit Paper 8ypu', 'Verification paper for cloud audit', 1, '2026-02-20 05:57:47.738986');
INSERT INTO public.questionpaper (id, name, description, admin_id, created_at) VALUES (20, 'Audit Paper bp5d', 'Verification paper for cloud audit', 1, '2026-02-20 05:58:11.039294');
INSERT INTO public.questionpaper (id, name, description, admin_id, created_at) VALUES (21, 'Audit Paper 9l5e', 'Verification paper for cloud audit', 1, '2026-02-20 05:58:38.896399');
INSERT INTO public.questionpaper (id, name, description, admin_id, created_at) VALUES (22, 'Manual Verification Test Paper', 'Test paper with text and audio questions.', 1, '2026-02-23 04:48:05.39062');
INSERT INTO public.questionpaper (id, name, description, admin_id, created_at) VALUES (23, 'Audit Paper ff76', 'Updated by audit', 1, '2026-02-24 05:39:26.969538');


--
-- Data for Name: interviewsession; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.interviewsession (id, access_token, admin_id, candidate_id, paper_id, schedule_time, duration_minutes, max_questions, start_time, end_time, status, total_score, current_status, last_activity, warning_count, max_warnings, is_suspended, suspension_reason, suspended_at, enrollment_audio_path, candidate_name, admin_name, is_completed, invite_link) VALUES (1, '3d5e5f3adc9746f9bca76202d3943024', 1, 7, 1, '2026-02-14 11:28:33.54', 180, 3, '2026-02-14 12:22:27.31917', '2026-02-14 12:24:32.780608', 'COMPLETED', 0, 'INTERVIEW_COMPLETED', '2026-02-14 12:24:32.780761', 0, 3, false, NULL, NULL, NULL, NULL, NULL, true, NULL);
INSERT INTO public.interviewsession (id, access_token, admin_id, candidate_id, paper_id, schedule_time, duration_minutes, max_questions, start_time, end_time, status, total_score, current_status, last_activity, warning_count, max_warnings, is_suspended, suspension_reason, suspended_at, enrollment_audio_path, candidate_name, admin_name, is_completed, invite_link) VALUES (69, 'a402528b8f1a4e2fb9d0c028fe7d5bae', 1, 32, 1, '2026-02-25 11:19:07', 60, NULL, NULL, NULL, 'SCHEDULED', NULL, 'INVITED', '2026-02-25 11:19:09.769479', 0, 3, false, NULL, NULL, NULL, NULL, NULL, false, NULL);
INSERT INTO public.interviewsession (id, access_token, admin_id, candidate_id, paper_id, schedule_time, duration_minutes, max_questions, start_time, end_time, status, total_score, current_status, last_activity, warning_count, max_warnings, is_suspended, suspension_reason, suspended_at, enrollment_audio_path, candidate_name, admin_name, is_completed, invite_link) VALUES (2, '8bb1556c19f6442f98ee3abda47ba7e7', 5, 7, 3, '2026-02-14 13:17:12.814', 180, 3, NULL, '2026-02-14 13:55:57.695742', 'COMPLETED', 0, 'INTERVIEW_COMPLETED', '2026-02-14 13:55:57.695923', 0, 3, false, NULL, NULL, NULL, NULL, NULL, true, NULL);
INSERT INTO public.interviewsession (id, access_token, admin_id, candidate_id, paper_id, schedule_time, duration_minutes, max_questions, start_time, end_time, status, total_score, current_status, last_activity, warning_count, max_warnings, is_suspended, suspension_reason, suspended_at, enrollment_audio_path, candidate_name, admin_name, is_completed, invite_link) VALUES (5, '18ac741376ad4119bdaf15b27db685c6', 1, 7, 2, '2026-02-17 05:06:56.797', 180, 5, NULL, NULL, 'SCHEDULED', NULL, 'INVITED', '2026-02-17 09:36:36.138545', 0, 3, false, NULL, NULL, NULL, NULL, NULL, false, NULL);
INSERT INTO public.interviewsession (id, access_token, admin_id, candidate_id, paper_id, schedule_time, duration_minutes, max_questions, start_time, end_time, status, total_score, current_status, last_activity, warning_count, max_warnings, is_suspended, suspension_reason, suspended_at, enrollment_audio_path, candidate_name, admin_name, is_completed, invite_link) VALUES (6, '604996b4806744aeb225f877ba5c9a04', 1, 7, 2, '2026-02-17 05:06:56.797', 180, 2, NULL, NULL, 'SCHEDULED', NULL, 'INVITED', '2026-02-17 09:36:48.372125', 0, 3, false, NULL, NULL, NULL, NULL, NULL, false, NULL);
INSERT INTO public.interviewsession (id, access_token, admin_id, candidate_id, paper_id, schedule_time, duration_minutes, max_questions, start_time, end_time, status, total_score, current_status, last_activity, warning_count, max_warnings, is_suspended, suspension_reason, suspended_at, enrollment_audio_path, candidate_name, admin_name, is_completed, invite_link) VALUES (64, '9ebd6b38d9d6409a8e56e4b383ce884f', 1, 23, 1, '2026-02-26 10:00:00', 14, 3, NULL, NULL, 'SCHEDULED', NULL, 'INVITED', '2026-02-25 09:08:20.569877', 0, 3, false, NULL, NULL, NULL, NULL, NULL, false, NULL);
INSERT INTO public.interviewsession (id, access_token, admin_id, candidate_id, paper_id, schedule_time, duration_minutes, max_questions, start_time, end_time, status, total_score, current_status, last_activity, warning_count, max_warnings, is_suspended, suspension_reason, suspended_at, enrollment_audio_path, candidate_name, admin_name, is_completed, invite_link) VALUES (65, '719802ae272949a3954b5eee2edc4c85', 1, 32, 1, '2026-02-25 10:17:55', 60, NULL, NULL, NULL, 'SCHEDULED', NULL, 'INVITED', '2026-02-25 10:17:57.189839', 0, 3, false, NULL, NULL, NULL, NULL, NULL, false, NULL);
INSERT INTO public.interviewsession (id, access_token, admin_id, candidate_id, paper_id, schedule_time, duration_minutes, max_questions, start_time, end_time, status, total_score, current_status, last_activity, warning_count, max_warnings, is_suspended, suspension_reason, suspended_at, enrollment_audio_path, candidate_name, admin_name, is_completed, invite_link) VALUES (56, '268851680b5b465b9b4a3a21806b4bd3', 1, 25, 2, '2026-02-24 04:35:00', 30, NULL, '2026-02-24 04:34:52.416882', '2026-02-24 04:35:32.73353', 'COMPLETED', 2.6666666666666665, 'INTERVIEW_COMPLETED', '2026-02-24 04:35:32.733748', 0, 3, false, NULL, NULL, NULL, NULL, NULL, true, NULL);
INSERT INTO public.interviewsession (id, access_token, admin_id, candidate_id, paper_id, schedule_time, duration_minutes, max_questions, start_time, end_time, status, total_score, current_status, last_activity, warning_count, max_warnings, is_suspended, suspension_reason, suspended_at, enrollment_audio_path, candidate_name, admin_name, is_completed, invite_link) VALUES (39, '4ca26c2e928145a9b80445958e1b3a3c', 1, 23, 1, '2026-02-23 08:45:00', 30, NULL, NULL, NULL, 'SCHEDULED', NULL, 'INVITED', '2026-02-23 08:41:06.527621', 0, 3, false, NULL, NULL, NULL, NULL, NULL, false, NULL);
INSERT INTO public.interviewsession (id, access_token, admin_id, candidate_id, paper_id, schedule_time, duration_minutes, max_questions, start_time, end_time, status, total_score, current_status, last_activity, warning_count, max_warnings, is_suspended, suspension_reason, suspended_at, enrollment_audio_path, candidate_name, admin_name, is_completed, invite_link) VALUES (53, '2a01a810447c4c64bd10f19f9bb960e4', 1, 25, 2, '2026-02-24 04:26:00', 30, NULL, '2026-02-24 04:25:58.599088', '2026-02-24 04:26:40.997943', 'COMPLETED', 2.5, 'INTERVIEW_COMPLETED', '2026-02-24 04:26:40.998174', 0, 3, false, NULL, NULL, NULL, NULL, NULL, true, NULL);
INSERT INTO public.interviewsession (id, access_token, admin_id, candidate_id, paper_id, schedule_time, duration_minutes, max_questions, start_time, end_time, status, total_score, current_status, last_activity, warning_count, max_warnings, is_suspended, suspension_reason, suspended_at, enrollment_audio_path, candidate_name, admin_name, is_completed, invite_link) VALUES (70, '482cdb16325a49039eeee403b8f25c3a', 5, 7, 4, '2026-02-25 17:08:00', 180, 3, '2026-02-25 19:13:24.326462', NULL, 'LIVE', NULL, 'LINK_ACCESSED', '2026-02-25 17:08:12.881798', 0, 3, false, NULL, NULL, NULL, NULL, NULL, false, NULL);
INSERT INTO public.interviewsession (id, access_token, admin_id, candidate_id, paper_id, schedule_time, duration_minutes, max_questions, start_time, end_time, status, total_score, current_status, last_activity, warning_count, max_warnings, is_suspended, suspension_reason, suspended_at, enrollment_audio_path, candidate_name, admin_name, is_completed, invite_link) VALUES (58, '53f1365ec81e47fca65c1868b5fec371', 1, 23, 1, '2026-02-24 18:00:00', 60, 5, NULL, NULL, 'SCHEDULED', NULL, 'INVITED', '2026-02-24 10:37:33.205253', 0, 3, false, NULL, NULL, NULL, NULL, NULL, false, NULL);
INSERT INTO public.interviewsession (id, access_token, admin_id, candidate_id, paper_id, schedule_time, duration_minutes, max_questions, start_time, end_time, status, total_score, current_status, last_activity, warning_count, max_warnings, is_suspended, suspension_reason, suspended_at, enrollment_audio_path, candidate_name, admin_name, is_completed, invite_link) VALUES (59, '838272f8b4784fb2b7d82014f839e2ad', 1, 23, 1, '2026-02-24 18:00:00', 14, 2, NULL, NULL, 'SCHEDULED', NULL, 'INVITED', '2026-02-24 10:55:11.190129', 0, 3, false, NULL, NULL, NULL, NULL, NULL, false, NULL);
INSERT INTO public.interviewsession (id, access_token, admin_id, candidate_id, paper_id, schedule_time, duration_minutes, max_questions, start_time, end_time, status, total_score, current_status, last_activity, warning_count, max_warnings, is_suspended, suspension_reason, suspended_at, enrollment_audio_path, candidate_name, admin_name, is_completed, invite_link) VALUES (60, 'ee277d5bbb5b43cd97d7a984cb399c59', 1, 23, 1, '2026-02-24 18:00:00', 14, 2, NULL, NULL, 'SCHEDULED', NULL, 'INVITED', '2026-02-24 11:51:11.530244', 0, 3, false, NULL, NULL, NULL, NULL, NULL, false, NULL);
INSERT INTO public.interviewsession (id, access_token, admin_id, candidate_id, paper_id, schedule_time, duration_minutes, max_questions, start_time, end_time, status, total_score, current_status, last_activity, warning_count, max_warnings, is_suspended, suspension_reason, suspended_at, enrollment_audio_path, candidate_name, admin_name, is_completed, invite_link) VALUES (47, 'b2b5481f9c0c415eb30e2a74eef78000', 1, 24, 1, '2026-02-23 12:05:00', 30, NULL, '2026-02-23 12:05:00.37572', '2026-02-23 12:05:54.298428', 'COMPLETED', 3, 'INTERVIEW_COMPLETED', '2026-02-23 12:05:54.298626', 0, 3, false, NULL, NULL, NULL, NULL, NULL, true, NULL);
INSERT INTO public.interviewsession (id, access_token, admin_id, candidate_id, paper_id, schedule_time, duration_minutes, max_questions, start_time, end_time, status, total_score, current_status, last_activity, warning_count, max_warnings, is_suspended, suspension_reason, suspended_at, enrollment_audio_path, candidate_name, admin_name, is_completed, invite_link) VALUES (54, 'bf5604b3611c4e1ea42e40cd7b3d1390', 1, 25, 2, '2026-02-24 04:31:00', 30, NULL, '2026-02-24 04:31:16.371409', '2026-02-24 04:32:03.544745', 'COMPLETED', 2, 'INTERVIEW_COMPLETED', '2026-02-24 04:32:03.544942', 0, 3, false, NULL, NULL, NULL, NULL, NULL, true, NULL);
INSERT INTO public.interviewsession (id, access_token, admin_id, candidate_id, paper_id, schedule_time, duration_minutes, max_questions, start_time, end_time, status, total_score, current_status, last_activity, warning_count, max_warnings, is_suspended, suspension_reason, suspended_at, enrollment_audio_path, candidate_name, admin_name, is_completed, invite_link) VALUES (12, '584980a32013486f95174dce77989639', 1, NULL, 17, '2026-02-19 18:00:00', 180, NULL, '2026-02-19 12:01:16.25546', '2026-02-19 12:03:41.686185', 'COMPLETED', 3, 'INTERVIEW_COMPLETED', '2026-02-19 12:03:41.686375', 0, 3, false, NULL, NULL, NULL, 'Audit Candidate', NULL, true, NULL);
INSERT INTO public.interviewsession (id, access_token, admin_id, candidate_id, paper_id, schedule_time, duration_minutes, max_questions, start_time, end_time, status, total_score, current_status, last_activity, warning_count, max_warnings, is_suspended, suspension_reason, suspended_at, enrollment_audio_path, candidate_name, admin_name, is_completed, invite_link) VALUES (66, '0546caa06b574251959f73b76b87d34e', 1, 32, 1, '2026-02-25 10:18:50', 60, NULL, NULL, NULL, 'SCHEDULED', NULL, 'LINK_ACCESSED', '2026-02-25 10:18:57.338353', 0, 3, false, NULL, NULL, NULL, NULL, NULL, false, NULL);
INSERT INTO public.interviewsession (id, access_token, admin_id, candidate_id, paper_id, schedule_time, duration_minutes, max_questions, start_time, end_time, status, total_score, current_status, last_activity, warning_count, max_warnings, is_suspended, suspension_reason, suspended_at, enrollment_audio_path, candidate_name, admin_name, is_completed, invite_link) VALUES (61, 'f1292038bd954f5291d588149dd48291', 1, 23, 1, '2026-02-24 18:00:00', 14, 2, NULL, NULL, 'SCHEDULED', NULL, 'INVITED', '2026-02-24 12:10:02.625089', 0, 3, false, NULL, NULL, NULL, NULL, NULL, false, NULL);
INSERT INTO public.interviewsession (id, access_token, admin_id, candidate_id, paper_id, schedule_time, duration_minutes, max_questions, start_time, end_time, status, total_score, current_status, last_activity, warning_count, max_warnings, is_suspended, suspension_reason, suspended_at, enrollment_audio_path, candidate_name, admin_name, is_completed, invite_link) VALUES (14, 'eba6fb0fb1284c83a827a2d77588807e', 1, NULL, 19, '2026-02-20 05:57:48.290688', 30, NULL, NULL, NULL, 'SCHEDULED', NULL, 'INVITED', '2026-02-20 05:57:48.606303', 0, 3, false, NULL, NULL, NULL, 'Auditor Candidate 8ypu', NULL, false, NULL);
INSERT INTO public.interviewsession (id, access_token, admin_id, candidate_id, paper_id, schedule_time, duration_minutes, max_questions, start_time, end_time, status, total_score, current_status, last_activity, warning_count, max_warnings, is_suspended, suspension_reason, suspended_at, enrollment_audio_path, candidate_name, admin_name, is_completed, invite_link) VALUES (7, '8dcf27cf3f76400197215b41d7d3d686', 1, NULL, 12, '2026-02-19 10:31:00.08426', 60, 2, '2026-02-19 10:31:01.049237', NULL, 'LIVE', NULL, 'INTERVIEW_ACTIVE', '2026-02-19 10:31:01.451453', 0, 3, false, NULL, NULL, 'app/assets/audio/enrollment/enroll_7.wav', 'Sim Candidate', NULL, false, NULL);
INSERT INTO public.interviewsession (id, access_token, admin_id, candidate_id, paper_id, schedule_time, duration_minutes, max_questions, start_time, end_time, status, total_score, current_status, last_activity, warning_count, max_warnings, is_suspended, suspension_reason, suspended_at, enrollment_audio_path, candidate_name, admin_name, is_completed, invite_link) VALUES (9, '9b5d231d293140b2924d47d4894c8ed4', 1, NULL, 14, '2026-02-19 10:39:27.505877', 60, 2, '2026-02-19 10:39:28.478071', NULL, 'LIVE', NULL, 'INTERVIEW_ACTIVE', '2026-02-19 10:39:28.88724', 0, 3, false, NULL, NULL, 'app/assets/audio/enrollment/enroll_9.wav', 'Sim Candidate', NULL, false, NULL);
INSERT INTO public.interviewsession (id, access_token, admin_id, candidate_id, paper_id, schedule_time, duration_minutes, max_questions, start_time, end_time, status, total_score, current_status, last_activity, warning_count, max_warnings, is_suspended, suspension_reason, suspended_at, enrollment_audio_path, candidate_name, admin_name, is_completed, invite_link) VALUES (15, '5b23de121e3848738decfe2fdccfba73', 1, NULL, 20, '2026-02-20 05:58:11.665122', 30, NULL, NULL, NULL, 'SCHEDULED', NULL, 'INVITED', '2026-02-20 05:58:11.928375', 0, 3, false, NULL, NULL, NULL, 'Auditor Candidate bp5d', NULL, false, NULL);
INSERT INTO public.interviewsession (id, access_token, admin_id, candidate_id, paper_id, schedule_time, duration_minutes, max_questions, start_time, end_time, status, total_score, current_status, last_activity, warning_count, max_warnings, is_suspended, suspension_reason, suspended_at, enrollment_audio_path, candidate_name, admin_name, is_completed, invite_link) VALUES (67, 'c185bf37a65f4ec9a139c13909db9ec5', 1, 32, 1, '2026-02-25 10:21:07', 60, NULL, NULL, NULL, 'SCHEDULED', NULL, 'LINK_ACCESSED', '2026-02-25 10:21:13.779413', 0, 3, false, NULL, NULL, NULL, NULL, NULL, false, NULL);
INSERT INTO public.interviewsession (id, access_token, admin_id, candidate_id, paper_id, schedule_time, duration_minutes, max_questions, start_time, end_time, status, total_score, current_status, last_activity, warning_count, max_warnings, is_suspended, suspension_reason, suspended_at, enrollment_audio_path, candidate_name, admin_name, is_completed, invite_link) VALUES (44, 'da78bf1c24d44f8d80266e8ff27f8dac', 1, 26, 1, '2026-02-23 10:50:00', 30, NULL, NULL, NULL, 'SCHEDULED', NULL, 'LINK_ACCESSED', '2026-02-23 10:59:59.681208', 0, 3, false, NULL, NULL, NULL, NULL, NULL, false, NULL);
INSERT INTO public.interviewsession (id, access_token, admin_id, candidate_id, paper_id, schedule_time, duration_minutes, max_questions, start_time, end_time, status, total_score, current_status, last_activity, warning_count, max_warnings, is_suspended, suspension_reason, suspended_at, enrollment_audio_path, candidate_name, admin_name, is_completed, invite_link) VALUES (10, '3eb061053ec84a8bb4740ee923ca1bac', 1, NULL, 15, '2026-02-19 10:45:10.451019', 60, 2, '2026-02-19 10:45:11.377619', NULL, 'LIVE', NULL, 'INTERVIEW_ACTIVE', '2026-02-19 11:09:07.853922', 0, 3, false, NULL, NULL, 'app/assets/audio/enrollment/enroll_10.wav', 'Sim Candidate', NULL, false, NULL);
INSERT INTO public.interviewsession (id, access_token, admin_id, candidate_id, paper_id, schedule_time, duration_minutes, max_questions, start_time, end_time, status, total_score, current_status, last_activity, warning_count, max_warnings, is_suspended, suspension_reason, suspended_at, enrollment_audio_path, candidate_name, admin_name, is_completed, invite_link) VALUES (8, 'cee1ec5fd1cc48fc9bc8a2113d639cab', 1, NULL, 13, '2026-02-19 10:36:23.29022', 60, 2, '2026-02-19 10:36:24.202062', NULL, 'LIVE', NULL, 'INTERVIEW_ACTIVE', '2026-02-19 10:36:24.576924', 0, 3, false, NULL, NULL, 'app/assets/audio/enrollment/enroll_8.wav', 'Sim Candidate', NULL, false, NULL);


--
-- Data for Name: interviewresult; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.interviewresult (id, interview_id, total_score, created_at) VALUES (1, 2, 0, '2026-02-16 13:47:23.648426');
INSERT INTO public.interviewresult (id, interview_id, total_score, created_at) VALUES (2, 1, 0, '2026-02-17 04:54:10.314421');
INSERT INTO public.interviewresult (id, interview_id, total_score, created_at) VALUES (3, 9, 0, '2026-02-19 10:41:55.120396');
INSERT INTO public.interviewresult (id, interview_id, total_score, created_at) VALUES (5, 12, 3, '2026-02-19 12:03:19.13382');
INSERT INTO public.interviewresult (id, interview_id, total_score, created_at) VALUES (7, 47, 3, '2026-02-23 12:05:19.823438');
INSERT INTO public.interviewresult (id, interview_id, total_score, created_at) VALUES (10, 53, 2.5, '2026-02-24 04:26:15.100995');
INSERT INTO public.interviewresult (id, interview_id, total_score, created_at) VALUES (11, 54, 2, '2026-02-24 04:31:33.015417');
INSERT INTO public.interviewresult (id, interview_id, total_score, created_at) VALUES (12, 56, 2.6666666666666665, '2026-02-24 04:35:05.442055');


--
-- Data for Name: questions; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (1, 1, 'what are hooks in reactjs', 'what are hooks in reactjs', 'General', 'Medium', 1, 'audio');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (2, 1, 'what are hooks in reactjs2', 'what are hooks in reactjs2', 'General', 'Medium', 1, 'audio');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (3, 1, 'what are hooks in reactjs3', 'what are hooks in reactjs3', 'General', 'Medium', 1, 'audio');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (4, 2, 'what is jwt in nodejs', 'what is jwt in nodejs', 'General', 'Medium', 1, 'audio');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (5, 2, 'what is jwt in nodejs2', 'what is jwt in nodejs2', 'General', 'Medium', 1, 'audio');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (6, 2, 'what is jwt in nodejs3', 'what is jwt in nodejs3', 'General', 'Medium', 1, 'audio');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (10, 3, 'What is Jwt?', 'What is Jwt?', 'Auth', 'Easy', 5, 'text');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (11, 3, 'What is middleware?', 'What is middleware?', 'Auth', 'Medium', 5, 'text');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (13, NULL, 'What is FastApis?', 'What is FastApis?', 'Auth', 'Hard', 5, 'text');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (28, NULL, 'Tell me about yourself and your background in software development.', NULL, 'Dynamic', 'Unknown', 1, 'audio');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (29, NULL, 'What is your experience with JavaScript and modern web frameworks?', NULL, 'Dynamic', 'Unknown', 1, 'audio');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (30, NULL, 'what is the full form of HTML?', NULL, 'Dynamic', 'Unknown', 1, 'audio');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (31, NULL, 'what is the full form of HTML', NULL, 'Dynamic', 'Unknown', 1, 'audio');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (32, NULL, 'Full form of HTML', NULL, 'Dynamic', 'Unknown', 1, 'audio');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (33, NULL, 'What is the full form of HTML?', NULL, 'Dynamic', 'Unknown', 1, 'audio');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (34, NULL, 'string', NULL, 'Dynamic', 'Unknown', 1, 'audio');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (35, NULL, 'Explain the concept of recursion.', NULL, 'Dynamic', 'Unknown', 1, 'audio');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (20, 4, 'What is ReactJs2?', 'What is ReactJs2?', 'Frontend', 'Medium', 5, 'text');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (38, 11, 'What is EC2?', 'What is EC2?', 'Cloud', 'Medium', 10, 'text');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (39, 12, 'What is Python?', 'What is Python?', 'Tech', 'Easy', 10, 'text');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (40, 12, 'Explain AI.', 'Explain AI.', 'AI', 'Medium', 20, 'text');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (41, 13, 'What is Python?', 'What is Python?', 'Tech', 'Easy', 10, 'text');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (42, 13, 'Explain AI.', 'Explain AI.', 'AI', 'Medium', 20, 'text');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (43, 14, 'What is Python?', 'What is Python?', 'Tech', 'Easy', 10, 'text');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (44, 14, 'Explain AI.', 'Explain AI.', 'AI', 'Medium', 20, 'text');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (45, 15, 'What is Python?', 'What is Python?', 'Tech', 'Easy', 10, 'text');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (46, 15, 'Explain AI.', 'Explain AI.', 'AI', 'Medium', 20, 'text');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (67, 3, 'What is libuv?', 'What is libuv?', 'Backend', 'Hard', 5, 'text');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (49, 17, 'What is your primary motivation for joining this audit?', 'What is your primary motivation for joining this audit?', 'General', 'Medium', 1, 'text');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (50, 17, 'Explain a complex AI architectural decision you recently made.', 'Explain a complex AI architectural decision you recently made.', 'General', 'Medium', 1, 'audio');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (51, 3, 'What is RestApis?', 'What is RestApis?', 'Router', 'Medium', 5, 'text');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (52, NULL, 'Explain the difference between let, const, and var in JavaScript.', NULL, 'Dynamic', 'Unknown', 1, 'audio');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (53, NULL, 'How do you handle asynchronous operations in JavaScript?', NULL, 'Dynamic', 'Unknown', 1, 'audio');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (54, NULL, 'What are React hooks and why are they useful?', NULL, 'Dynamic', 'Unknown', 1, 'audio');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (55, NULL, 'Describe a challenging project you''ve worked on and how you overcame obstacles.', NULL, 'Dynamic', 'Unknown', 1, 'audio');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (56, NULL, 'How do you ensure code quality and maintainability in your projects?', NULL, 'Dynamic', 'Unknown', 1, 'audio');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (57, NULL, 'What is your approach to debugging complex issues?', NULL, 'Dynamic', 'Unknown', 1, 'audio');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (58, 19, 'What is Python?', 'What is Python?', 'General', 'Medium', 1, 'audio');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (59, 20, 'What is Python?', 'What is Python?', 'General', 'Medium', 1, 'audio');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (60, 21, 'What is Python?', 'What is Python?', 'General', 'Medium', 1, 'audio');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (61, 22, 'What is the purpose of testing?', 'What is the purpose of testing?', 'Testing|60', 'Medium', 1, 'audio');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (62, 22, 'Explain SDLC.', 'Explain SDLC.', 'SDLC|60', 'Medium', 1, 'audio');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (63, 3, 'What is Node.js?', 'What is Node.js?', 'Backend', 'Easy', 5, 'text');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (64, 3, 'How is Node.js different from browser JavaScript?', 'How is Node.js different from browser JavaScript?', 'Backend', 'Easy', 5, 'text');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (68, 3, 'You are getting memory leaks in production. What steps will you take?', 'You are getting memory leaks in production. What steps will you take?', 'Backend', 'Hard', 10, 'text');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (66, 3, 'What is CORS?', 'What is CORS?', 'Backend', 'Medium', 8, 'text');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (65, 3, 'What are the phases of the Event Loop?', 'What are the phases of the Event Loop?', 'Backend', 'Medium', 8, 'text');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (69, 3, 'What is the difference between microtasks and macrotasks?', 'What is the difference between microtasks and macrotasks?', 'Backend', 'Hard', 5, 'text');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (70, 4, 'What is a component?', 'What is a component?', 'Frontend', 'Easy', 5, 'text');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (71, 4, 'What are props?', 'What are props?', 'Frontend', 'Easy', 5, 'text');
INSERT INTO public.questions (id, paper_id, content, question_text, topic, difficulty, marks, response_type) VALUES (72, 23, 'What is polymorphism?', 'What is polymorphism?', 'OOP', 'Hard', 5, 'text');


--
-- Data for Name: answers; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.answers (id, interview_result_id, question_id, candidate_answer, feedback, score, audio_path, transcribed_text, "timestamp") VALUES (1, 1, 28, 'Tell me about yourself and your background in software development. 2 years', 'Evaluation service currently unavailable. Please check later.', 0, NULL, NULL, '2026-02-16 13:47:23.671478');
INSERT INTO public.answers (id, interview_result_id, question_id, candidate_answer, feedback, score, audio_path, transcribed_text, "timestamp") VALUES (2, 1, 28, 'Tell me about yourself and your background in software development. 2 years', 'Evaluation service currently unavailable. Please check later.', 0, NULL, NULL, '2026-02-16 13:48:33.923855');
INSERT INTO public.answers (id, interview_result_id, question_id, candidate_answer, feedback, score, audio_path, transcribed_text, "timestamp") VALUES (3, 1, 28, 'Tell me about yourself and your background in software development. 2 years', 'Evaluation service currently unavailable. Please check later.', 0, NULL, NULL, '2026-02-16 13:51:25.957882');
INSERT INTO public.answers (id, interview_result_id, question_id, candidate_answer, feedback, score, audio_path, transcribed_text, "timestamp") VALUES (4, 1, 29, 'Hi, I’m Saksham Garg. I’m a software developer with experience primarily in JavaScript-based technologies, especially working with Node.js, Next.js, and React.

In my recent work, I’ve been involved in building and maintaining dynamic web applications, handling complex forms, API integrations, and implementing state management using tools like Redux Toolkit. I’ve also worked on debugging production issues, refactoring legacy code, and improving validation logic in large-scale forms such as financial or investment-related systems.

I’m comfortable working with:

Frontend: React, Next.js, Redux Toolkit, JavaScript/TypeScript

Backend: Node.js

Version Control & Tools: Git, npm, Husky hooks

APIs: REST APIs and integration handling', 'Evaluation service currently unavailable. Please check later.', 0, NULL, NULL, '2026-02-16 13:52:17.939476');
INSERT INTO public.answers (id, interview_result_id, question_id, candidate_answer, feedback, score, audio_path, transcribed_text, "timestamp") VALUES (5, 2, 30, 'The full form of HTML is Hypertext Markup Language.', 'Evaluation service currently unavailable. Please check later.', 0, NULL, NULL, '2026-02-17 04:54:10.335349');
INSERT INTO public.answers (id, interview_result_id, question_id, candidate_answer, feedback, score, audio_path, transcribed_text, "timestamp") VALUES (6, 2, 31, 'Hypertext Markup Language', 'Evaluation service currently unavailable. Please check later.', 0, NULL, NULL, '2026-02-17 05:14:13.15533');
INSERT INTO public.answers (id, interview_result_id, question_id, candidate_answer, feedback, score, audio_path, transcribed_text, "timestamp") VALUES (7, 2, 32, 'Hypertext Markup language', 'Evaluation service currently unavailable. Please check later.', 0, NULL, NULL, '2026-02-17 05:21:10.53179');
INSERT INTO public.answers (id, interview_result_id, question_id, candidate_answer, feedback, score, audio_path, transcribed_text, "timestamp") VALUES (8, 2, 33, 'Hypertext Markup language', 'Evaluation service currently unavailable. Please check later.', 0, NULL, NULL, '2026-02-17 05:35:03.926947');
INSERT INTO public.answers (id, interview_result_id, question_id, candidate_answer, feedback, score, audio_path, transcribed_text, "timestamp") VALUES (9, 2, 34, 'string', 'Evaluation service currently unavailable. Please check later.', 0, NULL, NULL, '2026-02-17 05:35:04.042511');
INSERT INTO public.answers (id, interview_result_id, question_id, candidate_answer, feedback, score, audio_path, transcribed_text, "timestamp") VALUES (10, 2, 32, 'Hypertext Markup language', 'Evaluation service currently unavailable. Please check later.', 0, NULL, NULL, '2026-02-17 05:53:43.165796');
INSERT INTO public.answers (id, interview_result_id, question_id, candidate_answer, feedback, score, audio_path, transcribed_text, "timestamp") VALUES (11, 2, 35, 'Recursion is when a function calls itself to solve a smaller instance of the problem.', 'Evaluation service currently unavailable. Please check later.', 0, NULL, NULL, '2026-02-17 06:35:11.830415');
INSERT INTO public.answers (id, interview_result_id, question_id, candidate_answer, feedback, score, audio_path, transcribed_text, "timestamp") VALUES (12, 3, 39, 'Python is a programming language.', 'The answer is correct but lacks detail. It would be better to explain that Python is a high-level, interpreted programming language known for its readability and ease of use. Mentioning some of its key features like dynamic typing, automatic memory management, and a large standard library would also be beneficial.', 4.5, NULL, NULL, '2026-02-19 10:41:55.183749');
INSERT INTO public.answers (id, interview_result_id, question_id, candidate_answer, feedback, score, audio_path, transcribed_text, "timestamp") VALUES (14, 5, 49, 'Testing the audio flow performance on cloud.', 'The candidate''s answer seems to be off-topic. The question was about their motivation for joining the audit team, not about testing audio flow performance on cloud. They should have provided reasons related to their interest in auditing, such as improving their skills, contributing to the security of systems, or gaining experience in a specific area of auditing.', 3.5, NULL, NULL, '2026-02-19 12:03:19.152159');
INSERT INTO public.answers (id, interview_result_id, question_id, candidate_answer, feedback, score, audio_path, transcribed_text, "timestamp") VALUES (15, 5, 50, 'Successfully completed the candidate flow audit.', 'The candidate''s response does not address the question about a complex AI architectural decision. Instead, it mentions a candidate flow audit, which is unrelated. The answer lacks detail and context about the architectural decision and its rationale. The candidate should provide specific examples and explain the reasoning behind the decision.', 2.5, NULL, NULL, '2026-02-19 12:03:40.176759');
INSERT INTO public.answers (id, interview_result_id, question_id, candidate_answer, feedback, score, audio_path, transcribed_text, "timestamp") VALUES (16, 1, 28, 'Tell me about yourself and your background in software development. ', 'The candidate started the answer by repeating the question, which is not ideal as it shows a lack of preparation or engagement. It would have been better to provide a concise and relevant response about their background and experience in software development. The candidate should practice summarizing their relevant skills and experiences without needing to restate the question.', 3.5, NULL, NULL, '2026-02-20 05:09:23.345107');
INSERT INTO public.answers (id, interview_result_id, question_id, candidate_answer, feedback, score, audio_path, transcribed_text, "timestamp") VALUES (17, 1, 28, 'My name is Tushar.A student of chitkara university pursuing final year in B tech cse. ', 'The candidate''s answer is brief and lacks depth. It would be more beneficial if the candidate provided specific examples of projects they have worked on, their experience with different programming languages, and any relevant coursework or certifications. This would give a clearer picture of their skills and background in software development.', 4.5, NULL, NULL, '2026-02-20 05:20:01.59831');
INSERT INTO public.answers (id, interview_result_id, question_id, candidate_answer, feedback, score, audio_path, transcribed_text, "timestamp") VALUES (18, 1, 29, 'I learned about javascript from w3schools and made industry level rojects', 'The candidate mentions learning JavaScript from W3Schools, which is a basic resource, but does not provide any details about their experience with modern web frameworks. They also mention working on industry-level projects, but do not specify the technologies used. It would be more helpful if the candidate could elaborate on their experience with specific frameworks like React, Angular, or Vue, and provide examples of projects they have worked on using these technologies.', 4.5, NULL, NULL, '2026-02-20 05:20:46.953802');
INSERT INTO public.answers (id, interview_result_id, question_id, candidate_answer, feedback, score, audio_path, transcribed_text, "timestamp") VALUES (19, 1, 52, 'let is used for variable declaration and const i dont know', 'The candidate correctly identified that let is used for variable declaration but is incorrect about const. const is used for declaring constants and the value cannot be changed after initialization. The candidate should also mention that var is function scoped, let and const are block scoped, and let allows for reassignment while const does not. Suggest reviewing the differences between these three keywords in JavaScript.', 4.5, NULL, NULL, '2026-02-20 05:21:33.375286');
INSERT INTO public.answers (id, interview_result_id, question_id, candidate_answer, feedback, score, audio_path, transcribed_text, "timestamp") VALUES (20, 1, 53, 'i have not done this in my college time', 'It''s important to demonstrate knowledge of asynchronous operations in JavaScript, especially since it''s a core concept in modern web development. Consider explaining the use of Promises, async/await, or callbacks to show your understanding of handling asynchronous operations.', 2.5, NULL, NULL, '2026-02-20 05:22:09.91254');
INSERT INTO public.answers (id, interview_result_id, question_id, candidate_answer, feedback, score, audio_path, transcribed_text, "timestamp") VALUES (21, 1, 54, 'Hooks are hooks', 'The candidate''s answer is incomplete and lacks detail. They should provide a more comprehensive explanation of what React hooks are and their primary benefits. For example, they could mention that hooks allow you to use state and other React features without writing a class, and they can make the code more functional and reusable.', 2.5, NULL, NULL, '2026-02-20 05:22:35.571306');
INSERT INTO public.answers (id, interview_result_id, question_id, candidate_answer, feedback, score, audio_path, transcribed_text, "timestamp") VALUES (22, 1, 55, 'I made an IOS application and challenges faced was like- we lacked team work ', 'The candidate''s answer is brief and lacks detail. It would be more helpful if the candidate could provide specific examples of challenges faced, how they were overcome, and the impact of their solutions. Additionally, mentioning teamwork issues is a start, but the candidate could elaborate on how they addressed these issues, such as by improving communication or restructuring the team.', 4.5, NULL, NULL, '2026-02-20 05:23:26.19205');
INSERT INTO public.answers (id, interview_result_id, question_id, candidate_answer, feedback, score, audio_path, transcribed_text, "timestamp") VALUES (23, 1, 56, 'using github', 'The candidate''s answer is too brief and does not provide a comprehensive explanation of how to ensure code quality and maintainability. Suggesting GitHub is just one aspect of code management and does not cover other important practices such as code reviews, unit testing, documentation, and adherence to coding standards. The answer could be improved by elaborating on these practices and how they contribute to code quality and maintainability.', 2.5, NULL, NULL, '2026-02-20 05:23:45.346733');
INSERT INTO public.answers (id, interview_result_id, question_id, candidate_answer, feedback, score, audio_path, transcribed_text, "timestamp") VALUES (24, 1, 57, 'i use AI agents for that', 'While using AI agents can be a part of your debugging strategy, it''s important to provide a more detailed explanation of your approach. Consider discussing your step-by-step process, tools you use, and how you integrate AI into your workflow. This would give a clearer picture of your debugging skills and problem-solving abilities.', 6.5, NULL, NULL, '2026-02-20 05:24:06.7074');
INSERT INTO public.answers (id, interview_result_id, question_id, candidate_answer, feedback, score, audio_path, transcribed_text, "timestamp") VALUES (26, 1, 28, 'Tell me about yourself and your background in software development. ', 'The candidate started the answer by repeating the question, which is not ideal as it shows a lack of preparation or engagement. They should have directly addressed the question with relevant information about their background and experience in software development. It''s important to provide a concise and relevant response that highlights key skills and experiences.', 3.5, NULL, NULL, '2026-02-20 13:29:19.383279');
INSERT INTO public.answers (id, interview_result_id, question_id, candidate_answer, feedback, score, audio_path, transcribed_text, "timestamp") VALUES (27, 1, 28, 'Tell me about yourself and your background in software development. 2 years of experience', 'The candidate''s response was too brief and lacked detail. It''s important to provide a more comprehensive overview of your background, including specific projects, technologies used, and key achievements. This would give the interviewer a better understanding of your skills and experience.', 2.5, NULL, NULL, '2026-02-20 13:30:59.276174');
INSERT INTO public.answers (id, interview_result_id, question_id, candidate_answer, feedback, score, audio_path, transcribed_text, "timestamp") VALUES (28, 7, 1, 'Hooks.', '{
  "feedback": "The candidate''s answer is incomplete and does not provide any meaningful explanation of what hooks are in React. A more detailed response would include that hooks are functions that let you "use state", "use effects", and other React features in functional components, which were previously only available in class components. The candidate should also mention that hooks must be called only from the top-level of a functional component and not inside loops, conditions, or nested functions.",
  "score": 2.0
}', 5, 'app/assets/audio/responses/resp_47_1_59682ea1.wav', 'Hooks.', '2026-02-23 12:05:19.892737');
INSERT INTO public.answers (id, interview_result_id, question_id, candidate_answer, feedback, score, audio_path, transcribed_text, "timestamp") VALUES (29, 7, 2, 'No idea.', 'The candidate clearly lacks knowledge about React hooks, which are a fundamental part of the library. It''s important to have a basic understanding of hooks to work effectively with React. Suggest reviewing the official React documentation on hooks to gain a foundational knowledge.', 2, 'app/assets/audio/responses/resp_47_2_fdeabe42.wav', 'No idea.', '2026-02-23 12:05:35.440816');
INSERT INTO public.answers (id, interview_result_id, question_id, candidate_answer, feedback, score, audio_path, transcribed_text, "timestamp") VALUES (30, 7, 3, 'The question is difference between lists and duples.', 'The candidate''s answer is incorrect and does not address the question about hooks in ReactJS. Instead, the candidate mentioned the difference between lists and tuples, which are unrelated concepts. The candidate should be asked to provide a correct definition and explanation of hooks in ReactJS, including their purpose and some common examples like useState and useEffect.', 2, 'app/assets/audio/responses/resp_47_3_1bc534f9.wav', 'The question is difference between lists and duples.', '2026-02-23 12:05:52.868019');
INSERT INTO public.answers (id, interview_result_id, question_id, candidate_answer, feedback, score, audio_path, transcribed_text, "timestamp") VALUES (35, 10, 5, 'I don''t know.', 'It''s important to have a foundational understanding of JWT (JSON Web Tokens) in the context of Node.js, as it''s a common authentication mechanism. You could have explained that JWT is a compact, URL-safe means of representing claims to be transferred between two parties. In Node.js, you can use libraries like `jsonwebtoken` to work with JWTs. Mentioning this would have shown your familiarity with the topic and its practical application.', 2.5, 'app/assets/audio/responses/resp_53_5_8b456ee4.wav', 'I don''t know.', '2026-02-24 04:26:25.568253');
INSERT INTO public.answers (id, interview_result_id, question_id, candidate_answer, feedback, score, audio_path, transcribed_text, "timestamp") VALUES (34, 10, 4, 'I don''t know.', 'It''s important to have a basic understanding of JWT (JSON Web Tokens) when working with Node.js, as it''s a common method for handling authentication and authorization. You should have mentioned that JWT is a compact, URL-safe means of representing claims to be transferred between two parties. In Node.js, you can use libraries like `jsonwebtoken` to create, sign, and verify JWTs. This would have shown that you have at least some familiarity with the topic.', 3, 'app/assets/audio/responses/resp_53_4_02d4417d.wav', 'I don''t know.', '2026-02-24 04:26:15.124072');
INSERT INTO public.answers (id, interview_result_id, question_id, candidate_answer, feedback, score, audio_path, transcribed_text, "timestamp") VALUES (36, 10, 6, 'Gracias.', 'The candidate''s response is brief and does not provide any meaningful information about JWT (JSON Web Token) in Node.js. A more detailed explanation would be expected, including what JWT is, its purpose, and how it is used in Node.js applications. The response should also include examples or code snippets if possible.', 2, 'app/assets/audio/responses/resp_53_6_fa617741.wav', 'Gracias.', '2026-02-24 04:26:39.324577');
INSERT INTO public.answers (id, interview_result_id, question_id, candidate_answer, feedback, score, audio_path, transcribed_text, "timestamp") VALUES (38, 11, 5, 'No, no, no.', 'The candidate''s answer is not helpful or informative. They should provide a clear explanation of what JWT (JSON Web Token) is and how it is used in Node.js applications, including key concepts like signing, verification, and its role in authentication and authorization.', 2, 'app/assets/audio/responses/resp_54_5_9601becd.wav', 'No, no, no.', '2026-02-24 04:31:47.436961');
INSERT INTO public.answers (id, interview_result_id, question_id, candidate_answer, feedback, score, audio_path, transcribed_text, "timestamp") VALUES (37, 11, 4, 'Jason Webb, Don''t call me.', 'The candidate''s answer is not relevant to the question. They provided a name instead of explaining what JWT (JSON Web Token) is in the context of Node.js. It''s important to provide accurate and relevant information when answering technical questions.', 2, 'app/assets/audio/responses/resp_54_4_ceb69bf7.wav', 'Jason Webb, Don''t call me.', '2026-02-24 04:31:33.029954');
INSERT INTO public.answers (id, interview_result_id, question_id, candidate_answer, feedback, score, audio_path, transcribed_text, "timestamp") VALUES (39, 11, 6, 'Hypertext Markup Language.', 'The candidate''s answer is incorrect. JWT stands for JSON Web Token, not Hypertext Markup Language. They should have explained that JWT is a compact, URL-safe means of representing claims to be transferred between two parties. In Node.js, JWT is often used for authentication and authorization. The candidate should be able to explain the basic concept and usage of JWT in a Node.js application.', 2, 'app/assets/audio/responses/resp_54_6_bad0f2ee.wav', 'Hypertext Markup Language.', '2026-02-24 04:32:02.220986');
INSERT INTO public.answers (id, interview_result_id, question_id, candidate_answer, feedback, score, audio_path, transcribed_text, "timestamp") VALUES (40, 12, 4, 'JSON Web Token.', 'The candidate correctly identified JWT but did not provide any context or explanation of how JWT is used in Node.js applications. It would be beneficial to explain the purpose of JWT and how it can be implemented in a Node.js environment, including any relevant libraries or frameworks.', 3.5, 'app/assets/audio/responses/resp_56_4_0188a9a1.wav', 'JSON Web Token.', '2026-02-24 04:35:05.456355');
INSERT INTO public.answers (id, interview_result_id, question_id, candidate_answer, feedback, score, audio_path, transcribed_text, "timestamp") VALUES (41, 12, 5, 'Obrigado.', 'The candidate''s response is not relevant to the question. They provided a word that does not answer the question about JWT in Node.js. It''s important to provide a clear and accurate explanation of the topic. Suggested improvements include explaining what JWT is and how it can be used in a Node.js application.', 2, 'app/assets/audio/responses/resp_56_5_10f0c6c9.wav', 'Obrigado.', '2026-02-24 04:35:20.533343');
INSERT INTO public.answers (id, interview_result_id, question_id, candidate_answer, feedback, score, audio_path, transcribed_text, "timestamp") VALUES (42, 12, 6, 'I don''t know.', 'It''s important to have a foundational understanding of JWT (JSON Web Tokens) in the context of Node.js. You could have explained that JWT is a compact, URL-safe means of representing claims to be transferred between two parties. In Node.js, you can use libraries like `jsonwebtoken` to create, sign, and verify JWTs. This is commonly used for authentication and authorization in web applications.', 2.5, 'app/assets/audio/responses/resp_56_6_cbbb10b5.wav', 'I don''t know.', '2026-02-24 04:35:31.63989');


--
-- Data for Name: interviewresponse; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.interviewresponse (id, interview_id, question_id, audio_path, transcribed_text, similarity_score, answer_text, evaluation_text, score, "timestamp") VALUES (1, 2, 4, NULL, NULL, NULL, 'answer 4', 'Evaluation service currently unavailable. Please check later.', 0, '2026-02-14 13:55:10.008823');
INSERT INTO public.interviewresponse (id, interview_id, question_id, audio_path, transcribed_text, similarity_score, answer_text, evaluation_text, score, "timestamp") VALUES (2, 2, 5, NULL, NULL, NULL, 'answer 5', 'Evaluation service currently unavailable. Please check later.', 0, '2026-02-14 13:55:21.094971');
INSERT INTO public.interviewresponse (id, interview_id, question_id, audio_path, transcribed_text, similarity_score, answer_text, evaluation_text, score, "timestamp") VALUES (3, 2, 6, NULL, NULL, NULL, 'answer 6', 'Evaluation service currently unavailable. Please check later.', 0, '2026-02-14 13:55:36.055531');


--
-- Data for Name: proctoringevent; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: sessionquestion; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (1, 1, 3, 0);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (2, 1, 1, 1);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (3, 1, 2, 2);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (162, 64, 1, 0);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (163, 64, 3, 1);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (164, 64, 2, 2);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (165, 65, 1, 0);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (94, 39, 1, 0);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (166, 65, 2, 1);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (95, 39, 2, 1);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (96, 39, 3, 2);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (167, 65, 3, 2);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (168, 66, 1, 0);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (17, 6, 5, 0);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (18, 6, 4, 1);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (19, 7, 39, 0);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (20, 7, 40, 1);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (21, 8, 41, 0);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (22, 8, 42, 1);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (23, 9, 43, 0);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (24, 9, 44, 1);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (25, 10, 45, 0);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (26, 10, 46, 1);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (169, 66, 2, 1);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (170, 66, 3, 2);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (29, 12, 49, 0);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (30, 12, 50, 1);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (171, 67, 1, 0);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (172, 67, 2, 1);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (33, 14, 58, 0);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (34, 15, 59, 0);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (173, 67, 3, 2);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (177, 69, 1, 0);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (178, 69, 2, 1);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (179, 69, 3, 2);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (180, 70, 70, 0);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (181, 70, 71, 1);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (182, 70, 20, 2);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (109, 44, 1, 0);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (110, 44, 2, 1);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (111, 44, 3, 2);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (118, 47, 1, 0);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (119, 47, 2, 1);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (120, 47, 3, 2);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (135, 53, 4, 0);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (136, 53, 5, 1);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (137, 53, 6, 2);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (138, 54, 4, 0);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (139, 54, 5, 1);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (140, 54, 6, 2);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (144, 56, 4, 0);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (145, 56, 5, 1);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (146, 56, 6, 2);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (150, 59, 2, 0);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (151, 59, 1, 1);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (152, 60, 1, 0);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (153, 60, 3, 1);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (154, 61, 3, 0);
INSERT INTO public.sessionquestion (id, interview_id, question_id, sort_order) VALUES (155, 61, 1, 1);


--
-- Data for Name: statustimeline; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (1, 1, 'INVITED', '2026-02-14 11:26:50.561176', '{"admin_id": 1, "candidate_id": 7, "email_sent": true}');
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (2, 1, 'LINK_ACCESSED', '2026-02-14 12:21:11.221989', NULL);
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (3, 1, 'INTERVIEW_COMPLETED', '2026-02-14 12:24:32.780659', '{"completed_at": "2026-02-14T12:24:32.780645+00:00"}');
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (4, 2, 'INVITED', '2026-02-14 13:15:36.144131', '{"admin_id": 5, "candidate_id": 7, "email_sent": true}');
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (5, 2, 'LINK_ACCESSED', '2026-02-14 13:28:41.433343', NULL);
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (6, 2, 'INTERVIEW_COMPLETED', '2026-02-14 13:55:57.695793', '{"completed_at": "2026-02-14T13:55:57.695777+00:00"}');
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (9, 5, 'INVITED', '2026-02-17 09:36:36.138434', '{"admin_id": 1, "candidate_id": 7, "email_sent": true}');
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (10, 6, 'INVITED', '2026-02-17 09:36:48.372007', '{"admin_id": 1, "candidate_id": 7, "email_sent": true}');
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (11, 7, 'INVITED', '2026-02-19 10:30:58.545561', '{"admin_id": 1, "candidate_id": 11, "email_sent": true}');
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (12, 7, 'LINK_ACCESSED', '2026-02-19 10:31:00.676594', NULL);
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (13, 7, 'ENROLLMENT_STARTED', '2026-02-19 10:31:01.028205', NULL);
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (14, 7, 'ENROLLMENT_COMPLETED', '2026-02-19 10:31:01.058299', NULL);
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (15, 7, 'INTERVIEW_ACTIVE', '2026-02-19 10:31:01.419877', NULL);
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (16, 8, 'INVITED', '2026-02-19 10:36:21.773088', '{"admin_id": 1, "candidate_id": 12, "email_sent": true}');
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (17, 8, 'LINK_ACCESSED', '2026-02-19 10:36:23.834788', NULL);
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (18, 8, 'ENROLLMENT_STARTED', '2026-02-19 10:36:24.18017', NULL);
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (19, 8, 'ENROLLMENT_COMPLETED', '2026-02-19 10:36:24.202565', NULL);
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (20, 8, 'INTERVIEW_ACTIVE', '2026-02-19 10:36:24.555313', NULL);
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (21, 9, 'INVITED', '2026-02-19 10:39:25.919334', '{"admin_id": 1, "candidate_id": 13, "email_sent": true}');
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (22, 9, 'LINK_ACCESSED', '2026-02-19 10:39:28.069484', NULL);
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (23, 9, 'ENROLLMENT_STARTED', '2026-02-19 10:39:28.457324', NULL);
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (24, 9, 'ENROLLMENT_COMPLETED', '2026-02-19 10:39:28.487108', NULL);
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (25, 9, 'INTERVIEW_ACTIVE', '2026-02-19 10:39:28.857055', NULL);
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (26, 10, 'INVITED', '2026-02-19 10:45:08.901725', '{"admin_id": 1, "candidate_id": 14, "email_sent": true}');
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (27, 10, 'LINK_ACCESSED', '2026-02-19 10:45:11.005286', NULL);
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (28, 10, 'ENROLLMENT_STARTED', '2026-02-19 10:45:11.354436', NULL);
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (29, 10, 'ENROLLMENT_COMPLETED', '2026-02-19 10:45:11.378132', NULL);
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (30, 10, 'INTERVIEW_ACTIVE', '2026-02-19 10:45:11.735347', NULL);
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (37, 12, 'INVITED', '2026-02-19 11:59:35.852121', '{"admin_id": 1, "candidate_id": 16, "email_sent": true}');
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (38, 12, 'INTERVIEW_COMPLETED', '2026-02-19 12:03:41.686251', '{"completed_at": "2026-02-19T12:03:41.686233+00:00"}');
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (40, 14, 'INVITED', '2026-02-20 05:57:48.606132', '{"admin_id": 1, "candidate_id": 18, "email_sent": true}');
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (41, 15, 'INVITED', '2026-02-20 05:58:11.928217', '{"admin_id": 1, "candidate_id": 19, "email_sent": true}');
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (66, 39, 'INVITED', '2026-02-23 08:41:06.526733', '{"admin_id": 1, "candidate_id": 23, "email_sent": true}');
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (72, 44, 'INVITED', '2026-02-23 10:49:09.477483', '{"admin_id": 1, "candidate_id": 26, "email_sent": true}');
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (73, 44, 'LINK_ACCESSED', '2026-02-23 10:59:59.680997', NULL);
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (78, 47, 'INVITED', '2026-02-23 12:04:28.645345', '{"admin_id": 1, "candidate_id": 24, "email_sent": true}');
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (79, 47, 'INTERVIEW_COMPLETED', '2026-02-23 12:05:54.298504', '{"completed_at": "2026-02-23T12:05:54.298477+00:00"}');
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (88, 53, 'INVITED', '2026-02-24 04:25:11.521164', '{"admin_id": 1, "candidate_id": 25, "email_sent": true}');
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (89, 53, 'INTERVIEW_COMPLETED', '2026-02-24 04:26:40.998003', '{"completed_at": "2026-02-24T04:26:40.997985+00:00"}');
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (90, 54, 'INVITED', '2026-02-24 04:30:52.851808', '{"admin_id": 1, "candidate_id": 25, "email_sent": true}');
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (91, 54, 'LINK_ACCESSED', '2026-02-24 04:31:05.970104', NULL);
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (92, 54, 'INTERVIEW_COMPLETED', '2026-02-24 04:32:03.544811', '{"completed_at": "2026-02-24T04:32:03.544784+00:00"}');
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (95, 56, 'INVITED', '2026-02-24 04:33:59.226515', '{"admin_id": 1, "candidate_id": 25, "email_sent": true}');
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (96, 56, 'INTERVIEW_COMPLETED', '2026-02-24 04:35:32.733615', '{"completed_at": "2026-02-24T04:35:32.733594+00:00"}');
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (99, 58, 'INVITED', '2026-02-24 10:37:33.205052', '{"admin_id": 1, "candidate_id": 23, "email_sent": true}');
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (100, 59, 'INVITED', '2026-02-24 10:55:11.189456', '{"admin_id": 1, "candidate_id": 23, "email_sent": true}');
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (101, 60, 'INVITED', '2026-02-24 11:51:11.529972', '{"admin_id": 1, "candidate_id": 23, "email_sent": true}');
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (102, 61, 'INVITED', '2026-02-24 12:10:02.624883', '{"admin_id": 1, "candidate_id": 23, "email_sent": true}');
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (107, 64, 'INVITED', '2026-02-25 09:08:20.566454', '{"admin_id": 1, "candidate_id": 23, "email_sent": true}');
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (108, 65, 'INVITED', '2026-02-25 10:17:57.189582', '{"admin_id": 1, "candidate_id": 32, "email_sent": true}');
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (109, 66, 'INVITED', '2026-02-25 10:18:51.910361', '{"admin_id": 1, "candidate_id": 32, "email_sent": true}');
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (110, 66, 'LINK_ACCESSED', '2026-02-25 10:18:55.971631', NULL);
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (111, 67, 'INVITED', '2026-02-25 10:21:08.326569', '{"admin_id": 1, "candidate_id": 32, "email_sent": true}');
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (112, 67, 'LINK_ACCESSED', '2026-02-25 10:21:12.398697', NULL);
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (115, 69, 'INVITED', '2026-02-25 11:19:09.769364', '{"admin_id": 1, "candidate_id": 32, "email_sent": true}');
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (116, 70, 'INVITED', '2026-02-25 17:07:08.283273', '{"admin_id": 5, "candidate_id": 7, "email_sent": true}');
INSERT INTO public.statustimeline (id, interview_id, status, "timestamp", context_data) VALUES (117, 70, 'LINK_ACCESSED', '2026-02-25 17:08:12.878093', NULL);


--
-- Name: answers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.answers_id_seq', 42, true);


--
-- Name: interviewresponse_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.interviewresponse_id_seq', 3, true);


--
-- Name: interviewresult_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.interviewresult_id_seq', 12, true);


--
-- Name: interviewsession_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.interviewsession_id_seq', 70, true);


--
-- Name: proctoringevent_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.proctoringevent_id_seq', 1, false);


--
-- Name: questionpaper_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.questionpaper_id_seq', 24, true);


--
-- Name: questions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.questions_id_seq', 73, true);


--
-- Name: sessionquestion_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.sessionquestion_id_seq', 182, true);


--
-- Name: statustimeline_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.statustimeline_id_seq', 117, true);


--
-- Name: user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.user_id_seq', 33, true);


--
-- PostgreSQL database dump complete
--

\unrestrict iHxUCaMZrYfkc5TAbyqawDVbiWbCWdbiR2OgseZcleBxnUrZZhwTn1tDTKDXMXL

