import torch
from isaaclab.assets import AssetBaseCfg
from isaaclab.managers import ObservationGroupCfg as ObsGroup
from isaaclab.managers import ObservationTermCfg as ObsTerm
from isaaclab.managers import SceneEntityCfg
from isaaclab.managers import TerminationTermCfg as DoneTerm
from isaaclab.utils import configclass
from xlerobot_tasks.assets.scenes import TABLE_WITH_CUBE_CFG, TABLE_WITH_CUBE_USD_PATH
from xlerobot_tasks.utils.domain_randomization import (
    domain_randomization,
    randomize_object_uniform,
)
from xlerobot_tasks.utils.general_assets import parse_usd_and_create_subassets

from . import mdp
from .xlerobot_env_cfg import (
    XLeRobotDefaultActionsCfg,
    XLeRobotEnvCfg,
    XLeRobotObservationsCfg,
    XLeRobotSceneCfg,
    XLeRobotTerminationsCfg,
)


@configclass
class XLeRobotLiftCubeSceneCfg(XLeRobotSceneCfg):
    """Scene configuration for the XLeRobot lift cube task."""

    scene: AssetBaseCfg = TABLE_WITH_CUBE_CFG.replace(prim_path="{ENV_REGEX_NS}/Scene")


@configclass
class XLeRobotLiftCubeObservationsCfg(XLeRobotObservationsCfg):
    """Observations for the lift cube task with grasp detection."""

    @configclass
    class SubtaskCfg(ObsGroup):
        """Observations for subtask group."""

        pick_cube = ObsTerm(
            func=mdp.object_grasped_right,
            params={
                "robot_cfg": SceneEntityCfg("robot"),
                "ee_frame_cfg": SceneEntityCfg("right_ee_frame"),
                "object_cfg": SceneEntityCfg("cube"),
            },
        )

        def __post_init__(self):
            self.enable_corruption = False
            self.concatenate_terms = False

    subtask_terms: SubtaskCfg = SubtaskCfg()


@configclass
class XLeRobotLiftCubeTerminationsCfg(XLeRobotTerminationsCfg):
    """Terminations for the lift cube task."""

    success = DoneTerm(
        func=mdp.cube_height_above_base,
        params={
            "cube_cfg": SceneEntityCfg("cube"),
            "robot_cfg": SceneEntityCfg("robot"),
            "robot_base_name": "base_link",
            "height_threshold": 0.20,
        },
    )


@configclass
class XLeRobotLiftCubeEnvCfg(XLeRobotEnvCfg):
    """Configuration for the XLeRobot lift cube environment."""

    scene: XLeRobotLiftCubeSceneCfg = XLeRobotLiftCubeSceneCfg(env_spacing=8.0)

    observations: XLeRobotLiftCubeObservationsCfg = XLeRobotLiftCubeObservationsCfg()
    actions: XLeRobotDefaultActionsCfg = XLeRobotDefaultActionsCfg()

    terminations: XLeRobotLiftCubeTerminationsCfg = XLeRobotLiftCubeTerminationsCfg()

    task_description: str = "Lift the red cube up using the right arm."

    def __post_init__(self) -> None:
        super().__post_init__()

        self.viewer.eye = (-0.4, -0.6, 0.5)
        self.viewer.lookat = (0.9, 0.0, -0.3)

        # Position robot so right arm is near the table
        self.scene.robot.init_state.pos = (0.35, -0.64, 0.01)

        parse_usd_and_create_subassets(TABLE_WITH_CUBE_USD_PATH, self)

        domain_randomization(
            self,
            random_options=[
                randomize_object_uniform(
                    "cube",
                    pose_range={
                        "x": (-0.075, 0.075),
                        "y": (-0.075, 0.075),
                        "z": (0.0, 0.0),
                        "yaw": (-30 * torch.pi / 180, 30 * torch.pi / 180),
                    },
                ),
            ],
        )
