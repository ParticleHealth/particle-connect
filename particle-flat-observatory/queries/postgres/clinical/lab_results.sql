-- =============================================================================
-- Query: Lab Results
-- Requirement: CLIN-04
-- Dialect: PostgreSQL
-- Description: Returns all lab observations for a patient with values, units,
--              and interpretation. Includes diagnostic report context for
--              grouping. The lab_interpretation column is included but may be
--              NULL if the data source does not provide it.
-- Parameters: patient_id = '6f3bc061-8515-41b9-bc26-75fc55f53284' (replace with your patient_id)
-- Parameterized: WHERE "patient_id" = :patient_id
-- Tables used: labs
-- =============================================================================

SELECT
  "lab_name",
  "lab_code",
  "lab_code_system",
  CAST("lab_value_quantity" AS NUMERIC) AS value_numeric,
  "lab_unit",
  "lab_interpretation",
  -- Uncomment to add reference range annotations based on common LOINC codes:
  -- CASE
  --   WHEN "lab_code" = '2093-3' AND CAST("lab_value_quantity" AS NUMERIC) > 200 THEN 'HIGH'   -- Total Cholesterol > 200 mg/dL
  --   WHEN "lab_code" = '2571-8' AND CAST("lab_value_quantity" AS NUMERIC) > 1.2 THEN 'HIGH'   -- Creatinine > 1.2 mg/dL
  --   WHEN "lab_code" = '2345-7' AND CAST("lab_value_quantity" AS NUMERIC) > 100 THEN 'HIGH'   -- Glucose > 100 mg/dL
  --   WHEN "lab_code" = '2160-0' AND CAST("lab_value_quantity" AS NUMERIC) > 1.2 THEN 'HIGH'   -- Creatinine > 1.2 mg/dL
  --   WHEN "lab_code" = '3094-0' AND CAST("lab_value_quantity" AS NUMERIC) > 20 THEN 'HIGH'    -- BUN > 20 mg/dL
  --   WHEN "lab_code" = '2823-3' AND CAST("lab_value_quantity" AS NUMERIC) > 5.0 THEN 'HIGH'   -- Potassium > 5.0 mEq/L
  --   WHEN "lab_code" = '2823-3' AND CAST("lab_value_quantity" AS NUMERIC) < 3.5 THEN 'LOW'    -- Potassium < 3.5 mEq/L
  --   WHEN "lab_code" = '2951-2' AND CAST("lab_value_quantity" AS NUMERIC) > 145 THEN 'HIGH'   -- Sodium > 145 mEq/L
  --   WHEN "lab_code" = '2951-2' AND CAST("lab_value_quantity" AS NUMERIC) < 135 THEN 'LOW'    -- Sodium < 135 mEq/L
  --   ELSE NULL
  -- END AS computed_flag,
  "lab_value_string",
  "lab_value_code",
  CAST("lab_timestamp" AS TIMESTAMPTZ) AS lab_time,
  "diagnostic_report_name",
  "diagnostic_report_id",
  "lab_observation_id"
FROM labs
WHERE "patient_id" = '6f3bc061-8515-41b9-bc26-75fc55f53284'  -- Replace with your patient_id
ORDER BY
  CAST("lab_timestamp" AS TIMESTAMPTZ) DESC,
  "lab_name";
