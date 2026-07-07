# ═══════════════════════════════════════════════════════════════════
#  ROBOT CONSOLE — PATIENT VITALS TAB
#  Displays patient vital signs received from the Surgeon Console
#  via TCP. Matches the Surgeon Console's Patient Vitals layout.
# ═══════════════════════════════════════════════════════════════════

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPainter, QPen, QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame,
    QScrollArea, QSizePolicy,
)

from constants import C
from ui.widgets import (
    CardFrame, SectionHeader, VitalCard, KeyValueRow, SparklineWidget,
)


class PatientVitalsTab(QWidget):
    """Patient Vitals tab — mirrors the Surgeon Console's ICU-style
    monitoring dashboard. All data comes from TCP, not local generation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {C['bg0']};")

        # Vital sign history for sparklines
        self._vital_history = {
            "HR": [], "SpO2": [], "EtCO2": [],
        }

        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        # ── Header ────────────────────────────────────────────────
        main_layout.addWidget(SectionHeader(
            "PATIENT VITALS — LIVE MONITORING  (Data from Surgeon Console)",
            C["green"]))

        # ── Top Row: 6 Monitoring Cards ───────────────────────────
        top_grid = QGridLayout()
        top_grid.setSpacing(6)

        vitals_cfg = [
            ("HR",      "bpm",  C["pink"],   True),
            ("SpO₂",    "%",    C["cyan"],   True),
            ("NIBP",    "mmHg", C["violet"], False),
            ("EtCO₂",   "mmHg", C["teal"],   True),
            ("RR",      "br/m", C["amber"],  False),
            ("Temp",    "°C",   C["green"],  False),
        ]

        self._vital_cards = {}
        for col, (key, unit, color, spark) in enumerate(vitals_cfg):
            vc = VitalCard(key, unit, color, show_sparkline=spark)
            vc.set_value("---")
            vc.set_status("WAITING", C["txt2"])
            top_grid.addWidget(vc, 0, col)
            self._vital_cards[key] = vc

        main_layout.addLayout(top_grid)

        # ── Middle Row: Vital Trends + Clinical Status ────────────
        mid_layout = QHBoxLayout()
        mid_layout.setSpacing(6)

        # Left: Vital Trends Graph
        trends_widget = QWidget()
        trends_layout = QVBoxLayout(trends_widget)
        trends_layout.setContentsMargins(0, 0, 0, 0)
        trends_layout.setSpacing(4)

        trends_layout.addWidget(SectionHeader("VITAL TRENDS", C["cyan"]))

        trends_card = CardFrame()
        tc_layout = QVBoxLayout(trends_card)
        tc_layout.setContentsMargins(6, 6, 6, 6)

        self._trends_canvas = VitalTrendsCanvas()
        tc_layout.addWidget(self._trends_canvas)

        # Legend
        legend = QWidget()
        legend.setStyleSheet(f"background-color: {C['bg2']};")
        leg_layout = QHBoxLayout(legend)
        leg_layout.setContentsMargins(10, 4, 10, 4)
        for label, color in [("HR", C["pink"]),
                              ("SpO₂", C["cyan"]),
                              ("EtCO₂", C["teal"])]:
            dot = QFrame()
            dot.setFixedSize(12, 3)
            dot.setStyleSheet(f"background-color: {color};")
            leg_layout.addWidget(dot)
            lbl = QLabel(label)
            lbl.setFont(QFont("Consolas", 8))
            lbl.setStyleSheet(f"color: {color};")
            leg_layout.addWidget(lbl)
            leg_layout.addSpacing(8)
        leg_layout.addStretch()
        tc_layout.addWidget(legend)

        trends_layout.addWidget(trends_card)

        mid_layout.addWidget(trends_widget, stretch=3)

        # Right: Clinical Status
        clinical_widget = QWidget()
        clinical_widget.setFixedWidth(380)
        cl_layout = QVBoxLayout(clinical_widget)
        cl_layout.setContentsMargins(0, 0, 0, 0)
        cl_layout.setSpacing(4)

        cl_layout.addWidget(SectionHeader("CLINICAL STATUS", C["green"]))

        self._clinical_items = {}
        clinical_data = [
            ("Hemodynamic Status",  "WAITING",  C["txt2"],
             "BP and HR data pending"),
            ("Respiratory Status",  "WAITING",  C["txt2"],
             "RR and EtCO₂ data pending"),
            ("Oxygenation Status",  "WAITING",  C["txt2"],
             "SpO₂ data pending"),
            ("Temperature Status",  "WAITING",  C["txt2"],
             "Core temp data pending"),
        ]
        for title, status, color, desc in clinical_data:
            ci = CardFrame()
            ci_layout = QVBoxLayout(ci)
            ci_layout.setContentsMargins(10, 8, 10, 8)

            top_row = QHBoxLayout()
            title_lbl = QLabel(title)
            title_lbl.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
            title_lbl.setStyleSheet(f"color: {C['txt0']}; border: none;")
            top_row.addWidget(title_lbl)

            status_lbl = QLabel(status)
            status_lbl.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
            status_lbl.setStyleSheet(f"color: {color}; border: none;")
            status_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            top_row.addWidget(status_lbl)

            ci_layout.addLayout(top_row)

            desc_lbl = QLabel(desc)
            desc_lbl.setFont(QFont("Consolas", 7))
            desc_lbl.setStyleSheet(f"color: {C['txt2']}; border: none;")
            ci_layout.addWidget(desc_lbl)

            cl_layout.addWidget(ci)
            self._clinical_items[title] = {
                "status_lbl": status_lbl,
                "desc_lbl": desc_lbl,
            }

        cl_layout.addStretch()
        mid_layout.addWidget(clinical_widget)

        main_layout.addLayout(mid_layout, stretch=1)

        # ── Bottom: ECG Status + Vital Events Log ─────────────────
        main_layout.addWidget(SectionHeader("ECG STATUS", C["pink"]))

        ecg_card = CardFrame()
        ecg_layout = QHBoxLayout(ecg_card)
        ecg_layout.setContentsMargins(12, 8, 12, 8)

        ecg_lbl = QLabel("ECG")
        ecg_lbl.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        ecg_lbl.setStyleSheet(f"color: {C['txt1']}; border: none;")
        ecg_layout.addWidget(ecg_lbl)

        self._ecg_value = QLabel("---")
        self._ecg_value.setFont(QFont("Consolas", 14, QFont.Weight.Bold))
        self._ecg_value.setStyleSheet(f"color: {C['pink']}; border: none;")
        ecg_layout.addWidget(self._ecg_value)

        ecg_layout.addStretch()

        self._ecg_status = QLabel("WAITING FOR DATA")
        self._ecg_status.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
        self._ecg_status.setStyleSheet(f"color: {C['txt2']}; border: none;")
        ecg_layout.addWidget(self._ecg_status)

        main_layout.addWidget(ecg_card)

    # ─── Public Update Methods ────────────────────────────────────

    def update_vitals(self, vitals_data: dict):
        """Update all vital sign displays from received TCP data.

        Expected keys in vitals_data payload:
            hr, spo2, nibp_s, nibp_d, etco2, rr, temp, ecg_status
        """
        payload = vitals_data.get("payload", vitals_data)

        hr = payload.get("hr", 0)
        spo2 = payload.get("spo2", 0)
        nibp_s = payload.get("nibp_s", 0)
        nibp_d = payload.get("nibp_d", 0)
        etco2 = payload.get("etco2", 0)
        rr = payload.get("rr", 0)
        temp = payload.get("temp", 0)
        ecg = payload.get("ecg_status", "NORMAL SINUS")

        # Update vital cards
        if "HR" in self._vital_cards:
            self._vital_cards["HR"].set_value(f"{hr:.0f}")
            oor = hr < 50 or hr > 100
            self._vital_cards["HR"].set_status(
                "⚠ OOR" if oor else "✔ OK",
                C["red"] if oor else C["green"])

        if "SpO₂" in self._vital_cards:
            self._vital_cards["SpO₂"].set_value(f"{spo2:.1f}")
            oor = spo2 < 95
            self._vital_cards["SpO₂"].set_status(
                "⚠ LOW" if oor else "✔ OK",
                C["red"] if oor else C["green"])

        if "NIBP" in self._vital_cards:
            self._vital_cards["NIBP"].set_value(
                f"{nibp_s:.0f}/{nibp_d:.0f}")
            self._vital_cards["NIBP"].set_status("✔ OK", C["green"])

        if "EtCO₂" in self._vital_cards:
            self._vital_cards["EtCO₂"].set_value(f"{etco2:.1f}")
            oor = etco2 < 30 or etco2 > 45
            self._vital_cards["EtCO₂"].set_status(
                "⚠ OOR" if oor else "✔ OK",
                C["amber"] if oor else C["green"])

        if "RR" in self._vital_cards:
            self._vital_cards["RR"].set_value(f"{rr:.0f}")
            oor = rr < 12 or rr > 20
            self._vital_cards["RR"].set_status(
                "⚠ OOR" if oor else "✔ OK",
                C["amber"] if oor else C["green"])

        if "Temp" in self._vital_cards:
            self._vital_cards["Temp"].set_value(f"{temp:.1f}")
            oor = temp < 36 or temp > 37.5
            self._vital_cards["Temp"].set_status(
                "⚠ OOR" if oor else "✔ OK",
                C["amber"] if oor else C["green"])

        # ECG Status
        self._ecg_value.setText(ecg)
        if "normal" in ecg.lower():
            self._ecg_status.setText("✔ NORMAL")
            self._ecg_status.setStyleSheet(
                f"color: {C['green']}; border: none;")
        else:
            self._ecg_status.setText("⚠ ABNORMAL")
            self._ecg_status.setStyleSheet(
                f"color: {C['red']}; border: none;")

        # Update sparklines
        self._vital_history["HR"].append(hr)
        self._vital_history["SpO2"].append(spo2)
        self._vital_history["EtCO2"].append(etco2)
        for k in self._vital_history:
            if len(self._vital_history[k]) > 60:
                self._vital_history[k].pop(0)

        if "HR" in self._vital_cards:
            self._vital_cards["HR"].update_sparkline(
                self._vital_history["HR"])
        if "SpO₂" in self._vital_cards:
            self._vital_cards["SpO₂"].update_sparkline(
                self._vital_history["SpO2"])
        if "EtCO₂" in self._vital_cards:
            self._vital_cards["EtCO₂"].update_sparkline(
                self._vital_history["EtCO2"])

        # Update trends canvas
        self._trends_canvas.set_data(self._vital_history)

        # Update clinical status
        self._update_clinical_status(hr, spo2, nibp_s, etco2, rr, temp)

    def _update_clinical_status(self, hr, spo2, nibp_s, etco2, rr, temp):
        """Update the clinical status panel based on vital values."""
        # Hemodynamic
        hemo = self._clinical_items.get("Hemodynamic Status")
        if hemo:
            if hr < 50 or hr > 100 or nibp_s > 160 or nibp_s < 90:
                hemo["status_lbl"].setText("⚠ ABNORMAL")
                hemo["status_lbl"].setStyleSheet(
                    f"color: {C['amber']}; border: none;")
            else:
                hemo["status_lbl"].setText("STABLE")
                hemo["status_lbl"].setStyleSheet(
                    f"color: {C['green']}; border: none;")

        # Respiratory
        resp = self._clinical_items.get("Respiratory Status")
        if resp:
            if rr < 10 or rr > 22 or etco2 > 50 or etco2 < 28:
                resp["status_lbl"].setText("⚠ ABNORMAL")
                resp["status_lbl"].setStyleSheet(
                    f"color: {C['amber']}; border: none;")
            else:
                resp["status_lbl"].setText("NORMAL")
                resp["status_lbl"].setStyleSheet(
                    f"color: {C['green']}; border: none;")

        # Oxygenation
        oxy = self._clinical_items.get("Oxygenation Status")
        if oxy:
            if spo2 < 95:
                oxy["status_lbl"].setText("⚠ LOW")
                oxy["status_lbl"].setStyleSheet(
                    f"color: {C['red']}; border: none;")
            else:
                oxy["status_lbl"].setText("ADEQUATE")
                oxy["status_lbl"].setStyleSheet(
                    f"color: {C['green']}; border: none;")

        # Temperature
        tmp = self._clinical_items.get("Temperature Status")
        if tmp:
            if temp < 36 or temp > 37.5:
                tmp["status_lbl"].setText("⚠ ABNORMAL")
                tmp["status_lbl"].setStyleSheet(
                    f"color: {C['amber']}; border: none;")
            else:
                tmp["status_lbl"].setText("NORMAL")
                tmp["status_lbl"].setStyleSheet(
                    f"color: {C['green']}; border: none;")


# ═══════════════════════════════════════════════════════════════════
#  VITAL TRENDS CANVAS — Multi-line graph
# ═══════════════════════════════════════════════════════════════════

class VitalTrendsCanvas(QWidget):
    """Custom QPainter widget that draws a multi-line vital trends graph."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Expanding)
        self.setStyleSheet(f"background-color: {C['bg2']};")
        self._data = {}

    def set_data(self, data: dict):
        self._data = data
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # Background
        painter.fillRect(0, 0, w, h, QColor(C["bg2"]))

        datasets = [
            ("HR",    self._data.get("HR", []),    50, 120, C["pink"]),
            ("SpO2",  self._data.get("SpO2", []),  92, 100, C["cyan"]),
            ("EtCO2", self._data.get("EtCO2", []), 28, 50,  C["teal"]),
        ]

        ml, mr, mt, mb = 40, 10, 10, 25
        cw = w - ml - mr
        ch = h - mt - mb

        if cw < 10 or ch < 10:
            painter.end()
            return

        # Grid lines
        pen = QPen(QColor(C["bg3"]))
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        for i in range(5):
            y = mt + i * ch // 4
            painter.drawLine(ml, y, w - mr, y)

        # Draw each dataset
        for label, data, lo, hi, color in datasets:
            if len(data) < 2:
                continue
            rng = hi - lo or 1
            pen = QPen(QColor(color), 2)
            painter.setPen(pen)

            from PyQt6.QtGui import QPainterPath
            path = QPainterPath()
            for i, v in enumerate(data):
                x = ml + i / max(len(data) - 1, 1) * cw
                y = mt + (1 - (v - lo) / rng) * ch
                if i == 0:
                    path.moveTo(x, y)
                else:
                    path.lineTo(x, y)
            painter.drawPath(path)

            # Label at end of line
            if data:
                last_y = mt + (1 - (data[-1] - lo) / rng) * ch
                painter.drawText(int(w - mr - 4), int(last_y), label)

        # Axes
        pen = QPen(QColor(C["border2"]), 1)
        painter.setPen(pen)
        painter.drawLine(ml, mt, ml, h - mb)
        painter.drawLine(ml, h - mb, w - mr, h - mb)

        # Time axis labels
        data_len = max((len(d) for _, d, _, _, _ in datasets), default=0)
        if data_len > 1:
            pen = QPen(QColor(C["txt2"]))
            painter.setPen(pen)
            painter.setFont(QFont("Consolas", 6))
            for i in range(0, data_len, max(1, data_len // 6)):
                x = ml + i / max(data_len - 1, 1) * cw
                painter.drawText(int(x) - 10, h - 4,
                                 f"-{data_len - i}s")

        painter.end()
