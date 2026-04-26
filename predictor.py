from __future__ import annotations

import platform

try:
    import torch
except Exception:  # pragma: no cover
    torch = None


def get_accelerator_info() -> dict[str, str | bool | int]:
    info: dict[str, str | bool | int] = {
        "os": f"{platform.system()} {platform.release()}",
        "torch_available": torch is not None,
        "cuda_available": False,
        "device": "cpu",
        "gpu_name": "",
        "gpu_count": 0,
    }
    if torch is None:
        return info

    cuda = bool(torch.cuda.is_available())
    info["cuda_available"] = cuda
    if cuda:
        info["device"] = "cuda"
        info["gpu_count"] = int(torch.cuda.device_count())
        info["gpu_name"] = str(torch.cuda.get_device_name(0))
    return info
