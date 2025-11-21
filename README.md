# TripWeaver — polyglot JFrog-ready demo

## Overview

This repository is a minimal, production-shaped polyglot demo application designed to be wired into JFrog tooling later. It contains:

- **frontend/** — Next.js (React) frontend with a single natural-language query box
- **api/** — FastAPI Python backend exposing POST /itinerary/plan
- **tools/seedgen/** — .NET 8 CLI that reads data/destinations.csv and writes data/index.json
- **data/** — source CSV and generated JSON index
- **charts/** — Helm umbrella chart for deployment
- **infra/** — simple Kubernetes manifests for local kind testing

## Getting started (quick)

1. Generate data index:
   ```bash
   make seed
   ```
2. Build images:
   ```bash
   make build
   ```
3. Run locally with docker-compose:
   ```bash
   make up
   ```
4. Test (runs unit tests):
   ```bash
   make test
   ```
5. Generate SBOMs and (stub) sign images:
   ```bash
   make sbom && make sign
   ```

See `DEMO.md` for a step-by-step demo script.

---
