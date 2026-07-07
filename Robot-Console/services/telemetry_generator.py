# ═══════════════════════════════════════════════════════════════════
#  ROBOT CONSOLE — TELEMETRY GENERATOR
#  Continuously generates realistic 6-DOF robotic arm data
#  at 100 updates per minute (~600ms interval).
# ═══════════════════════════════════════════════════════════════════

import math
import random
from datetime import datetime

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from models.data_models import RobotTelemetry, JointAngles, ToolPosition
from constants import TELEMETRY_UPDATE_INTERVAL_MS, JOINT_LIMITS, NUM_JOINTS


class TelemetryGenerator(QObject):
    """Generates continuous, realistic robotic arm telemetry data.

    Uses smooth sinusoidal motion with Gaussian noise to simulate
    realistic joint movements. Tool position is derived from a
    simplified forward kinematics model.
    """

    telemetry_updated = pyqtSignal(RobotTelemetry)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.setInterval(TELEMETRY_UPDATE_INTERVAL_MS)
        self._timer.timeout.connect(self._generate)

        self._t = 0.0                        # Internal time counter
        self._running = False
        self._telemetry = RobotTelemetry()

        # Per-joint oscillation parameters for natural-looking motion
        self._joint_params = [
            {"freq": 0.15,  "amp": 25.0,  "phase": 0.0,   "offset": 0.0},
            {"freq": 0.12,  "amp": 35.0,  "phase": 1.2,   "offset": 10.0},
            {"freq": 0.18,  "amp": 20.0,  "phase": 2.4,   "offset": -5.0},
            {"freq": 0.10,  "amp": 30.0,  "phase": 0.8,   "offset": 0.0},
            {"freq": 0.22,  "amp": 15.0,  "phase": 3.1,   "offset": 5.0},
            {"freq": 0.14,  "amp": 28.0,  "phase": 1.6,   "offset": -8.0},
        ]

        # Joint angle history for sparklines (last 50 values per joint)
        self.joint_history = {f"j{i+1}": [] for i in range(NUM_JOINTS)}

    # ─── Public API ───────────────────────────────────────────────

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def current_telemetry(self) -> RobotTelemetry:
        return self._telemetry

    def start(self):
        """Start generating telemetry data."""
        if self._running:
            return
        self._running = True
        self._telemetry.robot_status = "ACTIVE"
        self._telemetry.motion_state = "MOVING"
        self._timer.start()

    def stop(self):
        """Stop telemetry generation."""
        self._running = False
        self._timer.stop()
        self._telemetry.robot_status = "IDLE"
        self._telemetry.motion_state = "IDLE"

    # ─── Internal ─────────────────────────────────────────────────

    def _generate(self):
        """Generate one telemetry frame."""
        self._t += TELEMETRY_UPDATE_INTERVAL_MS / 1000.0

        # Generate joint angles with smooth sinusoidal motion + noise
        angles = []
        for i in range(NUM_JOINTS):
            p = self._joint_params[i]
            angle = (p["offset"]
                     + p["amp"] * math.sin(2 * math.pi * p["freq"] * self._t
                                           + p["phase"])
                     + random.gauss(0, 0.3))
            lo, hi = JOINT_LIMITS[i]
            angle = max(lo, min(hi, angle))
            angles.append(round(angle, 2))

            # Update history
            hist = self.joint_history[f"j{i+1}"]
            hist.append(angle)
            if len(hist) > 50:
                hist.pop(0)

        # Build joint angles
        ja = JointAngles(j1=angles[0], j2=angles[1], j3=angles[2],
                         j4=angles[3], j5=angles[4], j6=angles[5])

        # Simplified forward kinematics for tool position
        # Uses first 3 joints to compute approximate XYZ
        L1, L2, L3 = 150.0, 300.0, 250.0  # Link lengths in mm
        r1 = math.radians(angles[0])
        r2 = math.radians(angles[1])
        r3 = math.radians(angles[2])

        x = (L2 * math.cos(r2) + L3 * math.cos(r2 + r3)) * math.cos(r1)
        y = (L2 * math.cos(r2) + L3 * math.cos(r2 + r3)) * math.sin(r1)
        z = L1 + L2 * math.sin(r2) + L3 * math.sin(r2 + r3)

        tp = ToolPosition(x=round(x, 2), y=round(y, 2), z=round(z, 2))

        # End effector rotation from joints 4-6
        ee_rotation = round(angles[3] + angles[4] * 0.5 + angles[5] * 0.3, 2)

        # Motion state varies based on joint velocities
        motion_state = "MOVING"
        if self._t % 30 < 2:
            motion_state = "REPOSITIONING"
        elif self._t % 60 < 1:
            motion_state = "CALIBRATING"

        # Servo and torque status — occasionally show warnings
        servo_status = "NOMINAL"
        torque_status = "NOMINAL"
        if random.random() < 0.02:
            servo_status = "WARM"
        if any(abs(a) > 140 for a in angles):
            torque_status = "ELEVATED"

        # Assemble telemetry
        self._telemetry = RobotTelemetry(
            timestamp=datetime.now().isoformat(),
            robot_status="ACTIVE",
            joint_angles=ja,
            tool_position=tp,
            end_effector_rotation=ee_rotation,
            motion_state=motion_state,
            servo_status=servo_status,
            torque_status=torque_status,
        )

        self.telemetry_updated.emit(self._telemetry)
