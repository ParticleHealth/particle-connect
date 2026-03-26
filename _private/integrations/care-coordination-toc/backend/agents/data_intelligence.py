"""Agent 1: Data Intelligence — fetches and analyzes Particle patient data."""

import json
import logging

from agents.base import BaseAgent
from database import Database
from services.particle_client import ParticleClient
from services.call_context import build_call_context, analyze_care_gaps

logger = logging.getLogger(__name__)


class DataIntelligenceAgent(BaseAgent):
    """Pulls patient data from Particle API and builds structured context."""

    async def run(self, workflow_id: str) -> dict:
        workflow = self.db.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        demographics = json.loads(workflow["patient_demographics_json"] or "{}")

        client = ParticleClient()
        try:
            logger.info("Authenticating with Particle...")
            await client.authenticate()

            logger.info("Registering patient: %s %s", demographics.get("given_name"), demographics.get("family_name"))
            resp = await client.register_patient(demographics)
            particle_patient_id = resp.get("particle_patient_id")
            if not particle_patient_id:
                raise RuntimeError(f"No particle_patient_id in response: {resp}")

            logger.info("Submitting query for patient %s", particle_patient_id)
            await client.submit_query(particle_patient_id)

            logger.info("Waiting for query completion...")
            result = await client.wait_for_query(particle_patient_id)
            status = result.get("state", result.get("status", "UNKNOWN"))
            if status == "FAILED":
                raise RuntimeError(f"Query failed: {result}")

            logger.info("Retrieving flat data...")
            flat_data = await client.get_flat_data(particle_patient_id)

            context = build_call_context(flat_data, particle_patient_id)
            care_gaps = analyze_care_gaps(context, flat_data)

            self.db.store_patient_context(workflow_id, context, care_gaps)

            resource_counts = {
                k: len(v) if isinstance(v, list) else 0
                for k, v in flat_data.items()
            }

            return {
                "patient_context": context,
                "care_gaps": care_gaps,
                "resource_counts": resource_counts,
                "status": "complete",
            }
        finally:
            await client.close()

    def validate_preconditions(self, workflow_id: str) -> bool:
        workflow = self.db.get_workflow(workflow_id)
        return workflow is not None and workflow["status"] in ("pending", "data_gathering")
