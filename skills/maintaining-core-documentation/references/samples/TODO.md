# Project Roadmap & Backlog: dazbo-portfolio

## In Progress

- [~] Add semantic vector search (`gemini-embedding-2` + Firestore vector index) to complement keyword ranking in `search_portfolio`

## Planned Backlog

- [ ] Automate static asset scraping and upload into GCS during blog ingestion
- [ ] Add multi-environment staging promotion workflow in Cloud Build
- [ ] Expand ADK evaluation golden dataset for multi-turn portfolio queries

## Completed

- [x] Implement hybrid SSR/SPA SEO metadata injection and dynamic `/sitemap.xml` (2026-09-18)
- [x] Enforce multi-tier `slowapi` rate limiting on `/api` and `/api/chat/stream` (2026-09-10)
- [x] Build unified React + FastAPI container deployment with Terraform and Cloud Build (2026-08-29)
- [x] Launch multi-source ingestion CLI for GitHub, Medium, Dev.to, and manual YAML (2026-08-22)
