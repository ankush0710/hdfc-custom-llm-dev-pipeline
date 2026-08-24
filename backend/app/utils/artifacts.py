from pathlib import Path


AI_ARTIFACT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[3]
    / "ai"
    / "artifacts"
)


def get_artifact_path(
    model_name: str,
    version: str,
) -> Path:

    path = (
        AI_ARTIFACT_ROOT
        / model_name
        / version
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Model artifact not found: {path}"
        )

    return path