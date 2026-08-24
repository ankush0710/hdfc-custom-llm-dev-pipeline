import os


AI_DEVICE = os.getenv("AI_DEVICE", "auto")

AI_DEFAULT_MODEL = os.getenv(
    "AI_DEFAULT_MODEL",
    "qwen3_0_6b"
)

AI_MAX_NEW_TOKENS = int(
    os.getenv("AI_MAX_NEW_TOKENS", "256")
)

AI_TEMPERATURE = float(
    os.getenv("AI_TEMPERATURE", "0.2")
)

AI_TOP_P = float(
    os.getenv("AI_TOP_P", "0.9")
)

AI_DO_SAMPLE = os.getenv(
    "AI_DO_SAMPLE",
    "false"
).lower() == "true"