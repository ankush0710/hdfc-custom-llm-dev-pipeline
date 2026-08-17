import os
import uuid
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.model.dataset_model import Dataset_Model

UPLOAD_FILE = "Uploads/datasets"

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

    extension = os.path.splitext(
        original_filename
    )[1].lower()

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
    
    file_size = len(file_content) / (1024*1024)

    dataset = Dataset_Model(
        dataset_name = dataset_name,
        category = category,
        version = version,
        source = source,
        description = description,
        file_name = original_filename,
        file_path = file_path,
        file_type = extension.replace(".", "").upper(),
        file_size = file_size,
        status = "Uploaded"
    )

    db.add(dataset)
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

#========= function implementation for get the dataset info by id from  =================#
def get_dataset_by_id(db: Session, dataset_id: int):
    return(
        db.query(Dataset_Model)
        .filter(Dataset_Model.id == dataset_id)
        .first()
    )
