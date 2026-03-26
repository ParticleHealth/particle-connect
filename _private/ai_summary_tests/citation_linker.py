#!/usr/bin/env python3
"""Citation Linker: Maps citation text_snippets to their position in summary text.

Demonstrates the workflow for building an inline-citation UI:
  1. Load an AI output summary
  2. For each citation, find where its text_snippet appears in the summary
  3. Produce a list of (start, end, citation_id, text_snippet) ranges
  4. Show which claims are well-cited vs. uncited

This is the key missing piece — Particle provides citations and summaries
separately, but no inline markers connecting them.
"""

import json
import os
import re
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "ai_summary.db")


def strip_disclaimer(text: str) -> str:
    """Remove the standard Particle disclaimer from summary text."""
    marker = "Patient Name:"
    idx = text.find(marker)
    if idx > 0:
        return text[idx:]

    # For PATIENT_HISTORY type
    marker2 = "This summary is based on"
    idx2 = text.find(marker2)
    if idx2 > 0:
        return text[idx2:]

    return text


def find_snippet_positions(summary_text: str, snippets: list[dict]) -> list[dict]:
    """Find where each citation snippet appears in the summary text.

    Returns a list of matches with start/end positions, or None if not found.
    Uses exact substring matching first, then normalized matching.
    """
    results = []
    normalized_text = normalize(summary_text)

    for snippet_info in snippets:
        snippet = snippet_info["text_snippet"]
        citation_id = snippet_info["citation_id"]
        resource_type = snippet_info["resource_type"]

        # Try exact match first
        idx = summary_text.find(snippet)
        if idx >= 0:
            results.append({
                "citation_id": citation_id,
                "resource_type": resource_type,
                "text_snippet": snippet,
                "start": idx,
                "end": idx + len(snippet),
                "match_type": "exact",
            })
            continue

        # Try normalized match (collapse whitespace, case-insensitive)
        norm_snippet = normalize(snippet)
        idx = normalized_text.find(norm_snippet)
        if idx >= 0:
            results.append({
                "citation_id": citation_id,
                "resource_type": resource_type,
                "text_snippet": snippet,
                "start": idx,
                "end": idx + len(norm_snippet),
                "match_type": "normalized",
            })
            continue

        # Try partial match (first 40 chars)
        if len(snippet) > 40:
            partial = normalize(snippet[:40])
            idx = normalized_text.find(partial)
            if idx >= 0:
                results.append({
                    "citation_id": citation_id,
                    "resource_type": resource_type,
                    "text_snippet": snippet,
                    "start": idx,
                    "end": idx + len(partial),
                    "match_type": "partial",
                })
                continue

        # Not found in summary text — this citation supports the summary
        # but its text comes from the source, not the summary itself
        results.append({
            "citation_id": citation_id,
            "resource_type": resource_type,
            "text_snippet": snippet,
            "start": None,
            "end": None,
            "match_type": "source_only",
        })

    return results


def normalize(text: str) -> str:
    """Normalize text for fuzzy matching."""
    return re.sub(r"\s+", " ", text.lower().strip())


def analyze_output(conn, ai_output_id: str):
    """Analyze a single AI output's citation coverage."""
    cursor = conn.cursor()

    # Get the summary
    cursor.execute(
        "SELECT type, text FROM aIOutputs WHERE ai_output_id = ?",
        (ai_output_id,),
    )
    row = cursor.fetchone()
    if not row:
        print(f"Output {ai_output_id} not found.")
        return

    output_type, raw_text = row
    summary_text = strip_disclaimer(raw_text)

    # Get all citations
    cursor.execute(
        "SELECT citation_id, resource_type, text_snippet FROM aICitations WHERE ai_output_id = ?",
        (ai_output_id,),
    )
    citations = [
        {"citation_id": r[0], "resource_type": r[1], "text_snippet": r[2]}
        for r in cursor.fetchall()
    ]

    print(f"Output: {ai_output_id}")
    print(f"Type: {output_type}")
    print(f"Summary length: {len(summary_text)} chars")
    print(f"Total citations: {len(citations)}")

    # Find positions
    matches = find_snippet_positions(summary_text, citations)

    # Tally match types
    by_type = {}
    for m in matches:
        mt = m["match_type"]
        by_type[mt] = by_type.get(mt, 0) + 1

    print(f"\nMatch results:")
    for mt, count in sorted(by_type.items()):
        print(f"  {mt}: {count}")

    # Show inline matches
    inline = [m for m in matches if m["start"] is not None]
    source_only = [m for m in matches if m["start"] is None]

    if inline:
        print(f"\n--- INLINE MATCHES (found in summary text) ---")
        # Sort by position
        inline.sort(key=lambda m: m["start"])
        for m in inline[:10]:
            context_start = max(0, m["start"] - 20)
            context_end = min(len(summary_text), m["end"] + 20)
            context = summary_text[context_start:context_end]
            print(f"\n  [{m['match_type']}] pos {m['start']}-{m['end']}")
            print(f"  snippet: {m['text_snippet'][:80]}...")
            print(f"  context: ...{context}...")

    if source_only:
        print(f"\n--- SOURCE-ONLY CITATIONS (evidence from source docs, not in summary text) ---")
        for m in source_only[:5]:
            print(f"  [{m['resource_type']}] {m['text_snippet'][:100]}...")

    # Calculate coverage: what % of summary text is covered by citations?
    if inline:
        covered_chars = set()
        for m in inline:
            for i in range(m["start"], m["end"]):
                covered_chars.add(i)
        coverage = len(covered_chars) / len(summary_text) * 100
        print(f"\nText coverage: {coverage:.1f}% of summary has inline citation support")
    else:
        print(f"\nText coverage: 0% — all citations are source-only (no text overlap with summary)")


def main():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        print("Run load_and_explore.py first.")
        return

    conn = sqlite3.connect(DB_PATH)

    # Analyze one discharge summary and the patient history
    cursor = conn.cursor()

    print("=" * 70)
    print("DISCHARGE SUMMARY CITATION ANALYSIS")
    print("=" * 70)
    cursor.execute(
        "SELECT ai_output_id FROM aIOutputs WHERE type = 'DISCHARGE_SUMMARY' LIMIT 1"
    )
    row = cursor.fetchone()
    if row:
        analyze_output(conn, row[0])

    print("\n\n" + "=" * 70)
    print("PATIENT HISTORY CITATION ANALYSIS")
    print("=" * 70)
    cursor.execute(
        "SELECT ai_output_id FROM aIOutputs WHERE type = 'PATIENT_HISTORY' LIMIT 1"
    )
    row = cursor.fetchone()
    if row:
        analyze_output(conn, row[0])

    conn.close()


if __name__ == "__main__":
    main()
