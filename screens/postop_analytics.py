"""
Post-Operative Analytics tab — Charts, procedure summary, and insights.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QPainterPath, QLinearGradient
from widgets.card import MetricCard, PanelFrame


class LineAreaChart(QFrame):
    def __init__(self, values, color="#0095FF", fill=True):
        super().__init__()
        self.values = values
        self.color = QColor(color)
        self.fill = fill
        self.setMinimumHeight(180)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        if not self.values:
            return
        vmin, vmax = min(self.values), max(self.values)
        vmax = vmax if vmax != vmin else vmin + 1
        n = len(self.values)
        pad = 6
        pts = []
        for i, v in enumerate(self.values):
            x = pad + (w - 2 * pad) * i / (n - 1)
            y = h - pad - (h - 2 * pad) * (v - vmin) / (vmax - vmin)
            pts.append(QPointF(x, y))

        path = QPainterPath()
        path.moveTo(pts[0])
        for pt in pts[1:]:
            path.lineTo(pt)

        if self.fill:
            area = QPainterPath(path)
            area.lineTo(pts[-1].x(), h)
            area.lineTo(pts[0].x(), h)
            area.closeSubpath()
            grad = QLinearGradient(0, 0, 0, h)
            c1 = QColor(self.color)
            c1.setAlpha(90)
            c2 = QColor(self.color)
            c2.setAlpha(0)
            grad.setColorAt(0, c1)
            grad.setColorAt(1, c2)
            p.fillPath(area, grad)

        p.setPen(QPen(self.color, 2))
        p.drawPath(path)


class BarChart(QFrame):
    def __init__(self, labels, values, color="#4A5568"):
        super().__init__()
        self.labels = labels
        self.values = values
        self.color = QColor(color)
        self.setMinimumHeight(180)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height() - 18
        vmax = max(self.values) if self.values else 1
        n = len(self.values)
        gap = w / n
        bar_w = gap * 0.45
        p.setPen(Qt.PenStyle.NoPen)
        for i, v in enumerate(self.values):
            bh = (h - 10) * v / vmax
            x = gap * i + (gap - bar_w) / 2
            y = h - bh
            p.setBrush(self.color)
            p.drawRoundedRect(int(x), int(y), int(bar_w), int(bh), 4, 4)
        p.setPen(QColor("#6B7B8D"))
        for i, lab in enumerate(self.labels):
            x = gap * i
            p.drawText(int(x), h + 16, int(gap), 16, Qt.AlignmentFlag.AlignCenter, lab)


class DualLineChart(QFrame):
    def __init__(self, series_a, series_b, color_a="#20C997", color_b="#E5484D"):
        super().__init__()
        self.series_a = series_a
        self.series_b = series_b
        self.color_a = QColor(color_a)
        self.color_b = QColor(color_b)
        self.setMinimumHeight(180)

    def _draw_series(self, p, values, color, w, h, pad):
        vmin, vmax = 0, 100
        n = len(values)
        pts = []
        for i, v in enumerate(values):
            x = pad + (w - 2 * pad) * i / (n - 1)
            y = h - pad - (h - 2 * pad) * (v - vmin) / (vmax - vmin)
            pts.append(QPointF(x, y))
        path = QPainterPath()
        path.moveTo(pts[0])
        for pt in pts[1:]:
            path.lineTo(pt)
        p.setPen(QPen(color, 2))
        p.drawPath(path)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        pad = 6
        self._draw_series(p, self.series_a, self.color_a, w, h, pad)
        self._draw_series(p, self.series_b, self.color_b, w, h, pad)


class _StatusDot(QWidget):
    def __init__(self, color, parent=None):
        super().__init__(parent)
        self._color = QColor(color)
        self.setFixedSize(10, 10)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(self._color)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(1, 1, 8, 8)
        p.end()


class ChartPanel(QFrame):
    def __init__(self, title, badge_text, badge_color, chart_widget):
        super().__init__()
        self.setObjectName("Card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        header = QHBoxLayout()
        t = QLabel(title.upper())
        t.setObjectName("SectionTitle")
        
        b = QLabel(badge_text)
        b.setStyleSheet(f"color:{badge_color}; font-size:12px; font-weight:700;")
        
        header.addWidget(t)
        header.addStretch()
        header.addWidget(_StatusDot(badge_color))
        header.addSpacing(6)
        header.addWidget(b)
        layout.addLayout(header)
        layout.addWidget(chart_widget, 1)


class InsightCard(QFrame):
    def __init__(self, title, text, color):
        super().__init__()
        self.setObjectName("Card")
        # Ensure we have one of the standard accents in CSS
        accent = "cyan" if color == "#0095FF" else ("amber" if color == "#F4B740" else "green")
        self.setProperty("accent", accent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(6)
        t = QLabel(title)
        t.setStyleSheet(f"color:{color}; font-size:14px; font-weight:700;")
        t.setWordWrap(True)
        d = QLabel(text)
        d.setStyleSheet("color:#B5BEC8; font-size:13px;")
        d.setWordWrap(True)
        layout.addWidget(t)
        layout.addWidget(d)


def info_row(label, value, color="#F5F7FA"):
    row = QHBoxLayout()
    l = QLabel(label)
    l.setObjectName("FieldLabel")
    v = QLabel(value)
    v.setStyleSheet(f"color:{color}; font-size:14px; font-weight:700;")
    row.addWidget(l)
    row.addStretch()
    row.addWidget(v)
    return row


class PostopAnalyticsScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 14, 0, 0)
        outer.setSpacing(16)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)
        cards_row.addWidget(MetricCard("Procedure Duration", "01:42", "hh:mm", "Target \u2264 02:00"))
        cards_row.addWidget(MetricCard("Blood Loss", "42", "mL", "Below mean (78 mL)"))
        cards_row.addWidget(MetricCard("Sutures Placed", "12", sub="100% knot-secure"))
        cards_row.addWidget(MetricCard("Faults / Aborts", "0", sub="Clean session", accent="green", value_color="#20C997"))
        cards_row.addWidget(MetricCard("Peak Tip Force", "4.6", "N", "Limit 8.0 N", accent="amber"))
        cards_row.addWidget(MetricCard("Predicted Outcome", "92", "%", "Favourable", accent="green", value_color="#20C997"))
        outer.addLayout(cards_row)

        charts_row = QHBoxLayout()
        charts_row.setSpacing(14)

        tip_force = [3.0, 3.4, 2.6, 2.0, 1.3, 1.0, 1.6, 2.4, 3.2, 3.6, 3.5, 3.0, 2.4, 1.8, 1.2,
                     1.0, 1.5, 2.2, 3.0, 3.6, 3.8, 3.5, 3.0, 2.4, 1.8, 1.2, 1.0, 1.6, 2.4, 3.2,
                     3.6, 3.5, 3.0, 2.4, 1.8, 1.4, 1.8, 2.6, 3.2, 3.7]
        tip_chart = LineAreaChart(tip_force, color="#0095FF")
        charts_row.addWidget(ChartPanel("Tip Force  ·  Session Trace", "WITHIN LIMITS", "#20C997", tip_chart), 1)

        phase_labels = ["Access", "Insufflate", "Expose", "Dissect", "Clip", "Excise", "Close"]
        phase_values = [4, 3, 11, 16, 7, 9, 5]
        bar_chart = BarChart(phase_labels, phase_values, color="#1C2333")
        charts_row.addWidget(ChartPanel("Time by Phase", "MINUTES", "#6B7B8D", bar_chart), 1)

        spo2 = [97] * 15
        hr_norm = [60, 62, 63, 65, 62, 61, 60, 59, 61, 63, 65, 64, 63, 62, 61]
        dual_chart = DualLineChart(spo2, hr_norm)
        charts_row.addWidget(ChartPanel("Patient Vitals  ·  Trend", "STABLE", "#20C997", dual_chart), 1)

        outer.addLayout(charts_row, 1)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(14)

        summary = PanelFrame("Procedure Summary")
        for lab, val in [("Procedure", "Lap. Cholecystectomy"), ("Patient", "M. K\u00F6hler  ·  58F"),
                          ("Surgeon", "Dr. A. Voss"), ("Start", "08:42 UTC"), ("End", "10:24 UTC"),
                          ("Phases Completed", "7 / 7"), ("EBL", "42 mL")]:
            summary.add_layout(info_row(lab, val))
        summary.add_stretch()
        bottom_row.addWidget(summary, 1)

        outcome = PanelFrame("Outcome Metrics")
        outcome.add_layout(info_row("Margin Status", "R0  ·  negative", "#20C997"))
        outcome.add_layout(info_row("Tissue Trauma", "Minimal", "#20C997"))
        outcome.add_layout(info_row("Adverse Events", "None", "#20C997"))
        outcome.add_layout(info_row("Conversion to Open", "No", "#20C997"))
        outcome.add_layout(info_row("Pain Score (post)", "2 / 10"))
        outcome.add_layout(info_row("LOS Estimate", "1.2 days"))
        outcome.add_layout(info_row("Readmit Risk", "Low (4%)", "#20C997"))
        outcome.add_stretch()
        bottom_row.addWidget(outcome, 1)

        insights_col = QVBoxLayout()
        insights_col.setSpacing(12)
        ititle = QLabel("ANALYTICS INSIGHTS")
        ititle.setObjectName("SectionTitle")
        insights_col.addWidget(ititle)
        insights_col.addWidget(InsightCard("Force profile 22% below cohort mean",
                                            "Consistent gentle handling during dissection phase.", "#0095FF"))
        insights_col.addWidget(InsightCard("Phase efficiency in 84th percentile",
                                            "Dissect step finished 3.2 min faster than average.", "#20C997"))
        insights_col.addWidget(InsightCard("J3 approached 63% of limit",
                                            "Consider trocar repositioning earlier in next case.", "#F4B740"))
        insights_col.addWidget(InsightCard("Vitals remained stable throughout",
                                            "No HR/SpO2 excursions outside guard bands.", "#20C997"))
        insights_wrap = QWidget()
        insights_wrap.setLayout(insights_col)
        bottom_row.addWidget(insights_wrap, 1)

        outer.addLayout(bottom_row, 1)
