# AI Outputs & Citations: Deep Analysis

## Data Shape at a Glance

| Table | Records | Purpose |
|-------|---------|---------|
| `aIOutputs` | 22 | AI-generated clinical summaries |
| `aICitations` | 542 | Evidence snippets backing each summary |
| `documentReferences` | 51 | Flattened clinical document sections |
| `recordSources` | 307 | Resource → source file mapping |
| `sources` | 6 | Original CCDA XML files ingested |

---

## How the Tables Relate

```
sources (6 CCDA XML files)
    │
    ▼  source_id
recordSources (307 rows — which resource came from which file)
    │
    ▼  resource_id → document_reference_id / encounter_id / lab_observation_id / etc.
documentReferences / encounters / labs / vitalSigns / medications / problems / procedures
    ▲
    │  resource_reference_id + resource_type
aICitations (542 rows — "here is the exact text that proves this claim")
    │
    ▼  ai_output_id
aIOutputs (22 rows — the actual summary text)
```

### Join Keys

| From → To | Join Field |
|-----------|-----------|
| `aICitations` → `aIOutputs` | `ai_output_id` |
| `aICitations` → clinical tables | `resource_reference_id` → `{table}_id` (e.g., `document_reference_id`, `lab_observation_id`) |
| `aIOutputs.resource_reference_ids` | Comma-separated `ResourceType/hash` pairs — duplicates the citation refs but denormalized onto the output row |
| `recordSources` → clinical tables | `resource_id` → resource primary key |
| `recordSources` → `sources` | `source_id` |

---

## What's In the Summaries

### Types

- **21 DISCHARGE_SUMMARY** — one per encounter/document, structured template with: patient name, DOB, facility, admit/discharge dates, hospital course narrative, diagnoses, labs/imaging, medications (start/stop/continue), DME orders, follow-ups, social determinants
- **1 PATIENT_HISTORY** — longitudinal view across all encounters: demographics, problem list, hospitalizations, surgeries, imaging, labs, medications, allergies, immunizations, social history

### Citation Distribution

- Average: ~22 citations per discharge summary, 83 for the patient history
- Each citation has a `text_snippet` — the exact verbatim excerpt from the source document
- Multiple citations share the same `resource_reference_id` (one document section cited multiple times for different claims)
- Example: output `484011023214690159` has 23 citations pointing to only 7 unique source documents

### Citation Resource Types

| resource_type | Count | % |
|--------------|-------|---|
| DocumentReferences | 492 | 90.8% |
| Labs | 27 | 5.0% |
| Encounters | 13 | 2.4% |
| Procedures | 4 | 0.7% |
| VitalSigns | 2 | 0.4% |
| Medications | 2 | 0.4% |
| Problems | 1 | 0.2% |
| Locations | 1 | 0.2% |

The overwhelming majority (91%) cite document sections, not structured data.

---

## The Citation Resolution Gap

This is the single biggest structural issue:

| Metric | Count |
|--------|-------|
| Unique `resource_reference_id` values in citations (DocumentReferences type) | 132 |
| Actual `documentReferences` records in flat data | 51 |
| **Matched (resolvable)** | **11 (8.3%)** |
| **Orphaned (unresolvable)** | **121 (91.7%)** |

**Only 8.3% of document citations can be resolved to their source text in the flat data.**

The other 91.7% reference document sections that exist in the CCDA XML but were not flattened into the `documentReferences` table. This means:

- You have the summary text ("Serum Tryptase 18.5 mcg/L")
- You have the citation snippet pointing to a `resource_reference_id`
- But you **cannot look up what that document section actually contains** from flat data alone
- You'd need the raw CCDA XML to resolve these references

Labs, encounters, and other structured resources resolve much better — their IDs match the flat data tables directly.

---

## Workflows for Surfacing Summaries with Citations

### Workflow 1: Summary → Inline Citations (best for display)

```
1. SELECT * FROM ai_outputs WHERE patient_id = :pid
2. For each output, SELECT * FROM ai_citations WHERE ai_output_id = :oid
3. For each citation with resource_type = 'DocumentReferences':
   - Try: SELECT * FROM document_references WHERE document_reference_id = :ref_id
   - If found: display text_snippet with linked source section
   - If not found: display text_snippet only (source unresolvable from flat data)
4. For structured citations (Labs, Encounters, etc.):
   - Join directly to the matching table for full context
```

### Workflow 2: Citation → Provenance Chain (best for verification)

```
1. Start with a citation's resource_reference_id
2. Look up the resource in its table (document_references, labs, etc.)
3. Join through record_sources to get the source_id
4. Join to sources to get the original XML filename
5. Result: "This claim came from Discharge_Summary___PCP66537___.xml"
```

### Workflow 3: Summary-per-Encounter View (best for clinical review)

```
1. Get all discharge summaries
2. Group by the encounter they reference (parse resource_reference_ids for Encounters/)
3. Show one summary card per encounter with its citations underneath
4. Overlay with encounter metadata (dates, facility, type)
```

---

## SWOT Analysis

### Strengths

1. **Citation granularity is excellent.** Every claim in a summary has a traceable `text_snippet` pointing to the exact source text. This is rare and valuable — most AI summary systems don't provide verbatim evidence.

2. **Structured template for discharge summaries.** Consistent sections (Hospital Course, Diagnoses, Results, Orders, Follow-ups, Social) make parsing and display predictable. You can build reliable UI components around these sections.

3. **Dual-format reference tracking.** Both `aICitations` (normalized, per-snippet) and `aIOutputs.resource_reference_ids` (denormalized, per-output) exist. The denormalized field is useful for quick "which documents were used?" without joining.

4. **Multi-type citations.** Citations don't just point at documents — they reference Labs, Encounters, Procedures, etc. directly. This means structured data claims (lab values, dates) can be verified against the structured tables, not just free text.

5. **The PATIENT_HISTORY type is genuinely useful.** A single longitudinal summary across all encounters with 83 citations is exactly what a clinician needs for a "patient at a glance" that's verifiable.

6. **All TEXT columns (ELT).** No type-casting surprises on load. Every consumer decides how to cast.

### Weaknesses

1. **91.7% of document citations are orphaned in flat data.** The `resource_reference_id` for most DocumentReferences citations points to documents NOT in the `documentReferences` table. You cannot resolve the citation to its source section. This is the critical gap.

2. **No inline citation markers in summary text.** The summary `text` field is plain prose. There are no `[1]` markers, no `<cite>` tags, no way to know which sentence maps to which citation without NLP/fuzzy matching between the summary text and the citation `text_snippet`. Building a highlighted, clickable-citation UI requires string matching.

3. **`resource_reference_ids` is a comma-separated string.** It duplicates information from `aICitations` but in a harder-to-parse format. It also contains duplicates (the same ID appears multiple times) and mixes `ResourceType/hash` formatting.

4. **No section-level structure in summary text.** "Hospital Course Summary:", "Admit Diagnosis(es):", etc. are in the plain text but not in separate fields. Parsing sections requires regex or keyword matching against the template.

5. **No ordering on citations.** Citations have no `sequence` or `position` field. You can't reconstruct the order they appear in the summary without text matching.

6. **The disclaimer is embedded in the text.** Every summary starts with the same legal disclaimer. This is noise for any downstream consumer and must be stripped.

### Opportunities

1. **Build a citation linker.** Fuzzy-match `text_snippet` against the summary `text` to insert inline citation markers. The snippets are verbatim excerpts, so exact substring matching would work for ~80%+ of cases.

2. **Cross-reference with CCDA for full resolution.** Pull CCDA data alongside flat data and index document sections by their hash. This would resolve the 91.7% of orphaned citations.

3. **Section parser.** Build a template-aware parser that splits discharge summaries into structured sections (Hospital Course, Diagnoses, Results, Orders, Follow-ups). Each section then gets its own citation cluster.

4. **AI summary quality scoring.** Compare citation count and coverage against summary length. Flag summaries with low citation density (potential hallucination risk). Flag summaries where citations don't fuzzy-match the text (potential misattribution).

5. **Citation deduplication.** Group citations by `resource_reference_id` to see which source documents contribute most evidence. Build a "key sources" sidebar.

6. **Temporal citation grouping.** Cross-reference citation `resource_reference_id` with encounter dates to build a timeline of evidence.

### Threats

1. **Citation orphaning undermines trust.** If a consumer tries to verify a claim and can't resolve the citation, the whole citation system loses credibility. The 91.7% gap is a trust problem.

2. **Template changes break parsers.** If Particle changes the discharge summary template (adds/removes sections, changes headers), any section parser breaks silently.

3. **Disclaimer liability.** The embedded disclaimer says "may be incomplete" and "must be independently verified." If consumers display summaries without the disclaimer, there's liability risk. If they display it, it's noisy.

4. **Scale concerns.** 542 citations for 22 outputs (one patient). A panel of 1,000 patients could mean 25,000+ citation records. The flat structure works fine, but joins get expensive without indexing.

---

## Serviceability Assessment

### Is the structure easily serviceable?

**Mostly yes, with caveats.**

- The two-table design (`aIOutputs` + `aICitations`) is clean and normalized. Standard SQL joins work.
- The `resource_type` field on citations makes it easy to fan out to the right table.
- All TEXT columns means no schema migration issues.

**But:**
- The comma-separated `resource_reference_ids` on `aIOutputs` is a denormalization smell. It's redundant with `aICitations` and harder to query.
- The lack of a `section` field on the output text means you need text parsing to serve specific parts.
- No pagination or cursor on the citations — you always get all 542 at once.

### Is the summary easily serviceable?

**The text quality is high. The text format is not.**

The summaries are well-structured clinically — the template is comprehensive, the language is clear, and the information is actionable. A clinician reading the raw text would find it useful.

But serving it programmatically requires:
- Stripping the disclaimer
- Parsing sections by header keywords
- Building a citation overlay through string matching

There's no machine-readable structure on the summary itself. It's "structured text" — human-readable structure, not API-friendly structure.

### Is the summary easily citable based on this structure?

**Partially.**

What works:
- Every claim has at least one citation with `text_snippet`
- The snippets are verbatim source text, making them verifiable
- Citations link to specific resource types and IDs
- The provenance chain (citation → resource → recordSource → source file) is complete

What doesn't:
- No inline markers tying citations to specific sentences in the summary
- 91.7% of document citations can't be resolved to source content in flat data
- No citation ordering or position metadata
- Building a "click to see source" UI requires fuzzy text matching + CCDA access

**Bottom line:** The citation *data* is rich. The citation *UX* requires significant engineering to surface.

---

## Recommendations

### Quick Wins

1. **Strip disclaimer programmatically.** Split on the first double newline after the disclaimer block.
2. **Index citations by snippet.** Build a lookup from `text_snippet` → citation record, then do substring search against the summary text.
3. **Pre-join citations to outputs.** Create a view or materialized query that groups citations per output with their resource details.

### Medium Effort

4. **Section parser.** Regex-based parser for the discharge summary template. Map each section header to a structured field.
5. **Citation position mapper.** For each citation `text_snippet`, find its character offset in the summary `text`. Store as `(start, end, citation_id)` tuples.
6. **Resolve orphaned citations via CCDA.** Pull the CCDA ZIP, parse XML sections, hash them the same way Particle does, build a local lookup table.

### Longer Term

7. **Request structured summaries from Particle.** The current format is plain text with implicit structure. A JSON-structured summary (sections as fields, citations inline) would eliminate most of the parsing work.
8. **Request citation position metadata.** A `text_offset` or `sentence_index` field on citations would make inline highlighting trivial.
