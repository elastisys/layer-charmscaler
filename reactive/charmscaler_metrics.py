from charmhelpers.core.hookenv import config
from charms.reactive import set_state

set_state("charmscaler.metrics.available")


def get_metrics():
    cfg = config()

    return [{
        "name": "cpu",
        "database": "telegraf",
        "tag": "cpu",
        "field": "usage_idle",
        "aggregate_function": "MEAN",
        "downsample": 10,
        "data_settling": cfg.get("metric_data_settling_interval"),
        "cooldown": cfg.get("scaling_cooldown"),

        # Since we're currently looking at the idle CPU value, the
        # usage thresholds are in reverse.
        "rules": {
            "scale-up": {
                "condition": "BELOW",
                "threshold": (100 - cfg.get("scaling_cpu_max")),
                "period": cfg.get("scaling_period_upscale"),
                "resize": 1
            },
            "scale-in": {
                "condition": "ABOVE",
                "threshold": (100 - cfg.get("scaling_cpu_min")),
                "period": cfg.get("scaling_period_downscale"),
                "resize": -1
            },
        }
    }]
