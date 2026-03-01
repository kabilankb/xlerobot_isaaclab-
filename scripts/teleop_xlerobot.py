# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Standalone teleoperation script for XLeRobot environments."""

"""Launch Isaac Sim Simulator first."""
import multiprocessing

if multiprocessing.get_start_method() != "spawn":
    multiprocessing.set_start_method("spawn", force=True)
import argparse
import signal

from isaaclab.app import AppLauncher

# add argparse arguments
parser = argparse.ArgumentParser(description="XLeRobot teleoperation for XLeRobot environments.")
parser.add_argument("--num_envs", type=int, default=1, help="Number of environments to simulate.")
parser.add_argument(
    "--teleop_device",
    type=str,
    default="xlerobot-keyboard",
    choices=["xlerobot-keyboard", "xlerobot-gamepad"],
    help="Device for interacting with environment",
)
parser.add_argument("--task", type=str, default="XLeRobot-v0", help="Name of the task.")
parser.add_argument("--seed", type=int, default=None, help="Seed for the environment.")
parser.add_argument("--sensitivity", type=float, default=1.0, help="Sensitivity factor.")
parser.add_argument("--step_hz", type=int, default=60, help="Environment stepping rate in Hz.")

# append AppLauncher cli args
AppLauncher.add_app_launcher_args(parser)
# parse the arguments
args_cli = parser.parse_args()

app_launcher_args = vars(args_cli)

# launch omniverse app
app_launcher = AppLauncher(app_launcher_args)
simulation_app = app_launcher.app

import time

import gymnasium as gym
import torch
from isaaclab.envs import ManagerBasedRLEnv
from isaaclab.managers import TerminationTermCfg
from isaaclab_tasks.utils import parse_env_cfg

import xlerobot_tasks  # noqa: F401 -- triggers gym.register() for XLeRobot envs


class RateLimiter:
    """Convenience class for enforcing rates in loops."""

    def __init__(self, hz):
        self.hz = hz
        self.last_time = time.time()
        self.sleep_duration = 1.0 / hz
        self.render_period = min(0.0166, self.sleep_duration)

    def sleep(self, env):
        """Attempt to sleep at the specified rate in hz."""
        next_wakeup_time = self.last_time + self.sleep_duration
        while time.time() < next_wakeup_time:
            time.sleep(self.render_period)
            env.sim.render()

        self.last_time = self.last_time + self.sleep_duration

        # detect time jumping forwards (e.g. loop is too slow)
        if self.last_time < time.time():
            while self.last_time < time.time():
                self.last_time += self.sleep_duration


def manual_terminate(env: ManagerBasedRLEnv, success: bool):
    if hasattr(env, "termination_manager"):
        if success:
            env.termination_manager.set_term_cfg(
                "success",
                TerminationTermCfg(func=lambda env: torch.ones(env.num_envs, dtype=torch.bool, device=env.device)),
            )
        else:
            env.termination_manager.set_term_cfg(
                "success",
                TerminationTermCfg(func=lambda env: torch.zeros(env.num_envs, dtype=torch.bool, device=env.device)),
            )
        env.termination_manager.compute()


def main():
    """Running XLeRobot teleoperation."""

    # Show available GPUs
    if torch.cuda.is_available():
        print(f"\n[INFO] Available GPUs: {torch.cuda.device_count()}", flush=True)
        for i in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(i)
            print(f"  GPU {i}: {props.name} ({props.total_memory / 1024**3:.1f} GB)", flush=True)
        print(f"  Using device: {args_cli.device}", flush=True)
    else:
        print("\n[WARN] No CUDA GPUs available. Running on CPU.", flush=True)

    # Show available XLeRobot environments
    available_envs = sorted([spec.id for spec in gym.registry.values() if "XLeRobot" in spec.id])
    print(f"\n[INFO] Available XLeRobot environments:", flush=True)
    for env_id in available_envs:
        print(f"  - {env_id}", flush=True)
    print(f"\n[INFO] Task: {args_cli.task} | Device: {args_cli.teleop_device} | Envs: {args_cli.num_envs}", flush=True)

    env_cfg = parse_env_cfg(args_cli.task, device=args_cli.device, num_envs=args_cli.num_envs)
    env_cfg.use_teleop_device(args_cli.teleop_device)
    env_cfg.seed = args_cli.seed if args_cli.seed is not None else int(time.time())

    # disable timeout for teleoperation
    if hasattr(env_cfg.terminations, "time_out"):
        env_cfg.terminations.time_out = None
    if hasattr(env_cfg.terminations, "success"):
        env_cfg.terminations.success = None

    # no recording
    env_cfg.recorders = None

    # create environment
    env: ManagerBasedRLEnv = gym.make(args_cli.task, cfg=env_cfg).unwrapped

    # create controller
    if args_cli.teleop_device == "xlerobot-keyboard":
        from xlerobot_tasks.devices import XLeRobotKeyboard

        teleop_interface = XLeRobotKeyboard(env, sensitivity=args_cli.sensitivity)
    elif args_cli.teleop_device == "xlerobot-gamepad":
        from xlerobot_tasks.devices import XLeRobotGamepad

        teleop_interface = XLeRobotGamepad(env, sensitivity=args_cli.sensitivity)
    else:
        raise ValueError(f"Invalid device interface '{args_cli.teleop_device}'.")

    # add teleoperation key for env reset
    should_reset_recording_instance = False

    def reset_recording_instance():
        nonlocal should_reset_recording_instance
        should_reset_recording_instance = True

    # add teleoperation key for task success
    should_reset_task_success = False

    def reset_task_success():
        nonlocal should_reset_task_success
        should_reset_task_success = True
        reset_recording_instance()

    teleop_interface.add_callback("R", reset_recording_instance)
    teleop_interface.add_callback("N", reset_task_success)
    teleop_interface.display_controls()
    rate_limiter = RateLimiter(args_cli.step_hz)

    # reset environment
    env.reset()
    teleop_interface.reset()

    interrupted = False

    def signal_handler(signum, frame):
        """Handle SIGINT (Ctrl+C) signal."""
        nonlocal interrupted
        interrupted = True
        print("\n[INFO] KeyboardInterrupt (Ctrl+C) detected. Cleaning up resources...")

    original_sigint_handler = signal.signal(signal.SIGINT, signal_handler)

    try:
        while simulation_app.is_running() and not interrupted:
            # run everything in inference mode
            with torch.inference_mode():
                actions = teleop_interface.advance()
                if should_reset_task_success:
                    print("Task Success!!!")
                    should_reset_task_success = False
                if should_reset_recording_instance:
                    env.reset()
                    should_reset_recording_instance = False

                elif actions is None:
                    env.render()
                # apply actions
                else:
                    env.step(actions)
                if rate_limiter:
                    rate_limiter.sleep(env)
            if interrupted:
                break
    except Exception as e:
        import traceback

        print(f"\n[ERROR] An error occurred: {e}\n")
        traceback.print_exc()
        print("[INFO] Cleaning up resources...")
    finally:
        # Restore original signal handler
        signal.signal(signal.SIGINT, original_sigint_handler)
        # close the simulator
        env.close()
        simulation_app.close()


if __name__ == "__main__":
    # run the main function
    main()
