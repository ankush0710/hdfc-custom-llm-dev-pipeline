import platform
import torch


def get_hardware_profile():
    profile = {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "pytorch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "cuda_version": torch.version.cuda,
    }

    if torch.cuda.is_available():
        device = torch.cuda.current_device()
        properties = torch.cuda.get_device_properties(device)

        profile.update(
            {
                "gpu_name": properties.name,
                "gpu_memory_gb": round(
                    properties.total_memory / (1024**3), 2
                ),
                "compute_capability": (
                    f"{properties.major}.{properties.minor}"
                ),
                "device_index": device,
            }
        )
    else:
        profile.update(
            {
                "gpu_name": "CPU",
                "gpu_memory_gb": 0,
                "compute_capability": None,
                "device_index": None,
            }
        )

    return profile


if __name__ == "__main__":
    profile = get_hardware_profile()

    print("\n=== HDFC AI HARDWARE PROFILE ===")

    for key, value in profile.items():
        print(f"{key}: {value}")