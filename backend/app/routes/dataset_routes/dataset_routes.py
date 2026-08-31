# ================================================================================ #
# dataset routes -> GET, POST, PUT, DELETE
# ================================================================================ #

from pathlib import Path
from uuid import uuid4
from fastapi import (APIRouter, HTTPException, Depends, File, Form, UploadFile)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.auth_dependency import get_current_user, require_roles
from app.dbConfig.database_config import get_db
from app.model.dataset_model import Dataset_Model
from app.model.user_model import User_Model
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
    datasetName: str | None = Form(None),
    dataset_name: str | None = Form(None),
    category: str = Form(...),
    version: str = Form(...),
    source: str = Form(...),
    description: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User_Model = Depends(require_roles("ADMIN", "DS")),
):
    final_dataset_name = datasetName or dataset_name
    if not final_dataset_name:
        raise HTTPException(
            status_code=422,
            detail="datasetName or dataset_name is required"
        )

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
            dataset_name=final_dataset_name,
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


# ======================= route for get the dataset details by id ==========================#
@router.get(
    "/",
    response_model=list[DatasetResponse],
)
def get_dataset(
    db: Session = Depends(get_db),
    current_user: User_Model = Depends(get_current_user),
):
    return get_all_datasets(db)


# ======================= route for get the dataset details by id ===========================#
@router.get(
    "/{dataset_id}",
    response_model=DatasetResponse,
)
def get_dataset_id(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User_Model = Depends(get_current_user),
):
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
    db: Session = Depends(get_db),
    current_user: User_Model = Depends(get_current_user),
):
    dataset = get_dataset_by_id(db, dataset_id)

    if dataset is None:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found...."
        )

    if not dataset.versions:
        raise HTTPException(
            status_code=404,
            detail="No files available for this dataset"
        )

    # Sort or pick the latest version
    latest_version = sorted(dataset.versions, key=lambda v: v.created_at or 0, reverse=True)[0]
    
    file_path = None
    if latest_version.file_path and Path(latest_version.file_path).exists():
        file_path = Path(latest_version.file_path)
    elif latest_version.huggingface_path:
        from app.services.huggingface_service.hf_storage_service import get_hf_storage_service
        try:
            file_path = get_hf_storage_service().download_dataset(latest_version.huggingface_path)
        except Exception as err:
            raise HTTPException(status_code=404, detail=f"Failed to fetch dataset file from Hugging Face: {err}")

    if not file_path or not Path(file_path).exists():
        raise HTTPException(
            status_code=404,
            detail="Dataset file not found on server or Hugging Face repository"
        )

    return FileResponse(
        path=str(file_path),
        filename=latest_version.file_name,
        media_type="application/octet-stream"
    )

# ======================= function for deleting existing dataset from the db ===========================#
@router.delete("/{dataset_id}")
def delete_dataset_id(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User_Model = Depends(require_roles("ADMIN", "DS")),
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


# ======================= routes for dataset versions ===========================#
@router.get("/{dataset_id}/versions")
def list_dataset_versions(
    dataset_id: int,
    db: Session = Depends(get_db)
):
    from app.services.dataset_service.dataset_service import get_dataset_versions
    return get_dataset_versions(db, dataset_id)


@router.get("/versions/{version_id}/download")
def download_dataset_version(
    version_id: int,
    db: Session = Depends(get_db)
):
    from app.services.dataset_service.dataset_service import get_dataset_version_by_id
    version = get_dataset_version_by_id(db, version_id)

    if not version:
        raise HTTPException(
            status_code=404,
            detail="Dataset version not found"
        )

    file_path = None
    if version.file_path and Path(version.file_path).exists():
        file_path = Path(version.file_path)
    elif version.huggingface_path:
        from app.services.huggingface_service.hf_storage_service import get_hf_storage_service
        try:
            file_path = get_hf_storage_service().download_dataset(version.huggingface_path)
        except Exception as err:
            raise HTTPException(status_code=404, detail=f"Failed to fetch dataset version from Hugging Face: {err}")

    if not file_path or not Path(file_path).exists():
        raise HTTPException(
            status_code=404,
            detail="Dataset version file not found on disk or Hugging Face repository"
        )

    return FileResponse(
        path=str(file_path),
        filename=version.file_name,
        media_type="application/octet-stream"
    )

