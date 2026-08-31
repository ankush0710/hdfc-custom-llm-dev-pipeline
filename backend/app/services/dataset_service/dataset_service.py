import hashlib
import os
import uuid
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.model.dataset_model import Dataset_Model
from app.model.dataset_version_model import Dataset_Version_Model
from app.services.huggingface_service.hf_storage_service import get_hf_storage_service

#========= function implementation to create the dataset table in the databse ===========#
async def create_dataset(
    db: Session,
    dataset_name: str,
    category: str,
    version: str,
    source: str,
    description: str | None,
    file: UploadFile
):
    original_filename = file.filename or "uploaded_file"
    extension = os.path.splitext(original_filename)[1].lower()
    
    file_content = await file.read()
    file_size_mb = len(file_content) / (1024 * 1024)
    file_hash = hashlib.sha256(file_content).hexdigest()

    dataset = (db.query(Dataset_Model).filter(Dataset_Model.dataset_name == dataset_name).first())

    # ================ create dataset ========================================== #
    if not dataset:
        dataset = Dataset_Model(
            dataset_name = dataset_name,
            category = category,
            source = source,
            description = description,
        )
        db.add(dataset)
        db.flush()

    # ================== check dataset version already exists ==================================
    existing_version = (
        db.query(Dataset_Version_Model)
        .filter(
            Dataset_Version_Model.dataset_id == dataset.id,
            Dataset_Version_Model.version == version
        )
        .first()
    )

    if existing_version:
        raise ValueError(
            f"Dataset version '{version}' already exists for dataset '{dataset_name}'."
        )

    # ============= Upload actual dataset to Hugging Face Hub ================================#
    hf_service = get_hf_storage_service()
    hf_upload = hf_service.upload_dataset(
        file_path_or_bytes=file_content,
        filename=original_filename,
        dataset_id=dataset.id,
        version=version,
        category="raw",
        commit_message=f"Add raw dataset '{dataset_name}' v{version}",
    )

    # ============= create dataset versioning metadata in Neon ===============================#
    dataset_version = Dataset_Version_Model(
        dataset_id = dataset.id,
        version = version,
        file_name = original_filename,
        file_path = hf_upload["huggingface_path"],
        file_size = file_size_mb,
        file_type = extension.replace(".", "").upper() if extension else "CSV",
        file_hash = file_hash,
        status = "Uploaded",
        is_safe_for_training = False,
        pii_scan_status = "PENDING",
        huggingface_repo = hf_upload["huggingface_repo"],
        huggingface_path = hf_upload["huggingface_path"],
        commit_hash = hf_upload["commit_hash"],
    )

    db.add(dataset_version)
    db.commit()
    db.refresh(dataset)
    return dataset


#========= function implementation for get all the dataset info from databse =============#
def get_all_datasets(db: Session):
    return (
        db.query(Dataset_Model)
        .order_by(Dataset_Model.created_at.desc())
        .all()
    )

#========= function implementation for get the dataset info by id from posgres =================#
def get_dataset_by_id(db: Session, dataset_id: int):
    return(
        db.query(Dataset_Model)
        .filter(Dataset_Model.id == dataset_id)
        .first()
    )

#========= function implementation to delete the dataset info by id from posgres =================#
def delete_dataset_by_id(
    db: Session,
    dataset_id: int
):
    dataset = (
        db.query(Dataset_Model)
        .filter(Dataset_Model.id == dataset_id)
        .first()
    )

    if not dataset:
        return None

    # Delete physical file
    for version in dataset.versions:

        if (
            version.file_path
            and os.path.exists(version.file_path)
        ):
            os.remove(version.file_path)

    db.delete(dataset)
    db.commit()

    return dataset


def get_dataset_versions(db: Session, dataset_id: int):
    return (
        db.query(Dataset_Version_Model)
        .filter(Dataset_Version_Model.dataset_id == dataset_id)
        .order_by(Dataset_Version_Model.created_at.desc())
        .all()
    )


def get_dataset_version_by_id(db: Session, version_id: int):
    return (
        db.query(Dataset_Version_Model)
        .filter(Dataset_Version_Model.id == version_id)
        .first()
    )
