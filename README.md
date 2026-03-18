# particle-connect

A Python SDK, analytics pipeline, and admin UI for integrating with the [Particle Health](https://www.particlehealth.com/) nationwide health information exchange (HIE). Query clinical records (CCDA, FHIR R4, flat JSON) across thousands of EHR sources with a single API call — covering patient registration, clinical data retrieval, real-time ADT event subscriptions (Signal), and credential management.

This repository accelerates EHR integration and health data interoperability work by providing practical starting points (sample workflows, utilities, and scaffolding) for the Particle Health API. You are free to adapt these materials to your environment and requirements.

## Start Here

Pick the path that matches what you're trying to do:

| I want to... | Go here | Time to first result |
|---|---|---|
| **Pull clinical records** for a patient | [`particle-api-quickstarts/`](particle-api-quickstarts/) | ~10 min setup + 2-5 min query |
| **Explore sample data** without any credentials | [`particle-api-quickstarts/notebooks/`](particle-api-quickstarts/notebooks/) | ~2 min |
| **Load flat data into SQL** and run analytics | [`particle-analytics-quickstarts/`](particle-analytics-quickstarts/) | ~5 min (single command) |
| **Manage projects & credentials** via UI | [`management-ui/`](management-ui/) | ~3 min (docker compose up) |
| **See the raw API calls** (curl/httpx, no SDK) | [`particle-api-quickstarts/quick-starts/`](particle-api-quickstarts/quick-starts/) | ~5 min |
| **Set up Signal/ADT webhooks** | [`particle-api-quickstarts/workflows/signal_end_to_end.py`](particle-api-quickstarts/workflows/signal_end_to_end.py) | ~10 min |

### If you're brand new to Particle

1. **No credentials yet?** Open the [sample data notebook](particle-api-quickstarts/notebooks/explore_flat_data.ipynb) — zero setup, see real clinical data shapes immediately
2. **Have credentials?** Run [`workflows/check_setup.py`](particle-api-quickstarts/workflows/check_setup.py) to validate, then [`workflows/hello_particle.py`](particle-api-quickstarts/workflows/hello_particle.py) for a full end-to-end demo
3. **Have flat data and want to query it?** Run `particle-pipeline` in [`particle-analytics-quickstarts/`](particle-analytics-quickstarts/) — one command loads everything into DuckDB

### What's in each sub-project

```
particle-connect/
├── particle-api-quickstarts/        # Python SDK + workflows + quick-starts
│   ├── src/particle/                #   Installable SDK (auth, patient, query, document, signal)
│   ├── workflows/                   #   Production-like reference scripts (start with hello_particle.py)
│   ├── quick-starts/                #   Minimal curl + httpx examples (no SDK needed)
│   ├── notebooks/                   #   Jupyter notebook for exploring sample data
│   └── sample-data/                 #   Flat JSON + CCDA samples (no credentials needed)
│
├── particle-analytics-quickstarts/  # Load flat data → DuckDB/BigQuery + 15 pre-built SQL queries
│   ├── src/observatory/             #   CLI pipeline tool
│   ├── queries/                     #   Clinical, operational, and cross-cutting SQL queries
│   ├── ddl/                         #   Table definitions (DuckDB, PostgreSQL, BigQuery)
│   └── terraform/                   #   BigQuery infrastructure-as-code (optional)
│
├── management-ui/                   # Browser-based admin for projects, service accounts, credentials
│   ├── frontend/                    #   React 19 + TypeScript
│   └── backend/                     #   FastAPI proxy to Particle Management API
│
└── agent-documentation/             # AI-agent-friendly docs (llms.txt standard)
```

## AI Agent-Friendly Documentation

This repository includes agent-friendly documentation designed to help both engineers and AI agents understand, navigate, and work with the codebase safely. It provides clear setup instructions, repository structure, workflow guidance, and implementation examples to reduce ambiguity and accelerate time to value.

The documentation lives in [`agent-documentation/`](agent-documentation/) and follows the [llms.txt](https://llmstxt.org/) standard. The entry point is [`agent-documentation/llms.txt`](agent-documentation/llms.txt) — a lightweight index that tells an agent which file to read for any given task.

### Setting up your AI coding assistant

For the best experience, add the following instruction to your tool's configuration so your agent automatically knows where to find the documentation:

> For Particle API, SDK, data contract, or webhook tasks, start by reading `agent-documentation/llms.txt` to find the relevant topic file.

Where to add this depends on your tool:

| Tool | Configuration file |
|------|-------------------|
| **Claude Code** | `CLAUDE.md` in your project root |
| **Cursor** | `.cursor/rules/` directory (create a `.mdc` file) |
| **GitHub Copilot** | `.github/copilot-instructions.md` |
| **Windsurf** | `.windsurfrules` in your project root |
| **OpenAI Codex** | `AGENTS.md` in your project root |

Or simply tell your agent directly: *"Read `agent-documentation/llms.txt` first."*

## Support expectations

This repository is **not** an officially supported Particle product and does not include an SLA.  
For product help, troubleshooting, or production support, please use Particle’s standard support channels.


**DISCLAIMER**
This repository is provided by Particle for educational and illustrative purposes only. It is intended to help you get started with Particle integrations and is not a production-ready solution.

**No Warranty**. This code is provided "as is" without warranty of any kind, express or implied. Particle makes no representations regarding the accuracy, reliability, completeness, or suitability of this code for any particular purpose.

**Not Production-Ready**. This repository contains starter code, examples, and scaffolding for local development and learning. It has not been designed, tested, or hardened for production use. You are solely responsible for evaluating the security, compliance, privacy, performance, and scalability requirements of any implementation you deploy.

**No Maintenance Commitment**. Particle is under no obligation to maintain, update, or ensure compatibility of this repository as dependencies, best practices, or Particle's products evolve. There is no SLA associated with this repository.

**Support**. GitHub Issues and Pull Requests are not monitored as a support channel. For assistance, please use Particle's standard support channels. Pull requests may be reviewed at Particle's discretion but are not guaranteed to be merged or addressed.

**Your Responsibility**. By using this code, you acknowledge that you are responsible for your own implementation decisions, including security configurations, data handling, regulatory compliance, and operational monitoring.
