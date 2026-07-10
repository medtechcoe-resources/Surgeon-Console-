# ═══════════════════════════════════════════════════════════════════
#  ROBOT CONSOLE — ALERTS TAB
#  Displays generated robot alerts in a scrollable table with
#  severity colour-coding and filtering.
# ═══════════════════════════════════════════════════════════════════

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QFrame,
)

from constants import C
from ui.widgets import CardFrame, SectionHeader, StatusBadge
from models.data_models import AlertEntry


class AlertsTab(QWidget):
    """Alerts tab — displays a table of robot-generated alerts
    with timestamp, severity, source, and message columns."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {C['bg0']};")
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(10)

        # ── Header Row ────────────────────────────────────────────
        header_layout = QHBoxLayout()

        title = QLabel("SYSTEM ALERTS & SAFETY LOG")
        title.setFont(QFont("Consolas", 30, QFont.Weight.Bold))
        title.setStyleSheet(
            f"color: {C['txt0']}; background-color: {C['bg0']};")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Alert count badge
        self._alert_badge = StatusBadge("0 ALERTS", C["txt2"])
        header_layout.addWidget(self._alert_badge)

        main_layout.addLayout(header_layout)

        # ── Severity Legend ───────────────────────────────────────
        legend_layout = QHBoxLayout()
        for label, color in [("CRITICAL", C["red"]),
                              ("WARNING", C["amber"]),
                              ("INFO", C["cyan"])]:
            badge = QPushButton(label)
            badge.setFont(QFont("Consolas", 16, QFont.Weight.Bold))
            badge.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    padding: 6px 14px;
                    border: none;
                }}
            """)
            badge.setCursor(Qt.CursorShape.PointingHandCursor)
            legend_layout.addWidget(badge)

        legend_layout.addStretch()

        # Clear button
        clear_btn = QPushButton("✔  CLEAR ALL")
        clear_btn.setFont(QFont("Consolas", 20, QFont.Weight.Bold))
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {C['green']};
                color: white;
                padding: 12px 20px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {C['teal']};
            }}
        """)
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self._clear_alerts)
        legend_layout.addWidget(clear_btn)

        main_layout.addLayout(legend_layout)

        # ── Alerts Table ──────────────────────────────────────────
        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(
            ["TIMESTAMP", "SEVERITY", "SOURCE", "MESSAGE"])
        self._table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet(f"""
            QTableWidget {{
                alternate-background-color: {C['bg1']};
            }}
        """)

        main_layout.addWidget(self._table, stretch=1)

        # ── Summary Footer ────────────────────────────────────────
        footer = CardFrame()
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(12, 8, 12, 8)

        self._summary_labels = {}
        for sev, color in [("CRITICAL", C["red"]),
                            ("WARNING", C["amber"]),
                            ("INFO", C["cyan"])]:
            lbl = QLabel(f"{sev}: 0")
            lbl.setFont(QFont("Consolas", 18, QFont.Weight.Bold))
            lbl.setStyleSheet(f"color: {color}; border: none;")
            fl.addWidget(lbl)
            fl.addSpacing(30)
            self._summary_labels[sev] = lbl

        fl.addStretch()

        self._total_label = QLabel("TOTAL: 0")
        self._total_label.setFont(
            QFont("Consolas", 18, QFont.Weight.Bold))
        self._total_label.setStyleSheet(
            f"color: {C['txt0']}; border: none;")
        fl.addWidget(self._total_label)

        main_layout.addWidget(footer)

    # ─── Public Methods ───────────────────────────────────────────

    def add_alert(self, alert: AlertEntry):
        """Add a new alert entry to the table."""
        sev_colors = {
            "CRITICAL": C["red"],
            "WARNING": C["amber"],
            "INFO": C["cyan"],
        }
        sev_bg = {
            "CRITICAL": C["red_bg"],
            "WARNING": C["amber_bg"],
            "INFO": C["cyan_bg"],
        }

        color = sev_colors.get(alert.severity, C["cyan"])
        bg = sev_bg.get(alert.severity, C["cyan_bg"])

        row = 0  # Insert at top
        self._table.insertRow(row)

        # Timestamp
        ts_item = QTableWidgetItem(alert.timestamp)
        ts_item.setForeground(QColor(C["txt2"]))
        ts_item.setBackground(QColor(bg))
        self._table.setItem(row, 0, ts_item)

        # Severity
        sev_item = QTableWidgetItem(alert.severity)
        sev_item.setForeground(QColor(color))
        sev_item.setBackground(QColor(bg))
        sev_item.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
        self._table.setItem(row, 1, sev_item)

        # Source
        src_item = QTableWidgetItem(alert.source)
        src_item.setForeground(QColor(C["txt1"]))
        src_item.setBackground(QColor(bg))
        self._table.setItem(row, 2, src_item)

        # Message
        msg_item = QTableWidgetItem(alert.message)
        msg_item.setForeground(QColor(C["txt0"]))
        msg_item.setBackground(QColor(bg))
        self._table.setItem(row, 3, msg_item)

        # Update summary counts
        self._update_summary()

        # Keep max 200 rows
        while self._table.rowCount() > 200:
            self._table.removeRow(self._table.rowCount() - 1)

    def _clear_alerts(self):
        """Clear all alerts from the table."""
        self._table.setRowCount(0)
        self._update_summary()

    def _update_summary(self):
        """Update the summary footer with alert counts."""
        counts = {"CRITICAL": 0, "WARNING": 0, "INFO": 0}
        total = self._table.rowCount()

        for row in range(total):
            item = self._table.item(row, 1)
            if item:
                sev = item.text()
                if sev in counts:
                    counts[sev] += 1

        for sev, count in counts.items():
            if sev in self._summary_labels:
                self._summary_labels[sev].setText(f"{sev}: {count}")

        self._total_label.setText(f"TOTAL: {total}")

        # Update badge
        if counts["CRITICAL"] > 0:
            self._alert_badge.set_text_and_color(
                f"{total} ALERTS", C["red"])
        elif counts["WARNING"] > 0:
            self._alert_badge.set_text_and_color(
                f"{total} ALERTS", C["amber"])
        elif total > 0:
            self._alert_badge.set_text_and_color(
                f"{total} ALERTS", C["cyan"])
        else:
            self._alert_badge.set_text_and_color(
                "NO ALERTS", C["green"])
