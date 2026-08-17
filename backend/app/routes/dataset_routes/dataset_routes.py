from fastapi import (APIRouter, HTTPException, Depends, File, Form, UploadFile)
from sqlalchemy.orm import Session
from app.dbConfig.database_config import get_db
from app.schema.dataset_schema.dataset_scehma import DatasetResponse
from app.services.dataset_service.dataset_service import (create_dataset, get_all_datasets, get_dataset_by_id)

router = APIRouter(
    prefix="/api/datasets",
    tags=["Datasets"],
)

# ===================== routes for post to create dataset by multipart form ================#
@router.post(
    "/",
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

    return await create_dataset(
        db=db,
        dataset_name=datasetName,
        category=category,
        version=version,
        source=source,
        description=description,
        file=file,
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
