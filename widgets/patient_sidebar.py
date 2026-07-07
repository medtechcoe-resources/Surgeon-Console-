from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                             QSizePolicy, QProgressBar, QGridLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor


def hline():
    f = QFrame()
    f.setObjectName("HLine")
    f.setFrameShape(QFrame.Shape.HLine)
    return f


def field_row(label, value, bold=False, warn=False):
    row = QHBoxLayout()
    row.setContentsMargins(0, 0, 0, 0)
    lbl = QLabel(label)
    lbl.setObjectName("FieldLabel")
    val = QLabel(value)
    val.setObjectName("FieldValueWarn" if warn else ("FieldValueBold" if bold else "FieldValue"))
    val.setAlignment(Qt.AlignmentFlag.AlignRight)
    row.addWidget(lbl)
    row.addStretch()
    row.addWidget(val)
    return row


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


class SidebarCard(QFrame):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setObjectName("SidebarCard")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(18, 16, 18, 16)
        self.layout.setSpacing(10)
        t = QLabel(title.upper())
        t.setObjectName("SidebarCardTitle")
        self.layout.addWidget(t)

    def add_row(self, label, value, bold=False, warn=False):
        self.layout.addLayout(field_row(label, value, bold, warn))

    def add_widget(self, w):
        self.layout.addWidget(w)


class PatientSidebar(QWidget):
    """Left sidebar: Patient Information + Procedure Information + Safety + Vitals."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(300)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 16, 0, 16)
        layout.setSpacing(12)

        # --- Patient Information card ---
        patient_card = SidebarCard("Patient Information")
        header = QHBoxLayout()
        avatar = QLabel("MK")
        avatar.setObjectName("PatientAvatar")
        avatar.setFixedSize(48, 48)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(avatar)
        name_box = QVBoxLayout()
        name_box.setSpacing(3)
        name = QLabel("Marisa K\u00F6hler")
        name.setObjectName("PatientName")
        meta = QLabel("MRN  ·  0048-23119")
        meta.setObjectName("PatientMeta")
        name_box.addWidget(name)
        name_box.addWidget(meta)
        header.addLayout(name_box)
        header.addStretch()
        patient_card.layout.addLayout(header)
        patient_card.layout.addWidget(hline())
        patient_card.add_row("Age / Sex", "58  ·  F")
        patient_card.add_row("Weight", "64.2 kg")
        patient_card.add_row("Blood", "O+")
        patient_card.add_row("Allergies", "Penicillin", warn=True)
        layout.addWidget(patient_card)

        # --- Procedure Information card ---
        proc_card = SidebarCard("Procedure Information")
        type_row = QVBoxLayout()
        type_row.setSpacing(3)
        type_lbl = QLabel("Type")
        type_lbl.setObjectName("FieldLabel")
        type_val = QLabel("Laparoscopic Cholecystectomy")
        type_val.setObjectName("FieldValueBold")
        type_val.setWordWrap(True)
        type_row.addWidget(type_lbl)
        type_row.addWidget(type_val)
        proc_card.layout.addLayout(type_row)
        proc_card.layout.addWidget(hline())
        proc_card.add_row("Code", "ICD-10 K80.20")
        proc_card.add_row("Surgeon", "Dr. A. Voss", bold=True)
        proc_card.add_row("Assist", "Dr. R. Iyer", bold=True)
        proc_card.add_row("OR", "Suite 03")
        proc_card.add_row("Start", "08:42 UTC")
        proc_card.layout.addWidget(hline())

        phase_lbl = QLabel("PHASE")
        phase_lbl.setObjectName("SidebarCardTitle")
        proc_card.layout.addWidget(phase_lbl)
        phase_row = QHBoxLayout()
        phase_name = QLabel("Dissection")
        phase_name.setObjectName("FieldValueBold")
        phase_step = QLabel("Step 4 / 7")
        phase_step.setObjectName("FieldLabel")
        phase_row.addWidget(phase_name)
        phase_row.addStretch()
        phase_row.addWidget(phase_step)
        proc_card.layout.addLayout(phase_row)

        progress = QProgressBar()
        progress.setRange(0, 7)
        progress.setValue(4)
        progress.setTextVisible(False)
        progress.setFixedHeight(6)
        proc_card.layout.addWidget(progress)
        layout.addWidget(proc_card)

        # --- Safety Information card ---
        safety_card = SidebarCard("Safety Information")
        safety_items = [
            ("E-Stop Armed", "READY", "#20C997"),
            ("Force Limit", "NOMINAL", "#20C997"),
            ("Workspace", "IN BOUNDS", "#20C997"),
            ("Sterility", "VERIFIED", "#20C997"),
            ("Fault Counter", "0", "#F5F7FA"),
        ]
        for label, value, color in safety_items:
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            lbl = QLabel(label)
            lbl.setObjectName("FieldLabel")
            val_row = QHBoxLayout()
            val_row.setSpacing(6)
            if color == "#20C997":
                dot = _StatusDot(color)
                val_row.addWidget(dot)
            val = QLabel(value)
            # Use object name for theme-aware coloring
            if color == "#20C997":
                val.setObjectName("StatusGood")
            elif color == "#F5F7FA":
                val.setObjectName("FieldValueBold")
            else:
                val.setObjectName("StatusWarn")
            val.setAlignment(Qt.AlignmentFlag.AlignRight)
            val_row.addWidget(val)
            row.addWidget(lbl)
            row.addStretch()
            row.addLayout(val_row)
            safety_card.layout.addLayout(row)
        layout.addWidget(safety_card)

        # --- Vitals card ---
        vitals_card = SidebarCard("Vitals")
        vitals_grid = QGridLayout()
        vitals_grid.setSpacing(8)
        vitals_data = [
            ("HR", "74", "bpm", 0, 0),
            ("SpO2", "98", "%", 0, 1),
            ("BP", "118/74", "mmHg", 1, 0),
            ("Temp", "36.8", "\u00B0C", 1, 1),
        ]
        for label, value, unit, row_idx, col_idx in vitals_data:
            cell = QVBoxLayout()
            cell.setSpacing(2)
            lab = QLabel(label)
            lab.setObjectName("VitalLabel")
            val = QLabel(value)
            val.setObjectName("VitalValue")
            un = QLabel(unit)
            un.setObjectName("VitalUnit")
            cell.addWidget(lab)
            val_row = QHBoxLayout()
            val_row.setSpacing(4)
            val_row.addWidget(val)
            val_row.addWidget(un, alignment=Qt.AlignmentFlag.AlignBottom)
            val_row.addStretch()
            cell.addLayout(val_row)
            vitals_grid.addLayout(cell, row_idx, col_idx)
        vitals_card.layout.addLayout(vitals_grid)
        layout.addWidget(vitals_card)

        layout.addStretch()
