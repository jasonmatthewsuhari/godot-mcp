from __future__ import annotations

import logging

from .mcp_stdio_server import LeaderMCPServer


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    server = LeaderMCPServer()
    server.serve_stdio()


if __name__ == "__main__":
    main()

