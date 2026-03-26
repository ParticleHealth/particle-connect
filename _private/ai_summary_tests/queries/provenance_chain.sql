-- =============================================================================
-- Query: Full Provenance Chain
-- Dialect: SQLite
-- Description: Traces a citation all the way back to its source XML file.
--              citation → document → recordSource → source file
--              Shows the complete evidence trail for auditability.
-- Tables: aICitations, documentReferences, recordSources, sources
-- =============================================================================

SELECT
    c.citation_id,
    c.text_snippet,
    c.resource_type AS citation_type,
    c.resource_reference_id,

    -- Document level
    d.document_reference_type AS doc_section_type,

    -- Source file level
    rs.source_id,
    s.source_name AS source_file

FROM aICitations c

-- Resolve to document
LEFT JOIN documentReferences d
    ON c.resource_reference_id = d.document_reference_id
    AND c.resource_type = 'DocumentReferences'

-- Resolve to record source mapping
LEFT JOIN recordSources rs
    ON c.resource_reference_id = rs.resource_id

-- Resolve to source file
LEFT JOIN sources s
    ON rs.source_id = s.source_id

WHERE c.ai_output_id = (
    SELECT ai_output_id FROM aIOutputs
    WHERE type = 'DISCHARGE_SUMMARY' LIMIT 1
)
ORDER BY s.source_name, d.document_reference_type;
