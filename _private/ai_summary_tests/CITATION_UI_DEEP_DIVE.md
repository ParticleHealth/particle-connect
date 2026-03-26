# Building a "Click to See Source" Citation UI: Deep Dive

## The Problem Statement

You have an AI-generated clinical summary like this:

> Elvira Valadez, a 32-year-old female with no known prior allergies, presented to the ED via EMS with acute anaphylaxis after eating shrimp. Symptoms included difficulty breathing, generalized urticaria, and facial angioedema. EMS administered 0.3mg Epinephrine IM en route. In the ED, she received a second dose of Epinephrine 0.3mg IM, IV Diphenhydramine, IV Famotidine, and oxygen.

And you have citations like:

| text_snippet | resource_reference_id |
|---|---|
| "In the ED, she received a second dose of Epinephrine 0.3mg IM..." | `067f4062f38f...` |
| "Symptoms included difficulty breathing, generalized urticaria..." | `0b0ac9ad50e0...` |
| "EMS administered 0.3mg Epinephrine IM en route." | `463ca4edffce...` |

The goal is: **a user reads the summary, sees highlighted phrases, clicks one, and sees the original source document that proves the claim.**

This requires solving three separate problems:

1. **Highlight problem**: Which words in the summary should be highlighted?
2. **Resolution problem**: When they click, what do you show them?
3. **Presentation problem**: How do you render the source in a useful way?

Here's exactly what each step requires and where it breaks.

---

## Step 1: The Highlight Problem

### What you need to do

Take the summary text and overlay the citation snippets onto it, so you know which character ranges to highlight.

### What you have

- `aIOutputs.text` — the full summary as a plain string
- `aICitations.text_snippet` — verbatim excerpts from source documents

### What you don't have

- **No inline markers.** The summary has no `[1]` tags, no `<cite>` elements, no offset metadata.
- **No `position` or `sequence` field** on citations.
- The snippets come from the **source documents**, not the summary. The summary may paraphrase, reword, or restructure.

### How to do it

**Approach A: Exact substring matching (works for ~91% of discharge summaries)**

```python
for citation in citations:
    idx = summary_text.find(citation.text_snippet)
    if idx >= 0:
        highlights.append((idx, idx + len(citation.text_snippet), citation.id))
```

This works because Particle's AI often copies phrases verbatim from sources into the summary. Tested against real data:

| Summary Type | Exact Match | Partial Match | Source-Only | Total |
|---|---|---|---|---|
| Discharge Summary | 21 (91%) | 0 | 2 (9%) | 23 |
| Patient History | 62 (75%) | 3 (4%) | 18 (22%) | 83 |

The "source-only" citations are evidence the AI used but didn't copy verbatim — e.g., the citation says "Chest x-ray: Negative" but the summary says "A chest x-ray was negative." The claim is supported, but the wording differs.

**Approach B: Fuzzy/normalized matching (catches another ~5%)**

```python
normalized_summary = collapse_whitespace(summary.lower())
normalized_snippet = collapse_whitespace(snippet.lower())
idx = normalized_summary.find(normalized_snippet)
```

**Approach C: Semantic matching (for the remaining ~15-20%)**

For snippets that don't appear verbatim, you'd need NLP:
- Sentence-level embedding similarity (cosine distance between snippet and each summary sentence)
- This handles paraphrasing ("Chest x-ray: Negative" → "A chest x-ray was negative")
- Adds complexity: requires an embedding model, similarity threshold tuning

### What coverage looks like

After substring + normalized matching:
- **43% of the discharge summary text** has direct citation support (character coverage)
- **65% of the patient history text** has direct citation support
- The rest is connecting prose, section headers, "Not Documented" filler, and the disclaimer

### The step-by-step

1. Strip the disclaimer (split on "Patient Name:" or "This summary is based on")
2. For each citation, run `summary.find(snippet)` — if found, record `(start, end, citation_id)`
3. For misses, normalize whitespace/case and retry
4. Sort highlights by start position
5. Handle overlapping ranges (multiple citations for the same text)
6. Render: highlighted spans with click handlers

---

## Step 2: The Resolution Problem

### What you need to do

When the user clicks a highlighted phrase, show them the **original source content** that the citation came from.

### What you have

Each citation gives you:
- `resource_reference_id` — the ID of the source resource
- `resource_type` — which table it's in (`DocumentReferences`, `Labs`, `Encounters`, etc.)
- `text_snippet` — the verbatim excerpt

### Three resolution scenarios

#### Scenario A: Structured data citations (Labs, Encounters, Procedures, etc.) — WORKS

These resolve cleanly. The `resource_reference_id` matches a primary key in the corresponding flat data table.

**Example — what the user sees when they click:**

> **Summary says:** "WBC Auto (Bld) [#/Vol]: 10.11 10*3/uL"
>
> **Source record (from `labs` table):**
> - Lab name: WBC Auto (Bld) [#/Vol]
> - Value: 10.106057307073788
> - Unit: 10*3/uL
> - Collected: 2011-05-28T15:19:11+0000

> **Summary says:** "In 2025, there was 1 admission."
>
> **Source record (from `encounters` table):**
> - Type: Emergency
> - Period: 2025-11-01T20:30:00 to 2025-11-01T23:30:00

**Resolution rate: ~100%** for Labs, Encounters, Procedures, VitalSigns, Medications, Problems.

**But:** Only 9.2% of all citations are structured types. The other 90.8% are DocumentReferences.

#### Scenario B: Document citations that resolve (8.3% of doc citations) — WORKS BUT RAW

Some `resource_reference_id` values match a `document_reference_id` in the `documentReferences` table.

**Example — what the user sees when they click:**

> **Summary says:** "The patient has a severe, life-threatening allergy to shellfish"
>
> **Source document section (from `documentReferences`):**
> - Section type: Problem List
> - Raw content:
> ```xml
> <text xmlns:ns0="urn:hl7-org:v3">
>   <list>
>     <item><content styleCode="Bold">Anaphylaxis due to shellfish</content>
>       (NEW - 11/01/2025) - RESOLVED with treatment</item>
>     <item><content styleCode="Bold">Shellfish allergy -
>       SEVERE/LIFE-THREATENING</content> (NEW - 11/01/2025) - ACTIVE</item>
>   </list>
> </text>
> ```

**Problem:** The source content is **CDA XML**, not readable text. You need to:
1. Parse the XML
2. Strip tags
3. Extract the text content
4. Optionally highlight the specific `text_snippet` within it

This is doable but adds a rendering layer.

#### Scenario C: Document citations that DON'T resolve (91.7% of doc citations) — DEAD END

This is the core problem. Most `resource_reference_id` values for `DocumentReferences` citations **do not exist in the `documentReferences` table**.

**Example — what happens when the user clicks:**

> **Summary says:** "In the ED, she received a second dose of Epinephrine 0.3mg IM, IV Diphenhydramine, IV Famotidine, and oxygen."
>
> **Citation ref ID:** `067f4062f38f994fa3338a5bf6ea2b47c3c1ef7248f690fad241b5b9364c05e2`
>
> **Lookup:** `SELECT * FROM documentReferences WHERE document_reference_id = '067f4062...'` → **0 rows**
>
> **Result:** Nothing to show.

Why? The flat data `documentReferences` table only contains a subset of document sections — 51 records from 6 source XML files. The AI citations reference document sections that were processed during summary generation but weren't included in the flat data export. The IDs are SHA-256 hashes of document content, and the corresponding content lives only in the raw CCDA XML files.

**Scale of the problem:**

| | Count | Can resolve? |
|---|---|---|
| Total citations | 542 | — |
| Structured (Labs, Encounters, etc.) | 50 | Yes (100%) |
| DocumentReferences — in flat data | ~11 unique refs | Yes (need XML parsing) |
| DocumentReferences — NOT in flat data | ~121 unique refs | **No** (need CCDA) |

For the first discharge summary: **23 citations, 0 resolvable from flat data.** Every single one is a dead end.

---

## Step 3: The Presentation Problem

Even when you CAN resolve a citation, you need to decide what to show.

### For structured data (Labs, Vitals, etc.)

Straightforward — render the record as a card:

```
┌─────────────────────────────────────────────┐
│ 📋 Source: Lab Result                        │
│                                              │
│ Test:      WBC Auto (Bld) [#/Vol]           │
│ Value:     10.11 10*3/uL                    │
│ Collected: 2011-05-28                       │
│ Report:    CBC panel                        │
│                                              │
│ 💡 The summary rounded 10.106 → 10.11       │
└─────────────────────────────────────────────┘
```

### For resolved documents

The raw content is CDA XML. You need to:

1. Parse the XML (`<text>` element with nested `<list>`, `<table>`, `<paragraph>`, `<content>` tags)
2. Strip CDA namespace prefixes
3. Convert to readable HTML or plain text
4. Highlight the specific `text_snippet` within the extracted text
5. Show the section type as context ("Problem List", "Hospital Course", "Discharge Medications")

```
┌─────────────────────────────────────────────┐
│ 📄 Source: Problem List                      │
│ From: Encounter_Summary___PCP66537___.xml    │
│                                              │
│ • Anaphylaxis due to shellfish               │
│   (NEW - 11/01/2025) - RESOLVED             │
│ • [Shellfish allergy - SEVERE/LIFE-          │ ← highlighted
│   THREATENING] (NEW - 11/01/2025) - ACTIVE   │ ← highlighted
│                                              │
└─────────────────────────────────────────────┘
```

### For unresolvable citations (the 91.7%)

You have three options:

**Option A: Show just the snippet (minimum viable)**
```
┌─────────────────────────────────────────────┐
│ 📌 Citation                                  │
│                                              │
│ "In the ED, she received a second dose of   │
│  Epinephrine 0.3mg IM, IV Diphenhydramine,  │
│  IV Famotidine, and oxygen."                 │
│                                              │
│ Source: Clinical document (not available in   │
│ current data export)                         │
└─────────────────────────────────────────────┘
```

This is honest but underwhelming. The user sees the same text they already read.

**Option B: Pull CCDA and resolve from there**

This is the real fix. The `resource_reference_id` is a hash of a section in the CCDA XML. If you also retrieve the CCDA data:

1. Download CCDA ZIP via `/api/v2/patients/{id}/ccda`
2. Extract XML files
3. Parse each XML document's sections
4. Hash each section the same way Particle does
5. Build a lookup: `hash → (xml_file, section_element, full_text)`
6. Now the 91.7% dead ends become resolvable

**Problem:** You don't know Particle's exact hashing algorithm. You'd need to reverse-engineer it or ask Particle for the spec. Without it, you can't reliably map `resource_reference_id` → CCDA section.

**Option C: Full-text search across CCDA**

Instead of hash matching, search for the `text_snippet` verbatim in all CCDA XML content:

1. Download and extract CCDA
2. For each XML file, extract all text content
3. Search for the citation's `text_snippet`
4. If found, show the surrounding context from that XML section

This sidesteps the hash problem entirely. The `text_snippet` is a verbatim excerpt — it WILL appear in exactly one place in the CCDA content.

---

## The Complete Engineering Plan

### Phase 1: Flat-data-only (works today, partial coverage)

What you can ship with just the flat data API response:

1. **Highlight**: Substring-match citations against summary text (~80% match rate)
2. **Resolve structured citations**: Join Labs, Encounters, etc. by ID (100% resolution)
3. **Resolve document citations**: Join to `documentReferences` table (8.3% resolution)
4. **Parse resolved XML**: Strip CDA tags, extract readable text
5. **Fallback**: Show `text_snippet` alone for unresolvable citations

**Coverage: ~18% of citations fully resolvable (all structured + 8.3% of documents)**

### Phase 2: Add CCDA retrieval (full coverage)

1. Also call `/api/v2/patients/{id}/ccda` to get the ZIP
2. Extract all XML files
3. For each XML file, extract all `<text>` elements from `<section>` elements
4. Index the full text content of each section
5. For unresolved citations, search for `text_snippet` in the CCDA text index
6. When found, show the full section context with the snippet highlighted

**Coverage: ~100% of citations resolvable**

### Phase 3: Polish

1. **Section parser**: Split summary text into structured sections (Hospital Course, Diagnoses, Results, Orders, Follow-ups) using the known template headers
2. **Citation clustering**: Group citations by section, so each section shows its evidence count
3. **Source file attribution**: Use `recordSources` + `sources` to show "From: Discharge_Summary___PCP66537___.xml"
4. **Confidence indicators**: Color-code highlights by resolution quality (green = resolved to source record, yellow = snippet-only, red = no evidence found)

---

## Summary of What's Blocking You

| Component | Status | What's needed |
|---|---|---|
| Highlighting citations in summary text | **Solvable now** | Substring matching (proven to work) |
| Resolving Labs/Encounters/Vitals | **Works now** | Simple SQL join by ID |
| Resolving 8.3% of document citations | **Works but raw** | CDA XML parser for readable display |
| Resolving 91.7% of document citations | **Blocked** | Need CCDA data + text search or hash algorithm |
| Rendering source documents | **Needs work** | CDA XML → HTML converter |
| Citation ordering/positioning | **Missing from API** | Must derive from text matching |
| Section-level structure | **Missing from API** | Must parse template headers with regex |

The fundamental issue is: **flat data alone doesn't carry enough of the source documents to resolve most citations.** The flat `documentReferences` table has 51 records, but the citations reference 132 unique document sections. The missing 121 live in the CCDA XML. You need both data formats to build a complete citation experience.
