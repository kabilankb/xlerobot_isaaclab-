import gymnasium as gym

gym.register(
    id="XLeRobot-v0",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.xlerobot_env_cfg:XLeRobotDefaultEnvCfg",
    },
)

gym.register(
    id="XLeRobot-LiftCube-v0",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.xlerobot_lift_cube_env_cfg:XLeRobotLiftCubeEnvCfg",
    },
)

gym.register(
    id="XLeRobot-Loft-v0",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.xlerobot_loft_env_cfg:XLeRobotLoftEnvCfg",
    },
)
