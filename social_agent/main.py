from __future__ import annotations

import argparse
import logging
import sys
from typing import Dict

from .config_loader import AgentConfig, load_config
from .platform_clients import PlatformClient, create_client
from .preview import render_preview
from .scheduler import Scheduler

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def build_clients(config: AgentConfig) -> Dict[str, PlatformClient]:
    clients: Dict[str, PlatformClient] = {}
    for name, settings in config.platform_settings.items():
        clients[name] = create_client(name, settings)
    return clients


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Schedule social posts from a JSON config file")
    parser.add_argument("--config", required=True, help="Path to JSON configuration file")
    parser.add_argument("--preview", action="store_true", help="Hiển thị cấu hình và bài đăng mà không gửi đi")
    parser.add_argument("--simulate", action="store_true", help="Log actions instead of dispatching to platforms")
    parser.add_argument("--log-level", default="INFO", help="Python logging level (default: INFO)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(level=args.log_level.upper(), format=LOG_FORMAT)

    config = load_config(args.config)
    clients = build_clients(config)

    if args.preview:
        print(render_preview(config))
        return 0

    scheduler = Scheduler(clients, simulate=args.simulate)
    scheduler.schedule_posts(config.posts)
    scheduler.wait()
    return 0


if __name__ == "__main__":
    sys.exit(main())
