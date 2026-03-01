# XLeRobot IsaacLab

Standalone IsaacLab extension for the XLeRobot dual-arm mobile manipulator with keyboard and gamepad teleoperation.

## Environments

| Environment | Description |
|---|---|
| `XLeRobot-v0` | Default ground plane environment |
| `XLeRobot-LiftCube-v0` | Cube lifting task |
| `XLeRobot-Loft-v0` | Loft scene environment |

## Project Structure

```
xlerobot_ws/
├── assets/                     # Robot URDF/USD, scene assets (Git LFS)
├── scripts/
│   ├── teleop_xlerobot.py      # Keyboard/gamepad teleoperation
│   ├── test_xlerobot_env.py    # Environment test with random actions
│   └── test_xlerobot_env_debug.py  # Debug script with verbose output
└── source/xlerobot_tasks/
    └── xlerobot_tasks/
        ├── assets/             # Robot and scene configurations
        ├── devices/            # Teleoperation device drivers
        │   ├── device_base.py
        │   ├── xlerobot_keyboard.py
        │   ├── xlerobot_gamepad.py
        │   └── gamepad_utils.py
        ├── tasks/xlerobot/     # Environment configs and MDP
        │   ├── xlerobot_env_cfg.py
        │   ├── xlerobot_lift_cube_env_cfg.py
        │   ├── xlerobot_loft_env_cfg.py
        │   └── mdp/
        └── utils/
```

## Installation

### Prerequisites

- Isaac Sim 4.5+
- IsaacLab

### Setup

```bash
cd xlerobot_ws/source/xlerobot_tasks
pip install -e .
```

## Launch Commands

### Teleoperation (Keyboard)

```bash
# Default environment
python scripts/teleop_xlerobot.py --enable_cameras --num_envs 1 --task XLeRobot-v0

# Lift cube task
python scripts/teleop_xlerobot.py --enable_cameras --num_envs 1 --task XLeRobot-LiftCube-v0

# Loft scene
python scripts/teleop_xlerobot.py --enable_cameras --num_envs 1 --task XLeRobot-Loft-v0
```

### Teleoperation (Xbox Gamepad)

```bash
# Default environment
python scripts/teleop_xlerobot.py --enable_cameras --num_envs 1 --task XLeRobot-v0 --teleop_device xlerobot-gamepad

# Lift cube task
python scripts/teleop_xlerobot.py --enable_cameras --num_envs 1 --task XLeRobot-LiftCube-v0 --teleop_device xlerobot-gamepad

# Loft scene
python scripts/teleop_xlerobot.py --enable_cameras --num_envs 1 --task XLeRobot-Loft-v0 --teleop_device xlerobot-gamepad
```

### Teleoperation Options

```bash
# Custom sensitivity and step rate
python scripts/teleop_xlerobot.py --enable_cameras --num_envs 1 --task XLeRobot-v0 --sensitivity 1.5 --step_hz 30

# Headless mode (no GUI window)
python scripts/teleop_xlerobot.py --headless --enable_cameras --num_envs 1 --task XLeRobot-v0

# Multiple environments
python scripts/teleop_xlerobot.py --enable_cameras --num_envs 4 --task XLeRobot-v0
```

### Test Environment (Random Actions)

```bash
# Default environment
python scripts/test_xlerobot_env.py --enable_cameras --num_envs 1

# Lift cube task
python scripts/test_xlerobot_env.py --enable_cameras --num_envs 1 --task XLeRobot-LiftCube-v0

# Loft scene
python scripts/test_xlerobot_env.py --enable_cameras --num_envs 1 --task XLeRobot-Loft-v0

# Headless mode
python scripts/test_xlerobot_env.py --headless --enable_cameras --num_envs 1
```

### Debug Environment

```bash
# Verbose debug output for troubleshooting
python scripts/test_xlerobot_env_debug.py --enable_cameras --num_envs 1

# Debug specific task
python scripts/test_xlerobot_env_debug.py --enable_cameras --num_envs 1 --task XLeRobot-LiftCube-v0
```

## Teleoperation Arguments

| Argument | Default | Description |
|---|---|---|
| `--task` | `XLeRobot-v0` | Environment to load (`XLeRobot-v0`, `XLeRobot-LiftCube-v0`, `XLeRobot-Loft-v0`) |
| `--teleop_device` | `xlerobot-keyboard` | Input device (`xlerobot-keyboard` or `xlerobot-gamepad`) |
| `--sensitivity` | `1.0` | Control sensitivity multiplier |
| `--step_hz` | `60` | Simulation step rate in Hz |
| `--num_envs` | `1` | Number of parallel environments |
| `--seed` | `None` | Random seed |
| `--enable_cameras` | `False` | Enable camera rendering |
| `--headless` | `False` | Run without GUI |

## Keyboard Controls

| Key | Action |
|---|---|
| **B** | Start control |
| **R** | Reset simulation (task failure) |
| **N** | Mark task success and reset |
| **Ctrl+C** | Quit |

### Right Arm

| Key | Action |
|---|---|
| W / S | Forward / Backward |
| A / D | Left / Right |
| Q / E | Up / Down |
| J / L | Yaw left / right |
| K / I | Pitch up / down |
| U / O | Gripper open / close |

### Left Arm

Hold **SHIFT** + right arm keys to control the left arm.

### Head

| Key | Action |
|---|---|
| 7 / 9 | Head pan left / right |
| 8 / 0 | Head tilt up / down |

### Mobile Base

| Key | Action |
|---|---|
| Arrow Up / Down | Base forward / backward |
| Arrow Left / Right | Base strafe left / right |
| Z / X | Base rotate left / right |
| 1 / 2 / 3 | Base speed level (slow / medium / fast) |

## Gamepad Controls (Xbox)

| Input | Action |
|---|---|
| Left Stick | Arm forward / backward / left / right |
| Right Stick | Arm up / down + yaw |
| D-pad Up / Down | Arm pitch |
| RT / RB | Gripper open / close |
| LB (hold) | Switch to left arm |
| D-pad Left / Right | Head pan |
| LT (analog) | Head tilt |

## License

Apache-2.0
