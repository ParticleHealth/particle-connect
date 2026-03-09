# particle-connect

Tools, helper scripts, and reference examples to help customers integrate with the Particle Health Platform.

This repository is intended to accelerate evaluation and implementation work by providing practical starting points (e.g., sample workflows, utilities, and scaffolding). You are free to adapt these materials to your environment and requirements.

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
