-- CARCH single-Supabase schema split.
-- Run with an owner/admin connection in Supabase SQL Editor.
-- Keep application schemas private to the backend; do not expose demo/service via Data API.

create schema if not exists catalog;
create schema if not exists demo;
create schema if not exists service;

-- Runtime search paths:
-- demo backend:    demo,catalog
-- service backend: service,catalog

-- Card catalog lives in catalog and is shared by demo/service.
-- Existing public catalog tables can be copied once with:
--
-- create table catalog.cards (like public.cards including all);
-- insert into catalog.cards select * from public.cards;
-- create table catalog.card_benefits (like public.card_benefits including all);
-- insert into catalog.card_benefits select * from public.card_benefits;

-- Demo schema keeps presentation data.
-- Service schema keeps the same table structure but no user/application data.
-- Django metadata tables in service may contain django_migrations,
-- django_content_type, and auth_permission rows; user data tables must remain empty.
