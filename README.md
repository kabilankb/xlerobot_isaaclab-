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
│   └── test_xlerobot_env_debug.py
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

## Teleoperation

### Keyboard

```bash
python scripts/teleop_xlerobot.py --enable_cameras --num_envs 1 --task XLeRobot-v0
```

### Gamepad (Xbox)

```bash
python scripts/teleop_xlerobot.py --enable_cameras --num_envs 1 --task XLeRobot-v0 --teleop_device xlerobot-gamepad
```

### Controls

| Key | Action |
|---|---|
| **B** | Start control |
| **R** | Reset simulation |
| **N** | Mark success and reset |
| **Ctrl+C** | Quit |

#### Keyboard Controls

| Key | Action |
|---|---|
| W/S | Right arm forward/backward |
| A/D | Right arm left/right |
| Q/E | Right arm up/down |
| J/L | Right arm yaw |
| K/I | Right arm pitch |
| U/O | Right gripper open/close |
| SHIFT + above | Control left arm |
| 7/9 | Head pan |
| 8/0 | Head tilt |
| Arrow keys | Mobile base movement |
| Z/X | Base rotation |
| 1/2/3 | Base speed level |

### Arguments

| Argument | Default | Description |
|---|---|---|
| `--task` | `XLeRobot-v0` | Environment to load |
| `--teleop_device` | `xlerobot-keyboard` | `xlerobot-keyboard` or `xlerobot-gamepad` |
| `--sensitivity` | `1.0` | Control sensitivity |
| `--step_hz` | `60` | Simulation step rate |
| `--num_envs` | `1` | Number of parallel environments |

## License

Apache-2.0
