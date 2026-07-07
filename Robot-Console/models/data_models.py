# ═══════════════════════════════════════════════════════════════════
#  ROBOT CONSOLE — DATA MODELS
#  Shared data structures for telemetry, alerts, and vitals.
# ═══════════════════════════════════════════════════════════════════

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class JointAngles:
    """Current angles for all 6 robot joints (degrees)."""
    j1: float = 0.0
    j2: float = 0.0
    j3: float = 0.0
    j4: float = 0.0
    j5: float = 0.0
    j6: float = 0.0

    def to_dict(self) -> dict:
        return {"j1": self.j1, "j2": self.j2, "j3": self.j3,
                "j4": self.j4, "j5": self.j5, "j6": self.j6}


@dataclass
class ToolPosition:
    """End effector position in Cartesian space (mm)."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def to_dict(self) -> dict:
        return {"x": round(self.x, 2), "y": round(self.y, 2),
                "z": round(self.z, 2)}


@dataclass
class RobotTelemetry:
    """Complete robot telemetry snapshot."""
    timestamp: str = ""
    robot_status: str = "IDLE"
    joint_angles: JointAngles = field(default_factory=JointAngles)
    tool_position: ToolPosition = field(default_factory=ToolPosition)
    end_effector_rotation: float = 0.0
    motion_state: str = "IDLE"
    servo_status: str = "NOMINAL"
    torque_status: str = "NOMINAL"

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp or datetime.now().isoformat(),
            "robot_status": self.robot_status,
            "joint_angles": self.joint_angles.to_dict(),
            "tool_position": self.tool_position.to_dict(),
            "end_effector_rotation": round(self.end_effector_rotation, 2),
            "motion_state": self.motion_state,
            "servo_status": self.servo_status,
            "torque_status": self.torque_status,
        }


@dataclass
class AlertEntry:
    """A single alert record."""
    timestamp: str = ""
    severity: str = "INFO"         # CRITICAL, WARNING, INFO
    source: str = ""
    message: str = ""

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "severity": self.severity,
            "source": self.source,
            "message": self.message,
        }


@dataclass
class PatientVitals:
    """Patient vital signs received from the Surgeon Console."""
    heart_rate: float = 0.0
    blood_pressure_sys: float = 0.0
    blood_pressure_dia: float = 0.0
    oxygen_saturation: float = 0.0
    respiration_rate: float = 0.0
    body_temperature: float = 0.0
    etco2: float = 0.0
    ecg_status: str = "---"

    def to_dict(self) -> dict:
        return {
            "heart_rate": round(self.heart_rate, 1),
            "blood_pressure_sys": round(self.blood_pressure_sys, 0),
            "blood_pressure_dia": round(self.blood_pressure_dia, 0),
            "oxygen_saturation": round(self.oxygen_saturation, 1),
            "respiration_rate": round(self.respiration_rate, 0),
            "body_temperature": round(self.body_temperature, 1),
            "etco2": round(self.etco2, 1),
            "ecg_status": self.ecg_status,
        }


@dataclass
class ConnectionStats:
    """TCP connection statistics."""
    is_connected: bool = False
    remote_address: str = ""
    packets_sent: int = 0
    packets_received: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    errors: int = 0
    last_sent_time: str = "---"
    last_received_time: str = "---"
    data_rate_in: float = 0.0      # bytes/sec
    data_rate_out: float = 0.0     # bytes/sec
    latency_ms: float = 0.0
    reconnect_count: int = 0
