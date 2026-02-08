-- =============================================================================
-- Query: Vital Sign Trends
-- Requirement: CLIN-05
-- Dialect: PostgreSQL
-- Description: Returns true vital sign observations (BP, HR, RR, O2 sat, temp,
--              BMI) filtered by LOINC codes. The vital_signs table contains 116
--              rows including lab-like observations; this query filters to only
--              clinically recognized vital signs. Handles the leading comma in
--              vital_sign_observation_time by stripping it before timestamp cast.
-- Parameters: patient_id = '6f3bc061-8515-41b9-bc26-75fc55f53284' (replace with your patient_id)
-- Parameterized: WHERE "patient_id" = :patient_id
-- Tables used: vital_signs
-- =============================================================================

WITH vital_loinc_codes AS (
  -- Define the LOINC codes that represent true vital signs
  SELECT unnest(ARRAY[
    '8480-6',   -- Systolic Blood Pressure
    '8462-4',   -- Diastolic Blood Pressure
    '8867-4',   -- Heart Rate
    '9279-1',   -- Respiratory Rate
    '2708-6',   -- O2 Saturation (arterial)
    '59408-5',  -- O2 Saturation (pulse oximetry)
    '8310-5',   -- Body Temperature
    '39156-5'   -- BMI
  ]) AS loinc_code
),

parsed_vitals AS (
  SELECT
    vs."vital_sign_observation_name",
    vs."vital_sign_observation_code",
    CAST(vs."vital_sign_observation_value" AS NUMERIC) AS observation_value,
    vs."vital_sign_observation_unit" AS observation_unit,
    -- CRITICAL: Strip leading comma-space before casting to timestamp
    -- Raw values look like: ", 2011-05-28T15:19:11+0000"
    CAST(LTRIM(vs."vital_sign_observation_time", ', ') AS TIMESTAMPTZ) AS observation_time,
    vs."vital_sign_observation_id",
    vs."vital_sign_grouping_observation_id"
  FROM vital_signs vs
  INNER JOIN vital_loinc_codes lc
    ON vs."vital_sign_observation_code" = lc.loinc_code
  WHERE vs."patient_id" = '6f3bc061-8515-41b9-bc26-75fc55f53284'  -- Replace with your patient_id
)

SELECT
  "vital_sign_observation_name",
  "vital_sign_observation_code",
  observation_value,
  observation_unit,
  observation_time,
  "vital_sign_observation_id",
  "vital_sign_grouping_observation_id"
FROM parsed_vitals
ORDER BY
  observation_time DESC,
  "vital_sign_observation_name";
