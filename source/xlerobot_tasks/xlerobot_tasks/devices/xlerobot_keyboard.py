import carb
import numpy as np
import torch

from .device_base import Device


class XLeRobotKeyboard(Device):
    """A keyboard controller for the XLeRobot dual-arm mobile manipulator.

    Controls the right arm via IK (WASDQE + JL/KI), left arm via IK (TFGH + YH/UJ),
    grippers, head pan/tilt, and mobile base.

    Key bindings:
        ============================== ================= =================
        Description                    Key (+)           Key (-)
        ============================== ================= =================
        -- Right Arm (IK) --
        Forward / Backward              W                 S
        Left / Right                     A                 D
        Up / Down                        Q                 E
        Rotate Yaw Left / Right          J                 L
        Rotate Pitch Up / Down           K                 I
        Right Gripper Open / Close       U                 O
        -- Left Arm (IK) --
        (hold SHIFT + right arm keys)
        -- Head --
        Head Pan Left / Right            KEY_7             KEY_9
        Head Tilt Up / Down              KEY_8             KEY_0
        -- Mobile Base --
        Base Forward / Backward          UP                DOWN
        Base Left / Right                LEFT              RIGHT
        Base Rotate Left / Right         Z                 X
        Base Speed Level                 1 / 2 / 3
        ============================== ================= =================
    """

    def __init__(self, env, sensitivity: float = 1.0):
        super().__init__(env, "xlerobot-keyboard")

        self.pos_sensitivity = 0.01 * sensitivity
        self.joint_sensitivity = 0.15 * sensitivity
        self.rot_sensitivity = 0.15 * sensitivity

        self._create_key_bindings()

        # Right arm: (dx, dy, dz, droll, dpitch, dyaw, d_rotation, d_gripper) = 8
        self._right_arm_delta = np.zeros(8)
        # Left arm: same structure = 8
        self._left_arm_delta = np.zeros(8)
        # Head: (d_pan, d_tilt) = 2
        self._head_delta = np.zeros(2)
        # Base velocity: (vx, vy, vtheta) = 3
        self._base_vel = np.zeros(3)

        # Control mode: False=right arm, True=left arm
        self._left_arm_mode = False

        # Speed levels for base
        self._speed_levels = [
            {"xy_vel": 0.1, "theta_vel": 30 / 180.0 * np.pi},
            {"xy_vel": 0.2, "theta_vel": 60 / 180.0 * np.pi},
            {"xy_vel": 0.3, "theta_vel": 90 / 180.0 * np.pi},
        ]
        self._speed_index = 0

        # Robot asset
        self.asset_name = "robot"
        self.robot_asset = self.env.scene[self.asset_name]

        # Target frames for IK
        self.target_frame = "Fixed_Jaw"
        body_idxs, _ = self.robot_asset.find_bodies(self.target_frame)
        self.target_frame_idx = body_idxs[0]

        self._joint_names = self.robot_asset.data.joint_names

    def _add_device_control_description(self):
        self._display_controls_table.add_row(["--- Right Arm ---", ""])
        self._display_controls_table.add_row(["W/S", "forward/backward"])
        self._display_controls_table.add_row(["A/D", "left/right"])
        self._display_controls_table.add_row(["Q/E", "up/down"])
        self._display_controls_table.add_row(["J/L", "yaw left/right"])
        self._display_controls_table.add_row(["K/I", "pitch up/down"])
        self._display_controls_table.add_row(["U/O", "gripper open/close"])
        self._display_controls_table.add_row(["--- Left Arm ---", ""])
        self._display_controls_table.add_row(["SHIFT + above", "control left arm"])
        self._display_controls_table.add_row(["--- Head ---", ""])
        self._display_controls_table.add_row(["7/9", "head pan left/right"])
        self._display_controls_table.add_row(["8/0", "head tilt up/down"])
        self._display_controls_table.add_row(["--- Base ---", ""])
        self._display_controls_table.add_row(["UP/DOWN", "base forward/backward"])
        self._display_controls_table.add_row(["LEFT/RIGHT", "base left/right"])
        self._display_controls_table.add_row(["Z/X", "base rotate left/right"])
        self._display_controls_table.add_row(["1/2/3", "base speed level"])

    def get_device_state(self):
        # Concatenate: right_arm(8) + left_arm(8) + head(2) + base(3) = 21
        # The action processing will parse this into the proper format
        right_arm = self._convert_delta_from_frame(self._right_arm_delta)
        left_arm = self._left_arm_delta  # left arm uses similar delta
        head = self._head_delta
        base = self._base_vel
        return np.concatenate([right_arm, left_arm, head, base])

    def reset(self):
        self._right_arm_delta[:] = 0.0
        self._left_arm_delta[:] = 0.0
        self._head_delta[:] = 0.0
        self._base_vel[:] = 0.0
        self._speed_index = 0

    def _on_keyboard_event(self, event, *args, **kwargs):
        super()._on_keyboard_event(event, *args, **kwargs)

        # Check shift state for left arm mode
        if event.type == carb.input.KeyboardEventType.KEY_PRESS:
            if event.input.name == "LEFT_SHIFT" or event.input.name == "RIGHT_SHIFT":
                self._left_arm_mode = True
        if event.type == carb.input.KeyboardEventType.KEY_RELEASE:
            if event.input.name == "LEFT_SHIFT" or event.input.name == "RIGHT_SHIFT":
                self._left_arm_mode = False

        # Arm control keys
        if event.type == carb.input.KeyboardEventType.KEY_PRESS:
            if event.input.name in self._ARM_KEY_MAPPING:
                delta = self._ARM_DELTA_MAPPING[self._ARM_KEY_MAPPING[event.input.name]]
                if self._left_arm_mode:
                    self._left_arm_delta += delta
                else:
                    self._right_arm_delta += delta

            # Head control
            if event.input.name in self._HEAD_KEY_MAPPING:
                self._head_delta += self._HEAD_DELTA_MAPPING[self._HEAD_KEY_MAPPING[event.input.name]]

            # Base control
            if event.input.name in self._BASE_KEY_MAPPING:
                vel_key = self._BASE_KEY_MAPPING[event.input.name]
                scale_key = "theta_vel" if vel_key in ["rotate_left", "rotate_right"] else "xy_vel"
                self._base_vel += (
                    self._BASE_VEL_MAPPING[vel_key] * self._speed_levels[self._speed_index][scale_key]
                )

            # Speed level
            if event.input.name in ["KEY_1", "KEY_2", "KEY_3", "NUMPAD_1", "NUMPAD_2", "NUMPAD_3"]:
                self._speed_index = int(event.input.name.split("_")[-1]) - 1
                print(f"Base speed level: {self._speed_index + 1}")

        if event.type == carb.input.KeyboardEventType.KEY_RELEASE:
            if event.input.name in self._ARM_KEY_MAPPING:
                delta = self._ARM_DELTA_MAPPING[self._ARM_KEY_MAPPING[event.input.name]]
                if self._left_arm_mode:
                    self._left_arm_delta -= delta
                else:
                    self._right_arm_delta -= delta

            if event.input.name in self._HEAD_KEY_MAPPING:
                self._head_delta -= self._HEAD_DELTA_MAPPING[self._HEAD_KEY_MAPPING[event.input.name]]

            if event.input.name in self._BASE_KEY_MAPPING:
                self._base_vel[:] = 0.0

    def _create_key_bindings(self):
        # Arm delta mapping: (dx, dy, dz, droll, dpitch, dyaw, d_rotation, d_gripper)
        self._ARM_DELTA_MAPPING = {
            "forward": np.asarray([0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0]) * self.pos_sensitivity,
            "backward": np.asarray([0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0]) * self.pos_sensitivity,
            "left": np.asarray([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0]) * self.joint_sensitivity,
            "right": np.asarray([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0]) * self.joint_sensitivity,
            "up": np.asarray([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]) * self.pos_sensitivity,
            "down": np.asarray([-1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]) * self.pos_sensitivity,
            "rotate_up": np.asarray([0.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0]) * self.rot_sensitivity,
            "rotate_down": np.asarray([0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0]) * self.rot_sensitivity,
            "rotate_left": np.asarray([0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0]) * self.rot_sensitivity,
            "rotate_right": np.asarray([0.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0]) * self.rot_sensitivity,
            "gripper_open": np.asarray([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0]) * self.joint_sensitivity,
            "gripper_close": np.asarray([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -1.0]) * self.joint_sensitivity,
        }
        self._ARM_KEY_MAPPING = {
            "W": "forward",
            "S": "backward",
            "A": "left",
            "D": "right",
            "Q": "up",
            "E": "down",
            "K": "rotate_up",
            "I": "rotate_down",
            "J": "rotate_left",
            "L": "rotate_right",
            "U": "gripper_open",
            "O": "gripper_close",
        }

        # Head delta mapping: (d_pan, d_tilt)
        self._HEAD_DELTA_MAPPING = {
            "pan_left": np.asarray([1.0, 0.0]) * self.joint_sensitivity,
            "pan_right": np.asarray([-1.0, 0.0]) * self.joint_sensitivity,
            "tilt_up": np.asarray([0.0, -1.0]) * self.joint_sensitivity,
            "tilt_down": np.asarray([0.0, 1.0]) * self.joint_sensitivity,
        }
        self._HEAD_KEY_MAPPING = {
            "KEY_7": "pan_left",
            "NUMPAD_7": "pan_left",
            "KEY_9": "pan_right",
            "NUMPAD_9": "pan_right",
            "KEY_8": "tilt_up",
            "NUMPAD_8": "tilt_up",
            "KEY_0": "tilt_down",
            "NUMPAD_0": "tilt_down",
        }

        # Base velocity mapping: (vx, vy, vtheta)
        self._BASE_VEL_MAPPING = {
            "forward": np.asarray([1.0, 0.0, 0.0]),
            "backward": np.asarray([-1.0, 0.0, 0.0]),
            "left": np.asarray([0.0, 1.0, 0.0]),
            "right": np.asarray([0.0, -1.0, 0.0]),
            "rotate_left": np.asarray([0.0, 0.0, 1.0]),
            "rotate_right": np.asarray([0.0, 0.0, -1.0]),
        }
        self._BASE_KEY_MAPPING = {
            "UP": "forward",
            "DOWN": "backward",
            "LEFT": "left",
            "RIGHT": "right",
            "Z": "rotate_left",
            "X": "rotate_right",
        }
