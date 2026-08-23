from datetime import datetime, timezone
from sqlalchemy import Session
from app.model.evaluation_run_model import Evaluation_Run_Model
from app.model.evaluation_metric_models import Evaluation_Metric_Model
from app.model.evaluation_result_model import Evaluation_Result_Model
from app.evaluation.registry import get_evaluator


# ================================ create the evaluation runs ====================================== #
def creat_evaluation_run(db:Session, training_run_id:int, evaluator_type:str, evaluation_dataset_version_id: int | None=None, model_path: str | None=None):

    evaluation_run = Evaluation_Run_Model(
        training_run_id = training_run_id,
        evaluator_type = evaluator_type,
        evaluation_dataset_version_id = evaluation_dataset_version_id,
        model_path = model_path,
        status = "QUEUED"
    )
    db.add(evaluation_run)
    db.commit()
    db.refresh(evaluation_run)
    return evaluation_run

# ======================= To list of all evaluation runs -> running, queued, completed, failed ================================== #
def list_evaluation_run(db:Session, training_run_id: int | None=None):

    query = db.query(Evaluation_Run_Model)

    if training_run_id:
        query = query.filter(Evaluation_Run_Model.training_run_id == training_run_id)
        
    return (query.order_by(Evaluation_Run_Model.created_at.desc()).all())
        

# =========================== To execute the specific evaluation run ================================== #
def execute_evaluation(db:Session, evaluation_id:int, dataset_path:id):

    evaluation_run = get_evaluation_run(db, evaluation_id)

    if not evaluation_run:
        raise ValueError("Evaluation run not found")

    try:
        evaluation_run.status = "RUNNING"

        evaluation_run.started_at = datetime.now(timezone.utc)

        db.commit()

        evaluator = get_evaluator(evaluator_run.evaluator_type)
        result = evaluator.evaluate(model_path = evaluation_run.model_path, dataset_path = dataset_path)
        metrics = result.get("metrics", {})
        results = result.get("results", [])\

        for metric_name, metric_value in metrics.items():

            metric = Evaluation_Metric_Model(
                evaluation_run_id = evaluation_run.id,
                metric_name = metric_name,
                metric_value = float(metric_value)
            )
            db.add(metric)


        for item in results:

            evaluation_result = (
                Evaluation_Result_Model(
                    evaluation_run_id = evaluation_run.id,

                    sample_id = item.get(
                        "sample_id",
                        ""
                    ),
                    input_text = item.get(
                        "input_text",

                    ),
                     expected_output=item.get(
                        "expected_output"
                    ),

                    actual_output=item.get(
                        "actual_output"
                    ),

                    score=item.get(
                        "score"
                    ),

                    status=item.get(
                        "status"
                    )
                )
            )
            db.add(evaluation_result)

        evaluation_run.status = "COMPLETED"
        evaluation_run.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(evaluation_result)

        return evaluation_run

    except Exception as exc:

        evaluation_run.status = "FAILED"
        evaluation_run.error_message = str(exc)
        evaluation_run.completed_at = datetime.now(timezone.utc)
        db.commit()
        raise



