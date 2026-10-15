"""Compatibility entry point for the former figure publisher."""

from publish_direction_analysis import publish, refresh_direction

__all__ = ["publish", "refresh_direction"]

if __name__ == "__main__":
    publish()
