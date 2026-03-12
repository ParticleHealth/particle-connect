# SWOT Analysis — Particle Connect Agent Documentation & Repo

**Date**: 2026-03-11
**Scope**: Full repository analysis — agent documentation, tooling, DX, CI/CD, testing, cross-tool compatibility

---

## Strengths

- **Progressive disclosure is gold-standard.** llms.txt → AGENTS.md → topic files. An LLM loads ~3.2K tokens (llms.txt + AGENTS.md + one topic file) to start any task. Full doc set is ~31K tokens — fits in any modern context window.

- **LLM-optimized writing is strong.** ~75% structured content (tables, code blocks) vs 25% prose. Deterministic language throughout ("Use X", "Set Y", never "consider" or "you might want to"). Negative constraints front-loaded in llms.txt.

- **Error documentation is exceptional.** 09-troubleshooting.md has an error quick-reference table (HTTP code → exception → retry safe → action), 17 Symptom/Cause/Fix entries, exception hierarchy diagram, retry classification, and copy-pasteable fix code.

- **New data contracts (11, 12) raise the bar.** 22 table schemas with column definitions, types, relationships, and provenance model. 7 notification types with full CloudEvents examples and signature verification.

- **Claude Code integration is sophisticated.** Custom slash commands (`/update-docs`, `/new-integration`), specialized doc-reviewer agent with persistent memory, drift tracking, and self-updating best practices.

- **Integration workflow is well-designed.** Two-phase template (Discovery → Specification) with Particle compatibility matrix, data flow diagrams, known unknowns tracking, and sandbox test scenario mappings.

- **Accuracy is high.** All sampled endpoints, field names, and behaviors match actual source code. Critical llms.txt error (address_state) was caught and fixed. Drift tracking is active.

---

## Weaknesses

- **Pointers over copies is violated.** No `file_path:line_number` references anywhere. SDK usage examples are duplicated inline (04-sdk-reference.md:136-160) instead of pointing to `workflows/hello_particle.py`. Code will go stale when source changes.

- **71% of code blocks lack language tags.** 113 of 158 code blocks are untagged — especially in 02-api-reference.md (4% tagged), 03-management-api-reference.md (0%), 08-authentication.md (0%). LLMs parse tagged blocks more reliably.

- **CI/CD is nearly empty.** Tests, linting (ruff), and secret scanning (trufflehog) are commented out in the GitHub Actions workflow. No automated quality gates exist.

- **Test coverage is uneven.** Analytics pipeline has 8 test files. SDK has 1 integration test (no unit tests per module). Management UI has zero tests — frontend and backend both untested.

- **Frontend is undocumented.** React component architecture, state management, API client patterns, and prop signatures are absent from 06-management-ui.md. ~50% coverage vs ~90-95% for Python modules.

- **Patient ID terminology is confusing and buried.** `patient_id` vs `particle_patient_id` vs `external_patient_id` vs `person_id` — explained in 12-notification-data-contract.md:47-55 but not front-loaded. LLMs will conflate these.

- **Two files exceed the 400-line ceiling.** 11-flat-data-contract.md (598 lines, ~4.6K tokens) and 12-notification-data-contract.md (415 lines, ~5.5K tokens). Justified by content density, but may challenge context-limited models.

---

## Opportunities

- **Auto-generate compatibility reports from integration specs.** When a client file is filled out, an agent could cross-check against Particle constraints and flag issues automatically.

- **Seed boilerplate code from integration templates.** A `/generate-integration` command could produce auth setup, data mapping, and error handling code from a completed client spec.

- **CI/CD is low-hanging fruit.** Uncommenting the existing pytest, ruff, and trufflehog steps in the workflow file would add automated quality gates with near-zero effort.

- **Webhook receiver patterns are missing.** 12-notification-data-contract.md documents payload format but not implementation. Adding a FastAPI/Flask webhook handler example would make the doc directly actionable.

- **Decision trees for common tasks.** "Which data format should I use?" or "How do I debug a timeout?" — adding ASCII flow charts would reduce LLM reasoning time.

- **Enum value centralization.** WorkflowType, ADTEventType, PurposeOfUse are repeated across docs. A single reference could improve consistency and reduce staleness risk.

---

## Threats

- **Documentation drift accelerates with Signal.** The Signal module added 11 new models and 6 endpoints across 8 doc files. Each code change now requires updates in more places.

- **No automated drift detection.** Doc-reviewer agent tracks drift manually in MEMORY.md. If nobody runs `/update-docs` after code changes, docs silently go stale.

- **Sensitive data in integration specs.** Client endpoints, field mappings, and compliance details live in `_private/integrations/`. The sync-to-public workflow strips `_private/`, but accidental commits to the wrong branch could leak.

- **Monolithic data contracts may deter loading.** An LLM seeing 598 lines in 11-flat-data-contract.md may load it unnecessarily when it only needs one table's schema.

---

## Prioritized Next Steps

### High Priority — Discoverability

1. **Add a terminology disambiguation file (00-terminology.md).** Define `patient_id` vs `particle_patient_id` vs `external_patient_id` vs `person_id` in one place. Reference from every file that uses these terms. LLMs conflate similar terms aggressively — this is a direct error-reduction measure.

2. **Add task-based routing to llms.txt.** Current llms.txt lists files by topic. Add a "Start here based on your task" section: "Building an integration? → 04, 08, 10. Debugging? → 09. Analyzing data? → 05, 11. Setting up webhooks? → 02 (Signal section), 12." Reduces the LLM's decision overhead for first file load.

### High Priority — Efficiency

3. **Add language tags to all code blocks.** Tag HTTP examples as `http`, config as `bash` or `ini`, JSON as `json`, Python as `python`. This is a mechanical fix across ~113 blocks that directly improves LLM code generation accuracy.

4. **Replace duplicated code examples with source pointers.** Convert inline usage patterns in 04-sdk-reference.md to references: `See: particle-api-quickstarts/workflows/hello_particle.py:45-60`. Prevents staleness and follows the "pointers over copies" principle.

### Medium Priority

5. **Uncomment CI quality gates.** The GitHub Actions workflow already has pytest, ruff, and trufflehog steps — they're just commented out. Uncomment them to get automated linting, testing, and secret scanning with near-zero effort.

6. **Add a webhook receiver example to 12-notification-data-contract.md.** A minimal FastAPI route showing: receive CloudEvents POST → verify signature → parse payload → return 200. Makes the notification contract directly implementable.

7. **Split 02-api-reference.md.** Currently covers Query Flow + Document + Signal (287 lines, 3 concepts). Split into `02-query-flow-api.md` and `02-signal-api.md` to maintain one-concept-per-file principle and keep Signal docs independently loadable.

### Low Priority

8. **Add YAML frontmatter to each doc file.** Metadata block with version, last_updated, maintainer, and tags. Enables automated staleness detection and helps LLMs assess document currency.

9. **Document frontend architecture.** Add React component hierarchy, state management patterns, and API client usage to 06-management-ui.md. Currently at ~50% coverage vs ~95% for Python modules.

10. **Create a CHANGELOG.md for API version history.** Track breaking changes, new endpoints, and deprecated fields. Currently no versioning exists — an LLM has no way to know if docs describe the current or previous API version.
