# ═══════════════════════════════════════════════════════════════════
#  AETHER CONSOLE — LAUNCH ALL
#  Convenience script that starts the broker, Surgeon Console,
#  Robot Console, and Observer Screen as subprocesses.
#
#  Usage:  python launch_all.py
# ═══════════════════════════════════════════════════════════════════

import subprocess
import sys
import os
import time
import signal

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


def main():
    print("=" * 60)
    print("  AETHER CONSOLE — SYSTEM LAUNCHER")
    print("=" * 60)

    processes = []

    try:
        # 1. Start Broker
        print("\n  [1/4] Starting Pub-Sub Broker...")
        broker = subprocess.Popen(
            [sys.executable, os.path.join(PROJECT_ROOT, "broker.py")],
            cwd=PROJECT_ROOT,
        )
        processes.append(("Broker", broker))
        time.sleep(1)  # Wait for broker to start

        # 2. Start Surgeon Console
        print("  [2/4] Starting Surgeon Console...")
        surgeon = subprocess.Popen(
            [sys.executable, os.path.join(PROJECT_ROOT, "main.py")],
            cwd=PROJECT_ROOT,
        )
        processes.append(("Surgeon Console", surgeon))
        time.sleep(0.5)

        # 3. Start Robot Console
        print("  [3/4] Starting Robot Console...")
        robot = subprocess.Popen(
            [sys.executable, os.path.join(
                PROJECT_ROOT, "Robot-Console", "main.py")],
            cwd=os.path.join(PROJECT_ROOT, "Robot-Console"),
        )
        processes.append(("Robot Console", robot))
        time.sleep(0.5)

        # 4. Start Observer Screen
        print("  [4/4] Starting Observer Screen...")
        observer = subprocess.Popen(
            [sys.executable, os.path.join(
                PROJECT_ROOT, "Observer-Screen", "main.py")],
            cwd=os.path.join(PROJECT_ROOT, "Observer-Screen"),
        )
        processes.append(("Observer Screen", observer))

        print("\n  All systems launched. Press Ctrl+C to stop all.\n")

        # Wait for any process to exit
        while True:
            for name, proc in processes:
                ret = proc.poll()
                if ret is not None:
                    print(f"  [{name}] exited with code {ret}")
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n  Shutting down all processes...")
        for name, proc in reversed(processes):
            print(f"  Stopping {name}...")
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
        print("  All processes stopped.")


if __name__ == "__main__":
    main()
