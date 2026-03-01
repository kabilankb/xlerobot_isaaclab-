import numpy as np

from .device_base import Device
from .gamepad_utils import GamepadController


class XLeRobotGamepad(Device):
    """Gamepad controller for the XLeRobot dual-arm mobile manipulator.

    Uses an Xbox gamepad. By default controls the right arm; hold LB to switch to left arm.

    Key bindings:
        ====================== ==========================================
        Description              Key
        ====================== ==========================================
        -- Active Arm (IK) --
        Forward / Backward       Left stick Y
        Left / Right             Left stick X
        Up / Down                Right stick Y
        Rotate Yaw               Right stick X
        Rotate Pitch             D-pad Up / D-pad Down
        Gripper Open / Close     RT / RB
        -- Arm Switch --
        Hold for Left Arm        LB
        -- Head --
        Head Pan                 D-pad Left / D-pad Right
        Head Tilt                LT (analog)
        -- Base --
        (activate with Back)     Left/Right sticks control base
        ====================== ==========================================
    """

    def __init__(self, env, sensitivity: float = 1.0):
        super().__init__(env, "xlerobot-gamepad")

        self.pos_sensitivity = 0.01 * sensitivity
        self.joint_sensitivity = 0.15 * sensitivity
        self.rot_sensitivity = 0.15 * sensitivity

        # Initialize gamepad
        self._gamepad = GamepadController()
        self._gamepad.start()
        if "xbox" not in self._gamepad.name:
            raise ValueError("Only Xbox gamepads are supported.")
        self._create_key_mapping()

        # Right arm: (dx, dy, dz, droll, dpitch, dyaw, d_rotation, d_gripper) = 8
        self._right_arm_delta = np.zeros(8)
        # Left arm: same = 8
        self._left_arm_delta = np.zeros(8)
        # Head: (d_pan, d_tilt) = 2
        self._head_delta = np.zeros(2)
        # Base: (vx, vy, vtheta) = 3
        self._base_vel = np.zeros(3)

        # Robot asset
        self.asset_name = "robot"
        self.robot_asset = self.env.scene[self.asset_name]
        self.target_frame = "Fixed_Jaw"
        body_idxs, _ = self.robot_asset.find_bodies(self.target_frame)
        self.target_frame_idx = body_idxs[0]

    def __del__(self):
        super().__del__()
        self._gamepad.stop()

    def _add_device_control_description(self):
        self._display_controls_table.add_row(["Left Stick", "arm forward/backward/left/right"])
        self._display_controls_table.add_row(["Right Stick", "arm up/down + yaw"])
        self._display_controls_table.add_row(["D-pad Up/Down", "arm pitch"])
        self._display_controls_table.add_row(["RT/RB", "gripper open/close"])
        self._display_controls_table.add_row(["LB (hold)", "switch to left arm"])
        self._display_controls_table.add_row(["D-pad L/R", "head pan"])
        self._display_controls_table.add_row(["LT", "head tilt"])

    def get_device_state(self):
        right_arm = self._convert_delta_from_frame(self._right_arm_delta)
        left_arm = self._left_arm_delta
        head = self._head_delta
        base = self._base_vel
        return np.concatenate([right_arm, left_arm, head, base])

    def reset(self):
        self._right_arm_delta[:] = 0.0
        self._left_arm_delta[:] = 0.0
        self._head_delta[:] = 0.0
        self._base_vel[:] = 0.0

    def advance(self):
        self._right_arm_delta[:] = 0.0
        self._left_arm_delta[:] = 0.0
        self._head_delta[:] = 0.0
        self._base_vel[:] = 0.0
        self._update_action()
        return super().advance()

    def _create_key_mapping(self):
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

        self._ARM_INPUT_LIST = [
            ("forward", "L_Y", True),
            ("backward", "L_Y"),
            ("left", "L_X", True),
            ("right", "L_X"),
            ("up", "R_Y", True),
            ("down", "R_Y"),
            ("rotate_up", "DPAD_UP"),
            ("rotate_down", "DPAD_DOWN"),
            ("rotate_left", "R_X", True),
            ("rotate_right", "R_X"),
            ("gripper_open", "RT"),
            ("gripper_close", "RB"),
        ]

    def _update_action(self):
        self._gamepad.update()
        state = self._gamepad.get_state()

        # Check if LB held -> left arm mode
        is_lb, _ = self._gamepad.lookup_controller_state(state, "LB")
        target = self._left_arm_delta if is_lb else self._right_arm_delta

        # Arm control
        for mapping in self._ARM_INPUT_LIST:
            action_name, controller_name = mapping[0], mapping[1]
            reverse = mapping[2] if len(mapping) > 2 else False
            is_active, is_positive = self._gamepad.lookup_controller_state(state, controller_name, reverse)
            if is_active and is_positive:
                target += self._ARM_DELTA_MAPPING[action_name]

        # Head pan from D-pad left/right
        dpad_left, _ = self._gamepad.lookup_controller_state(state, "DPAD_LEFT")
        dpad_right, _ = self._gamepad.lookup_controller_state(state, "DPAD_RIGHT")
        if dpad_left:
            self._head_delta[0] += self.joint_sensitivity
        if dpad_right:
            self._head_delta[0] -= self.joint_sensitivity

        # Head tilt from LT analog
        lt_active, lt_positive = self._gamepad.lookup_controller_state(state, "LT")
        if lt_active:
            self._head_delta[1] += self.joint_sensitivity if lt_positive else -self.joint_sensitivity
