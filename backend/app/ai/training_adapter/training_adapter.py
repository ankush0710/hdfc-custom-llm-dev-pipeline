from pathlib import Path

from ai.training.config import TrainingConfig
from ai.training.model import prepare_model
from ai.training.trainer import train_model


class AITrainingAdapter:

    @staticmethod
    def train(
        base_model: str,
        dataset_path: str,
        output_dir: str,
        epochs: float = 1.0,
        learning_rate: float = 2e-4,
        batch_size: int = 1,
        max_seq_length: int = 256,
    ):

        config = TrainingConfig(
            base_model=base_model,
            dataset_path=Path(dataset_path),
            output_dir=Path(output_dir),
            num_train_epochs=epochs,
            learning_rate=learning_rate,
            per_device_train_batch_size=batch_size,
            max_seq_length=max_seq_length,
        )

        config.validate()

        model = prepare_model(config)

        raise NotImplementedError(
            "Expose the existing training dataset preparation "
            "from ai.training.train.py as a Python function before "
            "connecting the training worker."
        )