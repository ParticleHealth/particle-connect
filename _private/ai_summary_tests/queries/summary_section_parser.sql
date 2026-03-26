-- =============================================================================
-- Query: Summary Section Inventory
-- Dialect: SQLite
-- Description: Extracts the section headers from discharge summary text to
--              understand the template structure. Uses INSTR to find known
--              section markers. This helps build a programmatic section parser.
-- Tables: aIOutputs
-- =============================================================================

SELECT
    ai_output_id,
    type,
    LENGTH(text) AS total_length,

    -- Check which sections exist in the text
    CASE WHEN INSTR(text, 'Hospital Course Summary:') > 0
         THEN INSTR(text, 'Hospital Course Summary:') ELSE NULL END AS hospital_course_pos,
    CASE WHEN INSTR(text, 'Admit Diagnosis') > 0
         THEN INSTR(text, 'Admit Diagnosis') ELSE NULL END AS admit_dx_pos,
    CASE WHEN INSTR(text, 'Discharge Diagnosis') > 0
         THEN INSTR(text, 'Discharge Diagnosis') ELSE NULL END AS discharge_dx_pos,
    CASE WHEN INSTR(text, 'Results:') > 0
         THEN INSTR(text, 'Results:') ELSE NULL END AS results_pos,
    CASE WHEN INSTR(text, 'Orders:') > 0
         THEN INSTR(text, 'Orders:') ELSE NULL END AS orders_pos,
    CASE WHEN INSTR(text, 'Follow Ups') > 0
         THEN INSTR(text, 'Follow Ups') ELSE NULL END AS followups_pos,
    CASE WHEN INSTR(text, 'Social:') > 0
         THEN INSTR(text, 'Social:') ELSE NULL END AS social_pos,

    -- Section presence flags
    (INSTR(text, 'Hospital Course Summary:') > 0) AS has_hospital_course,
    (INSTR(text, 'Admit Diagnosis') > 0) AS has_admit_dx,
    (INSTR(text, 'Discharge Diagnosis') > 0) AS has_discharge_dx,
    (INSTR(text, 'Results:') > 0) AS has_results,
    (INSTR(text, 'Orders:') > 0) AS has_orders,
    (INSTR(text, 'Follow Ups') > 0) AS has_followups

FROM aIOutputs
WHERE type = 'DISCHARGE_SUMMARY'
ORDER BY ai_output_id;
