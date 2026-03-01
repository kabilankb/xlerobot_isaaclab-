"""Script to test the XLeRobot IsaacLab environment.

Runs the simulation continuously until Ctrl+C is pressed.

Usage:
    # With GUI (continuous):
    python scripts/test_xlerobot_env.py --enable_cameras --num_envs 1

    # Headless:
    python scripts/test_xlerobot_env.py --headless --enable_cameras --num_envs 1

    # Specific task:
    python scripts/test_xlerobot_env.py --enable_cameras --task XLeRobot-LiftCube-v0
"""

"""Launch Isaac Sim Simulator first."""

import argparse

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Test XLeRobot IsaacLab environment.")
parser.add_argument("--num_envs", type=int, default=1, help="Number of environments to simulate.")
parser.add_argument("--task", type=str, default="XLeRobot-v0", help="Task name to test.")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

"""Rest everything follows."""

import torch

import gymnasium as gym
from isaaclab.envs import ManagerBasedRLEnv
from isaaclab_tasks.utils import parse_env_cfg

import xlerobot_tasks  # noqa: F401


def main():
    # List available XLeRobot environments
    available_envs = sorted([spec.id for spec in gym.registry.values() if "XLeRobot" in spec.id])
    print(f"\n[INFO] Available XLeRobot environments:", flush=True)
    for env_id in available_envs:
        print(f"  - {env_id}", flush=True)

    task_name = args_cli.task
    print(f"\n[INFO] Creating environment: {task_name} with {args_cli.num_envs} envs", flush=True)

    env_cfg = parse_env_cfg(task_name, device=args_cli.device, num_envs=args_cli.num_envs)
    env: ManagerBasedRLEnv = gym.make(task_name, cfg=env_cfg).unwrapped

    print(f"[INFO] Environment created successfully!", flush=True)
    print(f"[INFO] Observation space: {env.observation_space}", flush=True)
    print(f"[INFO] Action space: {env.action_space}", flush=True)
    print(f"[INFO] Number of environments: {env.num_envs}", flush=True)

    # Print robot joint info
    robot = env.scene["robot"]
    print(f"\n[INFO] Robot joint names: {robot.data.joint_names}", flush=True)
    print(f"[INFO] Number of joints: {robot.num_joints}", flush=True)
    print(f"[INFO] Robot body names: {robot.data.body_names}", flush=True)
    print(f"[INFO] Number of bodies: {robot.num_bodies}", flush=True)

    # Reset environment
    print("\n[INFO] Resetting environment...", flush=True)
    obs, info = env.reset()
    print(f"[INFO] Observation keys: {list(obs['policy'].keys())}", flush=True)
    for key, val in obs["policy"].items():
        if isinstance(val, torch.Tensor):
            print(f"  - {key}: shape={val.shape}, dtype={val.dtype}", flush=True)

    # Run continuously with random actions until Ctrl+C
    print(f"\n[INFO] Running simulation with random actions. Press Ctrl+C to stop.", flush=True)
    step = 0
    while simulation_app.is_running():
        action = torch.randn(env.num_envs, env.action_space.shape[-1], device=env.device) * 0.3
        obs, reward, terminated, truncated, info = env.step(action)
        step += 1

        if step % 500 == 0:
            joint_pos = robot.data.joint_pos[0]
            print(f"  Step {step}: joint_pos_mean={joint_pos.mean().item():.4f}, reward={reward[0].item():.4f}", flush=True)

    print(f"\n[INFO] Stopped after {step} steps.", flush=True)
    env.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[INFO] Ctrl+C received. Shutting down...", flush=True)
    except Exception as e:
        raise e
    finally:
        simulation_app.close()
