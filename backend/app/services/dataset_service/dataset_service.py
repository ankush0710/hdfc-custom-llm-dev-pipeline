import os
import uuid
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.model.dataset_model import Dataset_Model
from app.model.dataset_version_model import Dataset_Version_Model

UPLOAD_FILE = "uploads/datasets"

#========= function implementation to create the dataset table in the databse ===========#
async def create_dataset(
    db:Session,
    dataset_name: str,
    category: str,
    version: str,
    source: str,
    description: str | None,
    file: UploadFile
):
    os.makedirs(UPLOAD_FILE, exist_ok=True)
    original_filename = file.filename or "uploaded_file"

    extension = os.path.splitext(original_filename)[1].lower()
    unique_filename = (
        f"{uuid.uuid4()}{extension}"
    )

    file_path = os.path.join(
        UPLOAD_FILE,
        unique_filename
    )
    file_content=await file.read()

    with open(file_path, "wb") as buffer:
        buffer.write(file_content)
    
    # Store the size in megabytes.
    file_size = len(file_content) / (1024 * 1024)

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

        # Remove uploaded physical file
        if os.path.exists(file_path):
            os.remove(file_path)

        raise ValueError(
            f"Dataset version '{version}' already exists."
            f"for dataset '{dataset_name}'."
        )


# ============= create dataset versioning ================================================#
    dataset_version = Dataset_Version_Model(
        dataset_id = dataset.id,
        version = version,
        file_name = original_filename,
        file_path = file_path,
        file_size = file_size,
        file_type = extension.replace(".", "").upper(),
        file_hash = None,
        status = "Uploaded",
        is_safe_for_training = False,
        pii_scan_status = "PENDING",
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
