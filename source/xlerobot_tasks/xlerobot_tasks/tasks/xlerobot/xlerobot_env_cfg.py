from dataclasses import MISSING
from typing import Any

import isaaclab.sim as sim_utils
import numpy as np
import torch
from isaaclab.assets import ArticulationCfg, AssetBaseCfg
from isaaclab.envs import ManagerBasedRLEnvCfg
from isaaclab.envs.mdp.recorders.recorders_cfg import (
    ActionStateRecorderManagerCfg as RecordTerm,
)
from isaaclab.managers import EventTermCfg as EventTerm
from isaaclab.managers import ObservationGroupCfg as ObsGroup
from isaaclab.managers import ObservationTermCfg as ObsTerm
from isaaclab.managers import SceneEntityCfg
from isaaclab.managers import TerminationTermCfg as DoneTerm
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.sensors import FrameTransformerCfg, OffsetCfg, TiledCameraCfg
from isaaclab.utils import configclass
from isaaclab.utils.datasets.episode_data import EpisodeData
from xlerobot_tasks.assets.xlerobot import XLEROBOT_CFG
from xlerobot_tasks.utils.constant import XLEROBOT_JOINT_NAMES

from . import mdp


@configclass
class XLeRobotSceneCfg(InteractiveSceneCfg):
    """Scene configuration for the XLeRobot dual-arm mobile manipulator."""

    scene: AssetBaseCfg = MISSING

    robot: ArticulationCfg = XLEROBOT_CFG.replace(prim_path="{ENV_REGEX_NS}/Robot")

    # End-effector frame for right arm
    right_ee_frame: FrameTransformerCfg = FrameTransformerCfg(
        prim_path="{ENV_REGEX_NS}/Robot/base_link",
        debug_vis=False,
        target_frames=[
            FrameTransformerCfg.FrameCfg(
                prim_path="{ENV_REGEX_NS}/Robot/Fixed_Jaw", name="right_gripper"
            ),
            FrameTransformerCfg.FrameCfg(
                prim_path="{ENV_REGEX_NS}/Robot/Fixed_Jaw",
                name="right_jaw_tip",
                offset=OffsetCfg(pos=(0.01, -0.097, 0.0)),
            ),
        ],
    )

    # End-effector frame for left arm
    left_ee_frame: FrameTransformerCfg = FrameTransformerCfg(
        prim_path="{ENV_REGEX_NS}/Robot/base_link",
        debug_vis=False,
        target_frames=[
            FrameTransformerCfg.FrameCfg(
                prim_path="{ENV_REGEX_NS}/Robot/Fixed_Jaw_2", name="left_gripper"
            ),
            FrameTransformerCfg.FrameCfg(
                prim_path="{ENV_REGEX_NS}/Robot/Fixed_Jaw_2",
                name="left_jaw_tip",
                offset=OffsetCfg(pos=(0.01, -0.097, 0.0)),
            ),
        ],
    )

    # Right arm camera (mounted on Fixed_Jaw)
    right_wrist: TiledCameraCfg = TiledCameraCfg(
        prim_path="{ENV_REGEX_NS}/Robot/Fixed_Jaw/Right_Arm_Camera/right_wrist_camera",
        offset=TiledCameraCfg.OffsetCfg(
            pos=(0.0, 0.0, 0.0), rot=(1.0, 0.0, 0.0, 0.0), convention="ros"
        ),
        data_types=["rgb"],
        spawn=sim_utils.PinholeCameraCfg(
            focal_length=36.5,
            focus_distance=400.0,
            horizontal_aperture=36.83,
            clipping_range=(0.01, 50.0),
            lock_camera=True,
        ),
        width=640,
        height=480,
        update_period=1 / 30.0,
    )

    # Left arm camera (mounted on Fixed_Jaw_2)
    left_wrist: TiledCameraCfg = TiledCameraCfg(
        prim_path="{ENV_REGEX_NS}/Robot/Fixed_Jaw_2/Left_Arm_Camera/left_wrist_camera",
        offset=TiledCameraCfg.OffsetCfg(
            pos=(0.0, 0.0, 0.0), rot=(1.0, 0.0, 0.0, 0.0), convention="ros"
        ),
        data_types=["rgb"],
        spawn=sim_utils.PinholeCameraCfg(
            focal_length=36.5,
            focus_distance=400.0,
            horizontal_aperture=36.83,
            clipping_range=(0.01, 50.0),
            lock_camera=True,
        ),
        width=640,
        height=480,
        update_period=1 / 30.0,
    )

    # Head camera (mounted on head_tilt_link/head_camera_link)
    head_camera: TiledCameraCfg = TiledCameraCfg(
        prim_path="{ENV_REGEX_NS}/Robot/head_tilt_link/head_camera_link/head_camera",
        offset=TiledCameraCfg.OffsetCfg(
            pos=(0.0, 0.0, 0.0), rot=(1.0, 0.0, 0.0, 0.0), convention="ros"
        ),
        data_types=["rgb"],
        spawn=sim_utils.PinholeCameraCfg(
            focal_length=28.7,
            focus_distance=400.0,
            horizontal_aperture=38.11,
            clipping_range=(0.01, 50.0),
            lock_camera=True,
        ),
        width=640,
        height=480,
        update_period=1 / 30.0,
    )

    light = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/Light",
        spawn=sim_utils.DomeLightCfg(color=(0.75, 0.75, 0.75), intensity=3000.0),
    )


@configclass
class XLeRobotActionsCfg:
    """Configuration for the actions."""

    right_arm_action: mdp.ActionTermCfg = MISSING
    right_gripper_action: mdp.ActionTermCfg = MISSING
    left_arm_action: mdp.ActionTermCfg = MISSING
    left_gripper_action: mdp.ActionTermCfg = MISSING
    base_action: mdp.ActionTermCfg = MISSING
    head_action: mdp.ActionTermCfg = MISSING


@configclass
class XLeRobotEventCfg:
    """Configuration for the events."""

    reset_all = EventTerm(func=mdp.reset_scene_to_default, mode="reset")


@configclass
class XLeRobotObservationsCfg:
    """Observation specifications for the MDP."""

    @configclass
    class PolicyCfg(ObsGroup):
        """Observations for policy group."""

        joint_pos = ObsTerm(func=mdp.joint_pos)
        joint_vel = ObsTerm(func=mdp.joint_vel)
        joint_pos_rel = ObsTerm(func=mdp.joint_pos_rel)
        joint_vel_rel = ObsTerm(func=mdp.joint_vel_rel)
        actions = ObsTerm(func=mdp.last_action)

        right_wrist = ObsTerm(
            func=mdp.image,
            params={"sensor_cfg": SceneEntityCfg("right_wrist"), "data_type": "rgb", "normalize": False},
        )
        left_wrist = ObsTerm(
            func=mdp.image,
            params={"sensor_cfg": SceneEntityCfg("left_wrist"), "data_type": "rgb", "normalize": False},
        )
        head_camera = ObsTerm(
            func=mdp.image,
            params={"sensor_cfg": SceneEntityCfg("head_camera"), "data_type": "rgb", "normalize": False},
        )

        right_ee_frame_state = ObsTerm(
            func=mdp.ee_frame_state,
            params={"ee_frame_cfg": SceneEntityCfg("right_ee_frame"), "robot_cfg": SceneEntityCfg("robot")},
        )
        left_ee_frame_state = ObsTerm(
            func=mdp.ee_frame_state,
            params={"ee_frame_cfg": SceneEntityCfg("left_ee_frame"), "robot_cfg": SceneEntityCfg("robot")},
        )
        joint_pos_target = ObsTerm(func=mdp.joint_pos_target, params={"asset_cfg": SceneEntityCfg("robot")})

        def __post_init__(self):
            self.enable_corruption = True
            self.concatenate_terms = False

    # observation groups
    policy: PolicyCfg = PolicyCfg()


@configclass
class XLeRobotRewardsCfg:
    """Configuration for the rewards."""


@configclass
class XLeRobotTerminationsCfg:
    """Configuration for the termination."""

    time_out = DoneTerm(func=mdp.time_out, time_out=True)


@configclass
class XLeRobotEnvCfg(ManagerBasedRLEnvCfg):
    """Configuration for the XLeRobot environment."""

    scene: XLeRobotSceneCfg = MISSING

    observations: XLeRobotObservationsCfg = MISSING
    actions: XLeRobotActionsCfg = XLeRobotActionsCfg()
    events: XLeRobotEventCfg = XLeRobotEventCfg()

    rewards: XLeRobotRewardsCfg = XLeRobotRewardsCfg()
    terminations: XLeRobotTerminationsCfg = MISSING

    recorders: RecordTerm = RecordTerm()

    robot_name: str = "xlerobot"
    """Robot name for dataset export."""
    default_feature_joint_names: list[str] = MISSING
    """Default feature joint names for dataset export."""
    task_description: str = MISSING
    """Task description for dataset export."""

    def __post_init__(self) -> None:
        super().__post_init__()

        self.decimation = 1
        self.episode_length_s = 30.0
        self.viewer.eye = (2.0, -2.0, 2.0)
        self.viewer.lookat = (0.0, 0.0, 0.8)

        self.sim.physx.bounce_threshold_velocity = 0.01
        self.sim.physx.friction_correlation_distance = 0.00625
        self.sim.render.enable_translucency = True

        self.scene.right_ee_frame.visualizer_cfg.markers["frame"].scale = (0.05, 0.05, 0.05)
        self.scene.left_ee_frame.visualizer_cfg.markers["frame"].scale = (0.05, 0.05, 0.05)

        # Arm joints get position features, base joints get velocity features
        arm_head_joint_names = XLEROBOT_JOINT_NAMES[:-3]
        base_joint_names = XLEROBOT_JOINT_NAMES[-3:]
        self.default_feature_joint_names = [f"{name}.pos" for name in arm_head_joint_names] + [
            f"{name}.vel" for name in base_joint_names
        ]

    def use_teleop_device(self, teleop_device) -> None:
        self.task_type = teleop_device
        self.actions = _init_xlerobot_action_cfg(self.actions, device=teleop_device)

    def preprocess_device_action(self, action: dict[str, Any], teleop_device) -> torch.Tensor:
        return _preprocess_xlerobot_action(action, teleop_device)

    def build_lerobot_frame(self, episode_data: EpisodeData, dataset_cfg=None) -> dict:
        obs_data = episode_data._data["obs"]
        action = obs_data["actions"][-1]
        processed_action = action.cpu().numpy()
        frame = {
            "action": processed_action,
            "observation.state": obs_data["joint_pos"][-1].cpu().numpy(),
            "task": self.task_description,
        }
        if dataset_cfg is not None:
            for frame_key in dataset_cfg.features.keys():
                if not frame_key.startswith("observation.images"):
                    continue
                camera_key = frame_key.split(".")[-1]
                frame[frame_key] = obs_data[camera_key][-1].cpu().numpy()
        return frame


def _init_xlerobot_action_cfg(action_cfg, device):
    """XLeRobot action configuration."""
    if device in ["xlerobot-leader", "joint_position"]:
        action_cfg.right_arm_action = mdp.JointPositionActionCfg(
            asset_name="robot",
            joint_names=["Rotation", "Pitch", "Elbow", "Wrist_Pitch", "Wrist_Roll"],
            scale=1.0,
        )
        action_cfg.right_gripper_action = mdp.JointPositionActionCfg(
            asset_name="robot",
            joint_names=["Jaw"],
            scale=1.0,
        )
        action_cfg.left_arm_action = mdp.JointPositionActionCfg(
            asset_name="robot",
            joint_names=["Rotation_2", "Pitch_2", "Elbow_2", "Wrist_Pitch_2", "Wrist_Roll_2"],
            scale=1.0,
        )
        action_cfg.left_gripper_action = mdp.JointPositionActionCfg(
            asset_name="robot",
            joint_names=["Jaw_2"],
            scale=1.0,
        )
        action_cfg.base_action = mdp.JointVelocityActionCfg(
            asset_name="robot",
            joint_names=["root_x_axis_joint", "root_y_axis_joint", "root_z_rotation_joint"],
            scale=1.0,
        )
        action_cfg.head_action = mdp.JointPositionActionCfg(
            asset_name="robot",
            joint_names=["head_pan_joint", "head_tilt_joint"],
            scale=1.0,
        )
    elif device in ["keyboard", "gamepad", "xlerobot-keyboard", "xlerobot-gamepad"]:
        action_cfg.right_arm_action = mdp.DifferentialInverseKinematicsActionCfg(
            asset_name="robot",
            joint_names=["Rotation", "Pitch", "Elbow", "Wrist_Pitch", "Wrist_Roll"],
            body_name="Fixed_Jaw",
            controller=mdp.DifferentialIKControllerCfg(
                command_type="pose", ik_method="dls", use_relative_mode=True
            ),
        )
        action_cfg.right_gripper_action = mdp.RelativeJointPositionActionCfg(
            asset_name="robot",
            joint_names=["Jaw"],
            scale=1.0,
        )
        action_cfg.left_arm_action = mdp.DifferentialInverseKinematicsActionCfg(
            asset_name="robot",
            joint_names=["Rotation_2", "Pitch_2", "Elbow_2", "Wrist_Pitch_2", "Wrist_Roll_2"],
            body_name="Fixed_Jaw_2",
            controller=mdp.DifferentialIKControllerCfg(
                command_type="pose", ik_method="dls", use_relative_mode=True
            ),
        )
        action_cfg.left_gripper_action = mdp.RelativeJointPositionActionCfg(
            asset_name="robot",
            joint_names=["Jaw_2"],
            scale=1.0,
        )
        action_cfg.base_action = mdp.JointVelocityActionCfg(
            asset_name="robot",
            joint_names=["root_x_axis_joint", "root_y_axis_joint", "root_z_rotation_joint"],
            scale=1.0,
        )
        action_cfg.head_action = mdp.JointPositionActionCfg(
            asset_name="robot",
            joint_names=["head_pan_joint", "head_tilt_joint"],
            scale=1.0,
        )
    return action_cfg


def _preprocess_xlerobot_action(action: dict[str, Any], teleop_device) -> torch.Tensor:
    """Preprocess device action for XLeRobot.

    For joint-position devices (xlerobot-leader), the device outputs 17 values that map
    directly to the action manager order.

    For IK devices (xlerobot-keyboard, xlerobot-gamepad), the device outputs a 21-vector:
        right_arm(8) + left_arm(8) + head(2) + base(3)
    where each arm 8-vector is: (dx, dy, dz, droll, dpitch, dyaw, d_rotation, d_gripper)

    The IK action manager expects 19 values:
        [0:6]   = right arm IK delta   (device[0:6])
        [6]     = right gripper         (device[7], skip device[6]=d_rotation)
        [7:13]  = left arm IK delta     (device[8:14])
        [13]    = left gripper           (device[15], skip device[14]=d_rotation)
        [14:17] = base velocity          (device[18:21])
        [17:19] = head position          (device[16:18])
    """
    joint_state = action["joint_state"]
    if teleop_device.device_type in ("xlerobot-keyboard", "xlerobot-gamepad"):
        # IK mode: 21-vector device output -> 19-vector action
        processed_action = torch.zeros(teleop_device.env.num_envs, 19, device=teleop_device.env.device)
        processed_action[:, 0:6] = joint_state[0:6]      # right arm IK delta
        processed_action[:, 6] = joint_state[7]           # right gripper (skip d_rotation at [6])
        processed_action[:, 7:13] = joint_state[8:14]     # left arm IK delta
        processed_action[:, 13] = joint_state[15]         # left gripper (skip d_rotation at [14])
        processed_action[:, 14:17] = joint_state[18:21]   # base velocity
        processed_action[:, 17:19] = joint_state[16:18]   # head position
    else:
        # Joint-position mode: 17-vector direct mapping
        processed_action = torch.zeros(teleop_device.env.num_envs, 17, device=teleop_device.env.device)
        processed_action[:, :] = joint_state
    return processed_action


##
# Concrete default environment configuration
##


@configclass
class XLeRobotDefaultSceneCfg(XLeRobotSceneCfg):
    """Default scene configuration with a ground plane."""

    scene: AssetBaseCfg = AssetBaseCfg(
        prim_path="/World/GroundPlane",
        spawn=sim_utils.GroundPlaneCfg(),
    )


@configclass
class XLeRobotDefaultActionsCfg:
    """Default actions with joint position control for all actuators."""

    right_arm_action: mdp.JointPositionActionCfg = mdp.JointPositionActionCfg(
        asset_name="robot",
        joint_names=["Rotation", "Pitch", "Elbow", "Wrist_Pitch", "Wrist_Roll"],
        scale=1.0,
    )
    right_gripper_action: mdp.JointPositionActionCfg = mdp.JointPositionActionCfg(
        asset_name="robot",
        joint_names=["Jaw"],
        scale=1.0,
    )
    left_arm_action: mdp.JointPositionActionCfg = mdp.JointPositionActionCfg(
        asset_name="robot",
        joint_names=["Rotation_2", "Pitch_2", "Elbow_2", "Wrist_Pitch_2", "Wrist_Roll_2"],
        scale=1.0,
    )
    left_gripper_action: mdp.JointPositionActionCfg = mdp.JointPositionActionCfg(
        asset_name="robot",
        joint_names=["Jaw_2"],
        scale=1.0,
    )
    base_action: mdp.JointVelocityActionCfg = mdp.JointVelocityActionCfg(
        asset_name="robot",
        joint_names=["root_x_axis_joint", "root_y_axis_joint", "root_z_rotation_joint"],
        scale=1.0,
    )
    head_action: mdp.JointPositionActionCfg = mdp.JointPositionActionCfg(
        asset_name="robot",
        joint_names=["head_pan_joint", "head_tilt_joint"],
        scale=1.0,
    )


@configclass
class XLeRobotDefaultEnvCfg(XLeRobotEnvCfg):
    """Default XLeRobot environment with a ground plane."""

    scene: XLeRobotDefaultSceneCfg = XLeRobotDefaultSceneCfg(env_spacing=8.0)

    observations: XLeRobotObservationsCfg = XLeRobotObservationsCfg()
    actions: XLeRobotDefaultActionsCfg = XLeRobotDefaultActionsCfg()

    terminations: XLeRobotTerminationsCfg = XLeRobotTerminationsCfg()

    task_description: str = "XLeRobot dual-arm mobile manipulation."

    def __post_init__(self) -> None:
        super().__post_init__()

        self.viewer.eye = (3.0, -3.0, 2.5)
        self.viewer.lookat = (0.0, 0.0, 0.8)
