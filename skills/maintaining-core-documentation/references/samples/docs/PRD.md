---
type: "Product Requirements"
title: "Dazbo Portfolio — Product Requirements"
description: "Product vision, target personas, success metrics, user stories, and explicit non-goals for the Dazbo Portfolio platform."
status: "stable"
---

# Product Requirements: dazbo-portfolio

## Executive Summary & Vision

`dazbo-portfolio` is a personal technical showcase and living reference application. It brings together published technical articles, software projects, live applications, and career highlights under a single curated experience, augmented by an interactive AI assistant that helps visitors explore relevant work conversationally rather than trawling fragmented links.

## Problem Statement

Technical writing and engineering output are scattered across multiple platforms (GitHub, Medium, Dev.to, YouTube, and standalone demos). Each platform exposes partial feeds, inconsistent metadata, and different search experiences:

- Visitors and recruiters cannot quickly discover all relevant work by topic or skill area in one place.
- Single Page Applications often degrade search-engine indexing and social preview cards when served without metadata injection.
- Manually re-publishing summaries and cross-links across sites creates constant maintenance drift.

## Target Users & Personas

| Persona | Context | Core Need |
| :--- | :--- | :--- |
| **Hiring Manager / Technical Recruiter** | Reviewing a candidate's track record within a 3–5 minute window | Rapidly verify depth across cloud, AI, and architecture via curated summaries and live demos |
| **Fellow Cloud / AI Engineer** | Discovering a blog post or open-source repo via search or social link | Read clean previews, inspect architectural patterns, and ask targeted follow-up questions |
| **Site Owner (Dazbo)** | Publishing new blogs, videos, and repos frequently | Synchronise new content automatically with minimal manual curation and predictable LLM spend |

## Goals & Success Metrics

| Goal | Metric / Signal | Target |
| :--- | :--- | :--- |
| **Unified Content Discovery** | Percentage of public blogs and featured repos searchable in one portal | 100% of active GitHub, Medium, Dev.to, and curated YAML items |
| **Search & Social Visibility** | Valid Open Graph / meta tags returned on initial route HTML | All primary portfolio routes render route-specific metadata before JS execution |
| **Conversational Assistance** | Relevance and factual grounding of assistant answers | Assistant cites only ingested portfolio items and never fabricates project URLs |
| **Controlled Operating Cost** | Monthly serverless and LLM token spend for a personal site | Scales to zero when idle; chat endpoint protected against automated abuse |

## Feature Scope

### MVP (In Scope)

- **Curated Portfolio Browsing**: Browse and filter projects, applications, technical articles, and experience highlights.
- **Interactive AI Portfolio Assistant**: Conversational Q&A grounded in ingested portfolio records with direct links to source articles and repositories.
- **Automated Content Aggregation**: Scheduled or on-demand synchronisation from GitHub, Medium (RSS + full history archive), Dev.to, and curated manual entries, enriched with concise AI summaries and tags.
- **Search-Friendly Routing**: Route-aware metadata injection and sitemap support so shared links render rich social previews.

### Future Roadmap

- **Semantic Search**: Concept-based discovery beyond exact keyword matching when visitors ask open-ended topical questions.
- **Automated Media Mirroring**: Automatic capture and caching of external project thumbnails.

## Core User Stories & Outcomes

1. **Topic Discovery**: As a **Fellow Cloud Engineer**, I want to ask the assistant *"What have you written about Gemini agents?"* so that I immediately receive concise summaries and direct links without clicking through dozens of pages.
2. **Executive Assessment**: As a **Hiring Manager**, I want to filter featured applications and read clean summaries of complex systems so that I can assess architectural breadth in minutes.
3. **Low-Friction Publishing**: As the **Site Owner**, I want newly published Medium or Dev.to articles to be imported, deduplicated, and summarised cleanly so that the portfolio stays current without manual HTML editing.

## Non-Goals (Out of Scope & Why)

- **Custom Web CMS / Admin Dashboard** — Content creation happens on native platforms (GitHub, Medium, Dev.to) or in version-controlled YAML; building an authenticated web editor adds unnecessary attack surface and maintenance overhead.
- **Visitor Accounts, Comments, or Auth Flows** — The portfolio is a public read-and-chat experience; omitting user registration keeps the site stateless and frictionless.
- **Multi-Tenant SaaS Hosting** — Designed as a clean single-owner reference implementation that others can fork, not a hosted multi-user SaaS product.

## Assumptions, Risks & Open Questions

- **Assumption**: External RSS and developer APIs (GitHub, Dev.to, Medium archive exports) remain sufficient sources of truth for article metadata and full text.
- **Risk & Mitigation**: Public chat endpoints expose LLM token usage to abuse; mitigated through strict per-client request throttling and non-destructive read-only agent tools.
- **Open Question**: Should vector-based semantic retrieval replace or complement tiered keyword ranking once the corpus exceeds 250 articles?
