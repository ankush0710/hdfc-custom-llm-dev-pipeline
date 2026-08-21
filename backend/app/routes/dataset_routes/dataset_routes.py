# ================================================================================ #
# dataset routes -> GET, POST, PUT, DELETE
# ================================================================================ #

from pathlib import Path
from uuid import uuid4
from fastapi import (APIRouter, HTTPException, Depends, File, Form, UploadFile)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.dbConfig.database_config import get_db
from app.model.dataset_model import Dataset_Model
from app.schema.dataset_schema.dataset_scehma import DatasetResponse
from app.services.dataset_service.dataset_service import (create_dataset, get_all_datasets, get_dataset_by_id, delete_dataset_by_id)

router = APIRouter(
    prefix="/datasets",
    tags=["Datasets"],
)

UPLOAD_DIR = Path("uploads/datasets")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ===================== routes for post to create dataset by multipart form ================#
@router.post(
    "/upload-dataset",
    response_model=DatasetResponse
)
async def upload_dataset(
    datasetName:str = Form(...),
    category: str = Form(...),
    version: str = Form(...),
    source: str = Form(...),
    description: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):

    file_extension=Path(file.filename).suffix.lower()

    allowed_extension={
        ".csv",
        ".xlsx",
        ".jsonl",
        ".json",
    }

    if file_extension not in allowed_extension:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type"
        )

    try:
        return await create_dataset(
            db=db,
            dataset_name=datasetName,
            category=category,
            version=version,
            source=source,
            description=description,
            file=file,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ======================= route for get the dataset details by id ==========================#
@router.get(
    "/",
    response_model=list[DatasetResponse],
)
def get_dataset(db:Session=Depends(get_db)):
    return get_all_datasets(db)


# ======================= route for get the dataset details by id ===========================#
@router.get(
    "/{dataset_id}",
    response_model=DatasetResponse,
)
def get_dataset_id(dataset_id:int, db:Session=Depends(get_db)):
    dataset = get_dataset_by_id(db, dataset_id)

    if dataset is None:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found...."
        )

    return dataset

# =================== function implimanetation to download the dataset ================#
@router.get("/{dataset_id}/download")
def download_dataset(
    dataset_id: int,
    db: Session = Depends(get_db)
):
    dataset = get_dataset_by_id(db, dataset_id)

    if dataset is None:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found...."
        )

    file_path = Path(dataset.file_path)

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Dataset file not found"
        )

    return FileResponse(
        path=str(file_path),
        filename=dataset.file_name,
        media_type="application/octet-stream"
    )

# ======================= function for deleting existing dataset from the db ===========================#
@router.delete("/{dataset_id}")
def delete_dataset_id(
    dataset_id: int,
    db: Session = Depends(get_db)
):
    dataset = delete_dataset_by_id(
        db,
        dataset_id
    )

    if not dataset:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found"
        )

    return {
        "message": "Dataset deleted successfully",
        "dataset_id": dataset_id
    }
