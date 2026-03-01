"""Debug script to test XLeRobot environment with verbose error output."""

"""Launch Isaac Sim Simulator first."""

import argparse
import sys
import traceback

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Debug XLeRobot IsaacLab environment.")
parser.add_argument("--num_envs", type=int, default=1, help="Number of environments to simulate.")
parser.add_argument("--task", type=str, default="XLeRobot-v0", help="Task name to test.")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

"""Rest everything follows."""

print("[DEBUG] IsaacSim started, beginning imports...", flush=True)

try:
    # Test if xlerobot_tasks is importable
    print("[DEBUG] Testing xlerobot_tasks import...", flush=True)
    try:
        import xlerobot_tasks
        print(f"[DEBUG] xlerobot_tasks imported OK: {xlerobot_tasks.__path__}", flush=True)
    except Exception as e:
        print(f"[DEBUG] xlerobot_tasks FAILED: {e}", flush=True)
        traceback.print_exc()

    import torch
    import gymnasium as gym
    from isaaclab.envs import ManagerBasedRLEnv
    from isaaclab_tasks.utils import parse_env_cfg

    # List registered envs
    matching = [spec.id for spec in gym.registry.values() if "XLeRobot" in spec.id]
    print(f"[DEBUG] Registered XLeRobot envs: {matching}", flush=True)

    if not matching:
        # Try manual import of xlerobot
        print("[DEBUG] No XLeRobot envs found, trying manual import...", flush=True)
        try:
            import xlerobot_tasks.tasks.xlerobot
            print("[DEBUG] Manual xlerobot import OK", flush=True)
            matching = [spec.id for spec in gym.registry.values() if "XLeRobot" in spec.id]
            print(f"[DEBUG] After manual import, XLeRobot envs: {matching}", flush=True)
        except Exception as e:
            print(f"[DEBUG] Manual xlerobot import FAILED: {e}", flush=True)
            traceback.print_exc()

    if not matching:
        print("[ERROR] No XLeRobot envs registered! Exiting.", flush=True)
        sys.exit(1)

    task_name = args_cli.task
    print(f"[INFO] Creating environment: {task_name} with {args_cli.num_envs} envs", flush=True)

    env_cfg = parse_env_cfg(task_name, device=args_cli.device, num_envs=args_cli.num_envs)
    print(f"[DEBUG] env_cfg parsed: {type(env_cfg).__name__}", flush=True)

    env: ManagerBasedRLEnv = gym.make(task_name, cfg=env_cfg).unwrapped
    print(f"[INFO] Environment created successfully!", flush=True)
    print(f"[INFO] Action space: {env.action_space}", flush=True)

    robot = env.scene["robot"]
    print(f"[INFO] Robot joint names: {robot.data.joint_names}", flush=True)
    print(f"[INFO] Number of joints: {robot.num_joints}", flush=True)

    print("[INFO] Resetting environment...", flush=True)
    obs, info = env.reset()
    print(f"[INFO] Observation keys: {list(obs['policy'].keys())}", flush=True)

    action_dim = env.action_space.shape[-1]
    print(f"[INFO] Running 10 steps with zero actions (action_dim={action_dim})...", flush=True)
    for step in range(10):
        action = torch.zeros(env.num_envs, action_dim, device=env.device)
        obs, reward, terminated, truncated, info = env.step(action)
        print(f"  Step {step}: reward={reward[0].item():.4f}", flush=True)

    print("[INFO] Test completed successfully!", flush=True)
    env.close()

except Exception as e:
    print(f"\n[ERROR] Exception occurred: {e}", flush=True)
    traceback.print_exc()
    sys.stdout.flush()
finally:
    simulation_app.close()
