import os
from pathlib import Path


def _detect_assets_root() -> Path:
    """Locate assets directory relative to this file (xlerobot_ws/assets/)."""
    # Go up from: utils/constant.py -> utils/ -> xlerobot_tasks/ -> xlerobot_tasks/ -> source/ -> xlerobot_ws/
    return Path(__file__).resolve().parents[4] / "assets"


def _resolve_assets_root() -> str:
    """Return env override if provided, otherwise default assets directory."""
    env_root = os.environ.get("XLEROBOT_ASSETS_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve().as_posix()

    return _detect_assets_root().resolve().as_posix()


ASSETS_ROOT = _resolve_assets_root()

XLEROBOT_JOINT_NAMES = [
    # Right arm
    "Rotation",
    "Pitch",
    "Elbow",
    "Wrist_Pitch",
    "Wrist_Roll",
    "Jaw",
    # Left arm
    "Rotation_2",
    "Pitch_2",
    "Elbow_2",
    "Wrist_Pitch_2",
    "Wrist_Roll_2",
    "Jaw_2",
    # Head
    "head_pan_joint",
    "head_tilt_joint",
    # Base
    "root_x_axis_joint",
    "root_y_axis_joint",
    "root_z_rotation_joint",
]
