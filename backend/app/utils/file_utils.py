import os
import uuid

processed_dir = "storage/processed"

def create_processed_path(dataset_id: int, original_path: str):
    os.makedirs(processed_dir, exist_ok=True)

    extension = os.path.splitext(original_path)[-1]

    unique_id = uuid.uuid4.hex[:8]

    filename = (
        f"dataset_{dataset_id}",
        f"processed_{unique_id}",
        f"{extension}"
    )

    return os.path.join(
        processed_dir,
        filename
    )
