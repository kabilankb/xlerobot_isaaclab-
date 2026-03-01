# XLeRobot IsaacLab — Development Documentation

## Project Overview

**Project:** XLeRobot IsaacLab — standalone IsaacLab extension for dual-arm mobile manipulator teleoperation and training.

**Hardware:** Dell Pro Max T2 Tower, NVIDIA RTX PRO 6000 Blackwell (98 GB VRAM), Intel Core Ultra 9 285K (24 cores), 128 GB RAM.

**Software:** NVIDIA Isaac Sim 4.5+, IsaacLab, Python 3.11, PyTorch (CUDA), Ubuntu 22.04.

**Repository:** https://github.com/kabilankb/xlerobot_isaaclab-

---

## Development Timeline

### Phase 1 — Environment Setup and Extension (Completed)

- Created standalone `xlerobot_ws` extension outside the main `leisaac` monorepo
- Registered 3 gym environments: `XLeRobot-v0`, `XLeRobot-LiftCube-v0`, `XLeRobot-Loft-v0`
- Set up robot USD assets, scene assets, and action/observation configurations
- Test scripts with random actions to validate environment creation

### Phase 2 — Keyboard and Gamepad Teleoperation (Completed)

**Files created:**
| File | Description |
|---|---|
| `xlerobot_tasks/utils/math_utils.py` | `rotvec_to_euler()` rotation utility |
| `xlerobot_tasks/devices/__init__.py` | Exports `XLeRobotKeyboard`, `XLeRobotGamepad` |
| `xlerobot_tasks/devices/device_base.py` | Base device class with keyboard listener, frame conversion |
| `xlerobot_tasks/devices/xlerobot_keyboard.py` | Keyboard controller (WASD + IK for dual arms, head, base) |
| `xlerobot_tasks/devices/xlerobot_gamepad.py` | Xbox gamepad controller |
| `xlerobot_tasks/devices/gamepad_utils.py` | Pygame-based gamepad input handler |
| `scripts/teleop_xlerobot.py` | Standalone teleoperation script |

**Bugs fixed in `xlerobot_env_cfg.py`:**

1. `_init_xlerobot_action_cfg` — device check only matched `"keyboard"` / `"gamepad"` but device types are `"xlerobot-keyboard"` / `"xlerobot-gamepad"`. Added both to the IK branch.

2. `_preprocess_xlerobot_action` — created a 17-wide tensor but device outputs 21 values. Fixed to properly slice the 21-value device output into a 19-value IK action tensor:
   ```
   Device 21-vector: right_arm(8) + left_arm(8) + head(2) + base(3)
     arm 8-vector: (dx, dy, dz, droll, dpitch, dyaw, d_rotation, d_gripper)

   IK action 19-vector (action manager order):
     [0:6]   = right arm IK delta   (device[0:6])
     [6]     = right gripper         (device[7], skip device[6]=d_rotation)
     [7:13]  = left arm IK delta     (device[8:14])
     [13]    = left gripper           (device[15], skip device[14]=d_rotation)
     [14:17] = base velocity          (device[18:21])
     [17:19] = head position          (device[16:18])
   ```

**Design decisions:**
- Copied device classes from `leisaac.devices` into the extension to avoid dependency on the monorepo
- Only import path changes were needed (`leisaac.utils` → `xlerobot_tasks.utils`, `..device_base` → `.device_base`)
- No recording support in the teleop script to avoid `leisaac.enhance` dependency
- Rate-limited loop with `RateLimiter` class for consistent step timing

---

## Architecture

### Robot: XLeRobot

- **Dual arms** — 5 DOF each (Rotation, Pitch, Elbow, Wrist_Pitch, Wrist_Roll) + 1 DOF gripper (Jaw)
- **Head** — 2 DOF (pan, tilt)
- **Mobile base** — 3 DOF velocity (x, y, theta)
- **Cameras** — right wrist, left wrist, head (640x480 RGB each)
- **Total joints** — 17 (5+1+5+1+2+3)

### Action Modes

| Mode | Device | Action Dimensions | Description |
|---|---|---|---|
| Joint Position | xlerobot-leader | 17 | Direct joint position targets |
| Differential IK | xlerobot-keyboard, xlerobot-gamepad | 19 | IK delta for arms (6 each) + gripper (1 each) + base vel (3) + head pos (2) |

### Control Flow

```
User Input → Device Class → get_device_state() → 21-vector
  → env.cfg.preprocess_device_action() → slice to 19-vector
  → env.step(action) → Action Manager → IK solver → Joint commands
```

### Environment Registration

```
xlerobot_tasks/__init__.py
  → from .tasks import *
    → tasks/__init__.py uses import_packages() to auto-discover
      → tasks/xlerobot/__init__.py calls gym.register() for all 3 envs
```

Scripts must `import xlerobot_tasks` before calling `parse_env_cfg()` to trigger registration.

---

## Known Issues and Notes

- `torch.cuda.get_device_properties().total_memory` (not `total_mem`) — fixed in commit `dd01621`
- `assets/scenes/lightwheel_loft/Loft/` directory is 4.3 GB — excluded from git, must be obtained separately
- Git LFS is used for binary assets (`.usd`, `.png`, `.jpg`, `.hdr`, `.obj`, `.mdl`, `.max`)
- GitHub free LFS quota is 1 GB storage / 1 GB bandwidth per month

---

## Roadmap

### Phase 3 — Data Recording
- [ ] Add HDF5 recording support to `teleop_xlerobot.py`
- [ ] LeRobot dataset format export
- [ ] Implement without `leisaac.enhance` dependency (standalone recorder)

### Phase 4 — Imitation Learning
- [ ] Collect demonstration datasets via teleoperation
- [ ] Train policies (ACT, Diffusion Policy)
- [ ] Evaluate in simulation

### Phase 5 — Reinforcement Learning
- [ ] Define reward functions for lift cube task
- [ ] Train with PPO/SAC using IsaacLab RL workflow
- [ ] Benchmark training performance on RTX PRO 6000

### Phase 6 — Additional Devices
- [ ] Port XLeRobot leader arm device for hardware-in-the-loop teleoperation
- [ ] Physical leader arms for higher quality demonstrations

### Phase 7 — Sim-to-Real Transfer
- [ ] Deploy trained policies to real XLeRobot hardware
- [ ] Domain randomization (lighting, textures, object poses)
- [ ] Real-world evaluation and fine-tuning

### Phase 8 — Additional Tasks
- [ ] Pick-and-place task
- [ ] Stacking task
- [ ] Drawer/cabinet opening task
- [ ] Success detection and auto-reset for autonomous training

---

## Commit History

| Commit | Description |
|---|---|
| `b540450` | Initial commit — source code, scripts, extension config |
| `d71662e` | Add robot and small scene assets via Git LFS |
| `0d131f7` | Exclude large loft scene assets from repo |
| `dd01621` | Fix GPU property name: `total_mem` → `total_memory` |
| `ab9f276` | Update README with all launch commands and controls |
