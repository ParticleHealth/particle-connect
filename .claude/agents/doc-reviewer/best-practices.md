# Best Practices for Agent Documentation

Reference guide used by the doc-reviewer agent to evaluate and improve agent-facing documentation.

## Fundamental Rule

The sole audience for this documentation is LLM agents (Claude Code, Codex, Cursor, Copilot, Gemini CLI, etc.). Every decision — word choice, structure, ordering, what to include, what to cut — must optimize for LLM comprehension and action accuracy. If a change makes docs more readable for humans but less actionable for LLMs, reject it.

## LLM-Optimized Writing Rules

1. **Structure > prose**: Tables, code blocks, and key-value pairs are parsed more reliably by LLMs than paragraphs. Convert any multi-sentence explanation into structured format where possible.
2. **Exact over approximate**: Provide exact field names, exact values, exact types. `"gender": "MALE | FEMALE"` beats "use the appropriate gender string".
3. **Negative constraints early**: "NEVER do X" prevents costly mistakes. Place these before positive instructions — an LLM that skips a best practice wastes time, but one that violates a constraint produces wrong code.
4. **Disambiguate confusable terms**: If two fields, endpoints, or concepts could be mixed up, add an explicit disambiguation note. LLMs conflate similar terms aggressively.
5. **One action per instruction**: "Register the patient, then submit a query" is two instructions. Break them into separate numbered steps.
6. **Deterministic language**: Use "Use X", "Set Y to Z", "Call endpoint A". Avoid "consider", "you might want to", "it's recommended to".
7. **Token budget awareness**: Every token an LLM spends reading filler is a token not spent on reasoning. Cut ruthlessly. If a sentence doesn't change what the agent DOES, delete it.
8. **Show the shape of data**: For API requests/responses, show the exact JSON structure. LLMs generate correct code much faster from a concrete example than from a field list.

## Core Principles

### 1. Progressive Disclosure (llms.txt standard)
- Provide a lightweight index file that points to focused topic files
- Agents load only what they need; no monolithic docs
- llms.txt serves as the entry point with one-line descriptions

### 2. One Concept Per File
- Each file covers a single domain (API, SDK, auth, etc.)
- Target 100-300 lines per file; split if exceeding 400
- File name should make the topic obvious without reading it

### 3. Front-Load Critical Information
- Lead every file with purpose, key endpoints, or critical gotchas
- Put "Don't do X" warnings near the top, not buried at the bottom
- LLMs weight earlier tokens more heavily in long contexts

### 4. Structured Markdown
- Consistent heading hierarchy (H1 = title, H2 = sections, H3 = subsections)
- Use tables for structured comparisons (endpoints, error codes, formats)
- Use fenced code blocks with language tags for all code/commands
- Use bold for key terms on first use

### 5. Pointers Over Copies
- Reference source code with `file_path:line_number` format
- Don't duplicate code that changes — point to it
- Keep the "source of truth" in code; docs describe intent and gotchas

### 6. Actionable Error Guidance
- Every troubleshooting entry needs: Symptom, Cause, Fix
- Include the exact error message or HTTP status an agent would see
- Provide copy-pasteable fix commands where possible

### 7. Cross-Tool Compatibility
- AGENTS.md: universal instructions (build, test, style, conventions)
- llms.txt: lightweight index following the llms.txt standard
- Structured Markdown: works with all LLM tools (Claude Code, Cursor, Copilot, Codex)

## Quality Checklist

When reviewing each doc file, verify:

- [ ] **Accuracy**: Do endpoints, field names, and behaviors match the actual source code?
- [ ] **Completeness**: Are all public APIs/services/models documented?
- [ ] **Currency**: Do file paths and line references still resolve?
- [ ] **Conciseness**: Is every sentence earning its tokens? Remove filler.
- [ ] **Code examples**: Are they correct and runnable?
- [ ] **Gotchas documented**: Are non-obvious behaviors called out prominently?
- [ ] **No stale content**: Remove references to deleted files or deprecated APIs
- [ ] **Consistent terminology**: Same concept uses the same term everywhere
- [ ] **Cross-references work**: Links between docs are valid
- [ ] **LLM-optimized**: Uses structured formats over prose, exact values over descriptions, deterministic instructions over suggestions, negative constraints are prominent

## Drift Detection Strategy

Documentation drifts from code when:
1. **New files/modules added** — check for undocumented source files
2. **API signatures changed** — compare doc'd params vs actual function signatures
3. **New error types** — check exception hierarchy for undocumented errors
4. **Config changes** — new env vars, new CLI flags, new settings
5. **Deleted code** — docs reference files/functions that no longer exist

## Anti-Patterns to Flag

- Monolithic files (>400 lines) trying to cover everything
- Inline code blocks that duplicate source (will go stale)
- Vague instructions ("configure as needed" without specifics)
- Missing error codes or status codes for API endpoints
- Undocumented required fields or parameters
- Contradictions between files (e.g., llms.txt says one thing, AGENTS.md another)
- Outdated model/context window numbers
- Documentation of internal implementation details that agents don't need
- Hedging language ("consider", "you may want to") instead of direct instructions
- Prose paragraphs where a table or code block would convey the same info in fewer tokens
- Describing data shapes in words instead of showing the JSON structure
- Ambiguous terms without disambiguation (e.g., using "ID" without specifying which ID)
