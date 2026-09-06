"""
backend/app/services/inference_service/inference_service.py

Control plane inference service for registered models.
Validates database model records and dispatches computation to the dedicated ML Service.
Zero torch/transformers dependencies.
"""
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.clients.ml_client import MLClient
from app.core.path_utils import resolve_artifact_path, validate_artifact_directory
from app.model.deployment_model import Deployment
from app.model.model_registry import Model_Registry
from app.schema.inference_schema.inference_schema import SUPPORTED_TASK_TYPES
from ai.inference.guardrails import BankingDomainGuardrail

logger = logging.getLogger(__name__)

INFERENCE_ALLOWED_STATUSES = {
    "DEPLOYED",
}


class InferenceService:

    def __init__(self, db: Session):
        self.db = db

    def predict(
        self,
        model_id: int,
        task_type: str,
        question: str,
        context: Optional[str] = None,
        max_new_tokens: int = int(os.getenv("AI_MAX_NEW_TOKENS", "256")),
        temperature: float = float(os.getenv("AI_TEMPERATURE", "0.7")),
        top_p: float = float(os.getenv("AI_TOP_P", "0.9")),
        do_sample: bool = os.getenv("AI_DO_SAMPLE", "true").lower() == "true",
        seed: int = 42,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:

        # Guardrail check: intercept out-of-domain queries early before ML dispatch
        guard_result = BankingDomainGuardrail.validate_query(question)
        if not guard_result.is_valid_banking_query:
            logger.info("Guardrail rejected non-banking query in backend InferenceService: '%s'", question[:80])
            refusal_msg = guard_result.refusal_message or "I can only assist with banking and financial-services related queries."
            return {
                "model_id": model_id,
                "model_name": f"Model #{model_id}",
                "fine_tuned": False,
                "task_type": task_type,
                "question": question,
                "context": context,
                "response": refusal_msg,
                "raw_response": refusal_msg,
                "latency_seconds": 0.001,
                "tokens_generated": 0,
                "device": "guardrail",
            }

        # 0. Validate task type
        if task_type not in SUPPORTED_TASK_TYPES:
            raise ValueError(
                f"The selected task type '{task_type}' is not supported. "
                f"Supported task types: {', '.join(sorted(SUPPORTED_TASK_TYPES))}"
            )

        # 1. Find model in PostgreSQL
        model = (
            self.db.query(Model_Registry)
            .filter(Model_Registry.id == model_id)
            .first()
        )

        if model is None:
            raise ValueError(f"Model ID '{model_id}' was not found in the Model Registry.")

        # 2. Check model status
        if model.status not in INFERENCE_ALLOWED_STATUSES:
            raise ValueError(
                f"Model '{model.model_name}' (v{model.version}) has status '{model.status}'. "
                f"Inference is only allowed for models with status in {sorted(INFERENCE_ALLOWED_STATUSES)}."
            )

        # 2b. Check active deployment in PostgreSQL
        active_deployment = (
            self.db.query(Deployment)
            .filter(Deployment.model_id == model.id, Deployment.status == "ACTIVE")
            .first()
        )
        if not active_deployment:
            raise ValueError(
                f"Model '{model.model_name}' (ID: {model.id}) does not have an ACTIVE deployment. "
                "Inference is only permitted for models with an active deployment record."
            )

        # 3. Resolve metadata
        raw_target_path = model.adapter_path or model.artifact_path
        hf_path = model.huggingface_path

        # 4. Dispatch inference to ML Service via MLClient
        start_time = time.perf_counter()

        ml_result = MLClient.predict(
            model_id=model.id,
            task_type=task_type,
            question=question,
            context=context,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            do_sample=do_sample,
            seed=seed,
            adapter_path_override=raw_target_path,
            base_model_override=model.base_model,
            huggingface_path=hf_path,
            request_id=request_id,
        )

        latency = time.perf_counter() - start_time

        # 5. Resolve real-time dataset lineage from relational DB chain
        from app.model.training_job_model import TrainingJobModel
        from app.model.training_model import Training_Model
        from app.model.dataset_version_model import Dataset_Version_Model
        from app.model.dataset_model import Dataset_Model
        from app.model.evaluation_run_model import Evaluation_Model

        training_run_id = None
        if model.training_job_id:
            job = self.db.query(TrainingJobModel).filter(TrainingJobModel.id == model.training_job_id).first()
            if job and job.training_run_id:
                training_run_id = job.training_run_id
            if not training_run_id:
                direct_run = self.db.query(Training_Model).filter(Training_Model.id == model.training_job_id).first()
                if direct_run:
                    training_run_id = direct_run.id
        if not training_run_id and getattr(model, "evaluation_id", None):
            ev = self.db.query(Evaluation_Model).filter(Evaluation_Model.evaluation_id == model.evaluation_id).first()
            if ev:
                training_run_id = ev.run_id

        dataset_id = None
        dataset_name = None
        dataset_version = None
        dataset_file_name = None

        if training_run_id:
            run = self.db.query(Training_Model).filter(Training_Model.id == training_run_id).first()
            if run and run.dataset_version_id:
                dv = self.db.query(Dataset_Version_Model).filter(Dataset_Version_Model.id == run.dataset_version_id).first()
                if dv:
                    dataset_id = dv.dataset_id
                    dataset_version = dv.version
                    dataset_file_name = dv.file_name
                    if dv.dataset_id:
                        ds = self.db.query(Dataset_Model).filter(Dataset_Model.id == dv.dataset_id).first()
                        if ds:
                            dataset_name = ds.dataset_name

        # 6. Format return payload matching existing API contract with real-time lineage
        response_text = ml_result.get("response", ml_result.get("text", str(ml_result)))
        tokens_count = ml_result.get("tokens_generated")
        if tokens_count is None and isinstance(response_text, str):
            tokens_count = len(response_text.split())

        return {
            "model_id": model.id,
            "model_name": model.model_name,
            "fine_tuned": ml_result.get("fine_tuned", False),
            "task_type": task_type,
            "question": question,
            "context": context,
            "response": response_text,
            "raw_response": str(ml_result),
            "latency_seconds": round(latency, 4),
            "tokens_generated": tokens_count,
            "device": ml_result.get("device"),
            "dataset_id": dataset_id,
            "dataset_name": dataset_name,
            "dataset_version": dataset_version,
            "dataset_file_name": dataset_file_name,
            "training_run_id": training_run_id,
        }