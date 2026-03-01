import isaaclab.envs.mdp as mdp
from isaaclab.managers import EventTermCfg as EventTerm
from isaaclab.managers import SceneEntityCfg


def randomize_object_uniform(
    name: str,
    pose_range: dict[str, tuple[float, float]],
    velocity_range: dict[str, tuple[float, float]] | None = None,
) -> EventTerm:
    if velocity_range is None:
        velocity_range = {}
    return EventTerm(
        func=mdp.reset_root_state_uniform,
        mode="reset",
        params={"pose_range": pose_range, "velocity_range": velocity_range, "asset_cfg": SceneEntityCfg(name)},
    )


def domain_randomization(env_cfg, random_options: list[EventTerm]):
    for idx, event_item in enumerate(random_options):
        setattr(env_cfg.events, f"domain_randomize_{idx}", event_item)
