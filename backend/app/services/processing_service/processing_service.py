# import required default libraries
import os
from datetime import datetime
import pandas as pd
from sqlalchemy.orm import Session

# import all required models 
from app.model.dataset_processing_model import Processing_Model
from app.model.quality_metrics_model import Quality_Model
from app.model.dataset_version_model import Dataset_Version_Model

# import all processors methods
from app.processor.cleaner import clean_file
from app.processor.validator import load_file, resolve_file_path
from app.processor.calculate_quality_metrics import calculate_quality_metrics
from app.processor.deDuplicator import remove_duplicate
from app.utils.file_utils import create_processed_path

def process_dataset(db: Session, dataset_version_id: int, operations: list[str]):
    dataset_version = (
        db.query(Dataset_Version_Model).filter(Dataset_Version_Model.id == dataset_version_id).first()
    )

    if not dataset_version:
        raise ValueError(
            "Dataset version not found"
        )
    
    input_file = resolve_file_path(dataset_version.file_path)

    job = Processing_Model(
        dataset_version_id = dataset_version_id,
        status = "Running",
        input_file = input_file,
        started_at = datetime.utcnow()
    )

    db.add(job)
    db.commit()
    db.refresh(job)


    try:
        # =========================== #
        # TO LOAD DATASET
        # =========================== #
        df = load_file(input_file)

        duplicate_count = 0

        # =========================== #
        # TO CLEAN DATASET
        # =========================== #
        if "clean" in operations:
            df = clean_file(df)

        # =========================== #
        # TO REMOVE DUPLICATE
        # =========================== #

        if "remove_duplicate" in operations:
            df, duplicate_count = remove_duplicate(df)

        # =========================== #
        # TO CHECK QUALITY METRICS
        # =========================== #
        metrics = calculate_quality_metrics(df, duplicate_rows=duplicate_count)

        # =========================== #
        # TO SAVED PROCCESSED DATA
        # =========================== #
        output_file = create_processed_path(
            dataset_version_id,
            input_file
        )

        extension = os.path.splitext(output_file)[1].lower()

        if extension == ".csv":
            df.to_csv(output_file, index=False)

        elif extension == ".xlsx":
            df.to_excel(output_file, index=False)

        elif extension == ".json":
            df.to_json(output_file, orient="records")

        elif extension == ".jsonl":
            df.to_json(output_file, orient="records", lines=True)

        # =========================== #
        # TO UPDATE PROCESSING JOB
        # =========================== #
        job.status = "COMPLETED"
        job.output_file = output_file
        job.completed_at = datetime.utcnow()

        # =========================== #
        # MARK ORIGINAL VERSION AS PROCESSED
        # This is the critical lineage link: training enforces status="Processed"
        # on the dataset_version_id passed to it. Without updating here, training
        # would always be blocked with HTTP 400.
        # =========================== #
        dataset_version.status = "Processed"

        # ============================ #
        # SAVE METRICS
        # ============================ #
        quality = Quality_Model(
            job_id=job.id,
            total_rows=metrics["total_rows"],
            total_columns=metrics["total_columns"],
            duplicate_rows=metrics["duplicate_rows"],
            missing_values=metrics["missing_values"],
            empty_rows=metrics["empty_rows"],
            quality_score=metrics["quality_score"]
        )

        db.add(quality)

        # ============================ #
        # REGISTER CLEANED DATASET VERSION
        # ============================ #
        cleaned_version_name = f"{dataset_version.version}-cleaned"
        existing_version = (
            db.query(Dataset_Version_Model)
            .filter(
                Dataset_Version_Model.dataset_id == dataset_version.dataset_id,
                Dataset_Version_Model.version == cleaned_version_name
            )
            .first()
        )

        if not existing_version and os.path.exists(output_file):
            file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
            cleaned_version = Dataset_Version_Model(
                dataset_id=dataset_version.dataset_id,
                version=cleaned_version_name,
                file_name=os.path.basename(output_file),
                file_path=output_file,
                file_size=file_size_mb,
                file_type=extension.replace(".", "").upper(),
                status="Processed"
            )
            db.add(cleaned_version)

        db.commit()

        return job, metrics

    except Exception as error:

        job.status = "FAILED"
        job.error_message = str(error)
        job.completed_at = datetime.utcnow()
        db.commit()

        raise error


def get_processing_metrics(db: Session, job_id: int):
    return db.query(Quality_Model).filter(Quality_Model.job_id == job_id).first()




        

