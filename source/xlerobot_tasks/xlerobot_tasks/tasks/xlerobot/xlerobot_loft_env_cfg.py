from isaaclab.assets import AssetBaseCfg
from isaaclab.utils import configclass
from xlerobot_tasks.assets.scenes import LOFT_CFG, LOFT_USD_PATH
from xlerobot_tasks.utils.general_assets import parse_usd_and_create_subassets

from .xlerobot_env_cfg import (
    XLeRobotDefaultActionsCfg,
    XLeRobotEnvCfg,
    XLeRobotObservationsCfg,
    XLeRobotSceneCfg,
    XLeRobotTerminationsCfg,
)


@configclass
class XLeRobotLoftSceneCfg(XLeRobotSceneCfg):
    """Scene configuration for the XLeRobot in a loft environment."""

    scene: AssetBaseCfg = LOFT_CFG.replace(prim_path="{ENV_REGEX_NS}/Scene")


@configclass
class XLeRobotLoftEnvCfg(XLeRobotEnvCfg):
    """Configuration for the XLeRobot loft environment."""

    scene: XLeRobotLoftSceneCfg = XLeRobotLoftSceneCfg(env_spacing=8.0)

    observations: XLeRobotObservationsCfg = XLeRobotObservationsCfg()
    actions: XLeRobotDefaultActionsCfg = XLeRobotDefaultActionsCfg()

    terminations: XLeRobotTerminationsCfg = XLeRobotTerminationsCfg()

    task_description: str = "XLeRobot dual-arm manipulation in the loft environment."

    def __post_init__(self) -> None:
        super().__post_init__()

        self.viewer.eye = (2.0, -2.0, 2.5)
        self.viewer.lookat = (0.0, 0.0, 0.8)

        parse_usd_and_create_subassets(LOFT_USD_PATH, self)
