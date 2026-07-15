# ═══════════════════════════════════════════════════════════════════
#  ROBOT CONSOLE — ROBOT TELEMETRY TAB
#  Displays continuously generated 6-DOF robotic arm data
#  including joint angles, tool position, and system status.
# ═══════════════════════════════════════════════════════════════════

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame,
    QSizePolicy,
)

from constants import C, NUM_JOINTS
from ui.widgets import (
    CardFrame, SectionHeader, StatusBadge, SparklineWidget,
    MetricCard, KeyValueRow,
)
from models.data_models import RobotTelemetry


class RobotTelemetryTab(QWidget):
    """Robot Telemetry tab — displays 6-DOF joint angles, tool position,
    end effector data, and system status.  Data is received from the
    Data Generator backend via the pub-sub broker."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {C['bg0']};")
        self._build_ui()

    def _build_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # ── LEFT PANEL: Joint Angles ──────────────────────────────
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)

        left_layout.addWidget(SectionHeader("JOINT ANGLES", C["amber"]))

        joint_colors = [
            C["cyan"], C["violet"], C["teal"],
            C["pink"], C["amber"], C["green"],
        ]

        self._joint_widgets = {}
        for i in range(NUM_JOINTS):
            color = joint_colors[i]
            joint_card = CardFrame()
            jc_layout = QVBoxLayout(joint_card)
            jc_layout.setContentsMargins(14, 12, 14, 12)
            jc_layout.setSpacing(4)

            # Header row: Joint name + value
            header = QHBoxLayout()

            # Colored dot
            dot = QFrame()
            dot.setFixedSize(8, 8)
            dot.setStyleSheet(f"""
                background-color: {color};
                border-radius: 4px;
            """)
            header.addWidget(dot)

            name_lbl = QLabel(f"  Joint {i + 1}")
            name_lbl.setFont(QFont("Consolas", 20, QFont.Weight.Bold))
            name_lbl.setStyleSheet(f"color: {C['txt0']}; border: none;")
            header.addWidget(name_lbl)

            header.addStretch()

            val_lbl = QLabel("0.00°")
            val_lbl.setFont(QFont("Consolas", 28, QFont.Weight.Bold))
            val_lbl.setStyleSheet(f"color: {color}; border: none;")
            header.addWidget(val_lbl)

            jc_layout.addLayout(header)

            # Sparkline
            spark = SparklineWidget(color=color, width=200, height=28)
            jc_layout.addWidget(spark)

            left_layout.addWidget(joint_card)
            self._joint_widgets[f"j{i+1}"] = {
                "value": val_lbl,
                "sparkline": spark,
                "color": color,
            }

        left_layout.addStretch()
        main_layout.addWidget(left_panel, stretch=2)

        # ── CENTER PANEL: Tool Position ───────────────────────────
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(4)

        center_layout.addWidget(SectionHeader(
            "TOOL POSITION", C["teal"]))

        # XYZ Position Cards
        self._pos_cards = {}
        for axis, color in [("X", C["cyan"]), ("Y", C["violet"]),
                             ("Z", C["teal"])]:
            pos_card = CardFrame()
            pc_layout = QHBoxLayout(pos_card)
            pc_layout.setContentsMargins(16, 16, 16, 16)

            axis_lbl = QLabel(f"{axis} :")
            axis_lbl.setFont(QFont("Consolas", 22, QFont.Weight.Bold))
            axis_lbl.setStyleSheet(f"color: {C['txt2']}; border: none;")
            pc_layout.addWidget(axis_lbl)

            pc_layout.addStretch()

            val_lbl = QLabel("0.00 mm")
            val_lbl.setFont(QFont("Consolas", 32, QFont.Weight.Bold))
            val_lbl.setStyleSheet(f"color: {color}; border: none;")
            pc_layout.addWidget(val_lbl)

            center_layout.addWidget(pos_card)
            self._pos_cards[axis] = val_lbl

        # End Effector Rotation
        center_layout.addWidget(SectionHeader(
            "END EFFECTOR", C["green"]))

        ee_card = CardFrame()
        ee_layout = QHBoxLayout(ee_card)
        ee_layout.setContentsMargins(16, 16, 16, 16)

        ee_lbl = QLabel("ROTATION :")
        ee_lbl.setFont(QFont("Consolas", 20, QFont.Weight.Bold))
        ee_lbl.setStyleSheet(f"color: {C['txt2']}; border: none;")
        ee_layout.addWidget(ee_lbl)

        ee_layout.addStretch()

        self._ee_rotation = QLabel("0.00°")
        self._ee_rotation.setFont(
            QFont("Consolas", 32, QFont.Weight.Bold))
        self._ee_rotation.setStyleSheet(
            f"color: {C['green']}; border: none;")
        ee_layout.addWidget(self._ee_rotation)

        center_layout.addWidget(ee_card)

        # Reach
        reach_card = CardFrame()
        rc_layout = QHBoxLayout(reach_card)
        rc_layout.setContentsMargins(16, 16, 16, 16)

        reach_lbl = QLabel("REACH :")
        reach_lbl.setFont(QFont("Consolas", 20, QFont.Weight.Bold))
        reach_lbl.setStyleSheet(f"color: {C['txt2']}; border: none;")
        rc_layout.addWidget(reach_lbl)

        rc_layout.addStretch()

        self._reach_value = QLabel("0.00 mm")
        self._reach_value.setFont(
            QFont("Consolas", 32, QFont.Weight.Bold))
        self._reach_value.setStyleSheet(
            f"color: {C['cyan']}; border: none;")
        rc_layout.addWidget(self._reach_value)

        center_layout.addWidget(reach_card)
        center_layout.addStretch()

        main_layout.addWidget(center_panel, stretch=2)

        # ── RIGHT PANEL: Status ───────────────────────────────────
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(4)

        right_layout.addWidget(SectionHeader(
            "ROBOT STATUS", C["cyan"]))

        # Motion State
        self._motion_card = self._build_status_item(
            "Motion State", "IDLE", C["txt2"])
        right_layout.addWidget(self._motion_card["card"])

        # Servo Status
        self._servo_card = self._build_status_item(
            "Servo Status", "NOMINAL", C["green"])
        right_layout.addWidget(self._servo_card["card"])

        # Torque Status
        self._torque_card = self._build_status_item(
            "Torque Status", "NOMINAL", C["green"])
        right_layout.addWidget(self._torque_card["card"])

        # Robot Status badge
        right_layout.addWidget(SectionHeader(
            "SYSTEM", C["violet"]))

        self._robot_status_badge = StatusBadge("IDLE", C["txt2"])
        right_layout.addWidget(self._robot_status_badge)

        # Update rate info
        right_layout.addWidget(SectionHeader(
            "UPDATE RATE", C["teal"]))

        rate_card = CardFrame()
        rate_layout = QVBoxLayout(rate_card)
        rate_layout.setContentsMargins(12, 10, 12, 10)

        rate_lbl = QLabel("100 updates / min")
        rate_lbl.setFont(QFont("Consolas", 20, QFont.Weight.Bold))
        rate_lbl.setStyleSheet(f"color: {C['teal']}; border: none;")
        rate_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rate_layout.addWidget(rate_lbl)

        freq_lbl = QLabel("≈ 600ms interval")
        freq_lbl.setFont(QFont("Consolas", 16))
        freq_lbl.setStyleSheet(f"color: {C['txt2']}; border: none;")
        freq_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rate_layout.addWidget(freq_lbl)

        right_layout.addWidget(rate_card)

        # Telemetry counter
        self._update_count = 0
        self._counter_lbl = QLabel("Updates: 0")
        self._counter_lbl.setFont(QFont("Consolas", 16))
        self._counter_lbl.setStyleSheet(
            f"color: {C['txt2']}; background-color: {C['bg0']};")
        right_layout.addWidget(self._counter_lbl)

        right_layout.addStretch()
        main_layout.addWidget(right_panel, stretch=1)

    def _build_status_item(self, label: str, value: str,
                            color: str) -> dict:
        """Build a labelled status card."""
        card = CardFrame()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        lbl = QLabel(label)
        lbl.setFont(QFont("Consolas", 18, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {C['txt1']}; border: none;")
        layout.addWidget(lbl)

        val = QLabel(value)
        val.setFont(QFont("Consolas", 28, QFont.Weight.Bold))
        val.setStyleSheet(f"color: {color}; border: none;")
        layout.addWidget(val)

        return {"card": card, "value": val}

    # ─── Public Update ────────────────────────────────────────────

    def update_telemetry(self, telemetry: RobotTelemetry,
                         joint_history: dict):
        """Update all telemetry displays."""
        self._update_count += 1
        self._counter_lbl.setText(f"Updates: {self._update_count}")

        ja = telemetry.joint_angles
        tp = telemetry.tool_position

        # Joint angles
        for i, angle in enumerate([ja.j1, ja.j2, ja.j3,
                                    ja.j4, ja.j5, ja.j6]):
            key = f"j{i+1}"
            w = self._joint_widgets.get(key)
            if w:
                w["value"].setText(f"{angle:.2f}°")
                hist = joint_history.get(key, [])
                if hist:
                    w["sparkline"].update_data(hist)

        # Tool position
        self._pos_cards["X"].setText(f"{tp.x:.2f} mm")
        self._pos_cards["Y"].setText(f"{tp.y:.2f} mm")
        self._pos_cards["Z"].setText(f"{tp.z:.2f} mm")

        # EE Rotation
        self._ee_rotation.setText(
            f"{telemetry.end_effector_rotation:.2f}°")

        # Reach (distance from origin)
        import math
        reach = math.sqrt(tp.x**2 + tp.y**2 + tp.z**2)
        self._reach_value.setText(f"{reach:.2f} mm")

        # Motion state
        ms = telemetry.motion_state
        ms_color = C["green"] if ms == "MOVING" else (
            C["amber"] if ms == "REPOSITIONING" else C["cyan"])
        self._motion_card["value"].setText(ms)
        self._motion_card["value"].setStyleSheet(
            f"color: {ms_color}; border: none;")

        # Servo status
        ss = telemetry.servo_status
        ss_color = C["green"] if ss == "NOMINAL" else C["amber"]
        self._servo_card["value"].setText(ss)
        self._servo_card["value"].setStyleSheet(
            f"color: {ss_color}; border: none;")

        # Torque status
        ts = telemetry.torque_status
        ts_color = C["green"] if ts == "NOMINAL" else C["amber"]
        self._torque_card["value"].setText(ts)
        self._torque_card["value"].setStyleSheet(
            f"color: {ts_color}; border: none;")

        # Robot status badge
        rs = telemetry.robot_status
        rs_color = C["green"] if rs == "ACTIVE" else C["txt2"]
        self._robot_status_badge.set_text_and_color(rs, rs_color)

    def update_telemetry_from_dict(self, payload: dict):
        """Update all telemetry displays from a raw broker payload dict.

        Called when telemetry arrives via the pub-sub bridge from the
        Data Generator backend (no local ``RobotTelemetry`` object).
        """
        import math

        self._update_count += 1
        self._counter_lbl.setText(f"Updates: {self._update_count}")

        ja = payload.get("joint_angles", {})
        tp = payload.get("tool_position", {})

        # Joint angles
        for i in range(6):
            key = f"j{i + 1}"
            angle = ja.get(key, 0.0)
            w = self._joint_widgets.get(key)
            if w:
                w["value"].setText(f"{angle:.2f}°")
                # Build a minimal sparkline history from the single new value
                # (we don't have history from the broker — approximate it)
                spark: "SparklineWidget" = w["sparkline"]
                if hasattr(spark, "_data"):
                    spark._data.append(angle)
                    if len(spark._data) > 50:
                        spark._data.pop(0)
                    spark.update()

        # Tool position
        self._pos_cards["X"].setText(f"{tp.get('x', 0.0):.2f} mm")
        self._pos_cards["Y"].setText(f"{tp.get('y', 0.0):.2f} mm")
        self._pos_cards["Z"].setText(f"{tp.get('z', 0.0):.2f} mm")

        # EE Rotation
        self._ee_rotation.setText(
            f"{payload.get('end_effector_rotation', 0.0):.2f}°")

        # Reach
        x = tp.get("x", 0.0)
        y = tp.get("y", 0.0)
        z = tp.get("z", 0.0)
        reach = math.sqrt(x ** 2 + y ** 2 + z ** 2)
        self._reach_value.setText(f"{reach:.2f} mm")

        # Motion state
        ms = payload.get("motion_state", "IDLE")
        ms_color = (C["green"] if ms == "MOVING"
                    else C["amber"] if ms == "REPOSITIONING"
                    else C["cyan"])
        self._motion_card["value"].setText(ms)
        self._motion_card["value"].setStyleSheet(
            f"color: {ms_color}; border: none;")

        # Servo status
        ss = payload.get("servo_status", "NOMINAL")
        ss_color = C["green"] if ss == "NOMINAL" else C["amber"]
        self._servo_card["value"].setText(ss)
        self._servo_card["value"].setStyleSheet(
            f"color: {ss_color}; border: none;")

        # Torque status
        ts = payload.get("torque_status", "NOMINAL")
        ts_color = C["green"] if ts == "NOMINAL" else C["amber"]
        self._torque_card["value"].setText(ts)
        self._torque_card["value"].setStyleSheet(
            f"color: {ts_color}; border: none;")

        # Robot status badge
        rs = payload.get("robot_status", "ACTIVE")
        rs_color = C["green"] if rs == "ACTIVE" else C["txt2"]
        self._robot_status_badge.set_text_and_color(rs, rs_color)

