# ═══════════════════════════════════════════════════════════════════
#  DATA GENERATOR — ROBOT TELEMETRY GENERATOR
#  Produces realistic 6-DOF robotic arm telemetry using sinusoidal
#  joint motion + simplified forward kinematics.
#  Interval: every 600 ms (~100 updates/min).
# ═══════════════════════════════════════════════════════════════════

import math
import random
from datetime import datetime

import psutil
from PyQt6.QtCore import QObject, QTimer, pyqtSignal

# ── Joint Limits (degrees) ────────────────────────────────────────
JOINT_LIMITS = [
    (-170, 170),   # J1
    (-120, 120),   # J2
    (-170, 170),   # J3
    (-120, 120),   # J4
    (-170, 170),   # J5
    (-120, 120),   # J6
]

NUM_JOINTS = 6
INTERVAL_MS = 600   # 100 updates/min ≈ 600 ms


class RobotTelemetryGenerator(QObject):
    """Generates continuous, realistic robotic arm telemetry.

    Uses smooth sinusoidal motion with Gaussian noise to simulate
    realistic joint movements.  Tool position is derived from a
    simplified forward kinematics model.  Emits ``telemetry_ready``
    each tick for the publisher to forward to the broker.
    """

    telemetry_ready = pyqtSignal(dict)   # emits the full telemetry dict

    # Per-joint oscillation parameters — natural-looking motion
    _JOINT_PARAMS = [
        {"freq": 0.15, "amp": 25.0, "phase": 0.0,  "offset":  0.0},
        {"freq": 0.12, "amp": 35.0, "phase": 1.2,  "offset": 10.0},
        {"freq": 0.18, "amp": 20.0, "phase": 2.4,  "offset": -5.0},
        {"freq": 0.10, "amp": 30.0, "phase": 0.8,  "offset":  0.0},
        {"freq": 0.22, "amp": 15.0, "phase": 3.1,  "offset":  5.0},
        {"freq": 0.14, "amp": 28.0, "phase": 1.6,  "offset": -8.0},
    ]

    def __init__(self, parent=None):
        super().__init__(parent)

        self._timer = QTimer(self)
        self._timer.setInterval(INTERVAL_MS)
        self._timer.timeout.connect(self._generate)

        self._t = 0.0          # internal time counter (seconds)
        self._running = False
        self._msg_count = 0

        # Joint angle history for sparklines (last 50 per joint)
        self.joint_history: dict[str, list[float]] = {
            f"j{i + 1}": [] for i in range(NUM_JOINTS)
        }

        # Latest generated payload — readable by console UI
        self.latest: dict = {}

    # ── Public API ────────────────────────────────────────────────

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def message_count(self) -> int:
        return self._msg_count

    def start(self):
        """Start generating robot telemetry."""
        if self._running:
            return
        self._running = True
        self._timer.start()

    def stop(self):
        """Stop generating robot telemetry."""
        self._running = False
        self._timer.stop()

    def pause(self):
        """Pause without resetting time counter."""
        if self._running:
            self._timer.stop()
            self._running = False

    def resume(self):
        """Resume from paused state."""
        if not self._running:
            self._running = True
            self._timer.start()

    # ── Internal ──────────────────────────────────────────────────

    def _generate(self):
        """Generate one telemetry frame and emit it."""
        self._t += INTERVAL_MS / 1000.0

        # ── Joint angles: sinusoidal + noise ──────────────────────
        angles: list[float] = []
        for i in range(NUM_JOINTS):
            p = self._JOINT_PARAMS[i]
            angle = (
                p["offset"]
                + p["amp"] * math.sin(2 * math.pi * p["freq"] * self._t + p["phase"])
                + random.gauss(0, 0.3)
            )
            lo, hi = JOINT_LIMITS[i]
            angle = max(lo, min(hi, angle))
            angle = round(angle, 2)
            angles.append(angle)

            hist = self.joint_history[f"j{i + 1}"]
            hist.append(angle)
            if len(hist) > 50:
                hist.pop(0)

        # ── Simplified forward kinematics ─────────────────────────
        L1, L2, L3 = 150.0, 300.0, 250.0   # link lengths in mm
        r1 = math.radians(angles[0])
        r2 = math.radians(angles[1])
        r3 = math.radians(angles[2])

        x = (L2 * math.cos(r2) + L3 * math.cos(r2 + r3)) * math.cos(r1)
        y = (L2 * math.cos(r2) + L3 * math.cos(r2 + r3)) * math.sin(r1)
        z = L1 + L2 * math.sin(r2) + L3 * math.sin(r2 + r3)

        # ── End effector derived values ────────────────────────────
        ee_rotation = round(
            angles[3] + angles[4] * 0.5 + angles[5] * 0.3, 2
        )

        # ── Motion state ──────────────────────────────────────────
        if self._t % 30 < 2:
            motion_state = "REPOSITIONING"
        elif self._t % 60 < 1:
            motion_state = "CALIBRATING"
        else:
            motion_state = "MOVING"

        # ── Servo / torque diagnostics ────────────────────────────
        servo_status = "NOMINAL"
        torque_status = "NOMINAL"
        if random.random() < 0.02:
            servo_status = "WARM"
        if any(abs(a) > 140 for a in angles):
            torque_status = "ELEVATED"

        # ── CPU usage (real system metric) ────────────────────────
        try:
            cpu = psutil.cpu_percent(interval=None)
        except Exception:
            cpu = 0.0

        payload = {
            "timestamp":            datetime.now().isoformat(),
            "robot_status":         "ACTIVE",
            "motion_state":         motion_state,
            "servo_status":         servo_status,
            "torque_status":        torque_status,
            "end_effector_rotation": ee_rotation,
            "joint_angles": {
                "j1": angles[0], "j2": angles[1], "j3": angles[2],
                "j4": angles[3], "j5": angles[4], "j6": angles[5],
            },
            "tool_position": {
                "x": round(x, 2),
                "y": round(y, 2),
                "z": round(z, 2),
            },
            "velocity":         0.0,
            "force":            round(random.gauss(0.8, 0.15), 3),
            "motion_enabled":   motion_state != "IDLE",
            "emergency_status": "CLEAR",
            "cpu_usage":        cpu,
            "latency":          round(random.gauss(1.2, 0.3), 2),
        }

        self.latest = payload
        self._msg_count += 1
        self.telemetry_ready.emit(payload)
