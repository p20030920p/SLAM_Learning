"""Compatibility entry point for the former figure publisher."""

from publish_direction_analysis import DIRECTION_EN, DIRECTION_ZH, publish, refresh_direction

__all__ = ["DIRECTION_EN", "DIRECTION_ZH", "publish", "refresh_direction"]

if __name__ == "__main__":
    publish()
