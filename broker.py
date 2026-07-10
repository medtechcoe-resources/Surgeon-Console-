# ═══════════════════════════════════════════════════════════════════
#  AETHER CONSOLE — PUB-SUB BROKER LAUNCHER
#  Standalone script to run the central pub-sub broker.
#  Start this before launching any console applications.
#
#  Usage:  python broker.py
#          python broker.py --host 0.0.0.0 --port 5000
# ═══════════════════════════════════════════════════════════════════

import sys
import os
import argparse
import logging

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared_networking.broker import PubSubBroker
from shared_networking.config import BROKER_HOST, BROKER_PORT


def main():
    parser = argparse.ArgumentParser(
        description="Aether Pub-Sub Broker")
    parser.add_argument("--host", default=BROKER_HOST,
                        help=f"Bind address (default: {BROKER_HOST})")
    parser.add_argument("--port", type=int, default=BROKER_PORT,
                        help=f"Bind port (default: {BROKER_PORT})")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable verbose logging")
    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    broker = PubSubBroker(host=args.host, port=args.port)
    try:
        broker.start()
    except KeyboardInterrupt:
        print("\n  Broker shutting down...")
        broker.stop()


if __name__ == "__main__":
    main()
