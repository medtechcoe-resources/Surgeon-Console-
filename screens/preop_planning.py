"""
Pre-Operation tab — MRI/CT scan viewers with load buttons, registration, segmentation, volume statistics.
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
                             QFrame, QSlider, QProgressBar, QSizePolicy, QPushButton,
                             QFileDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QRadialGradient, QPen
from widgets.card import MetricCard, PanelFrame


class ScanViewport(QFrame):
    """Axial slice viewer with load button and simulated scan display."""

    def __init__(self, modality, info):
        super().__init__()
        self.setObjectName("Card")
        self.setMinimumHeight(420)
        self.modality = modality
        self.info = info
        self._loaded = True

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QHBoxLayout()
        header.setContentsMargins(20, 14, 20, 10)
        title = QLabel(modality)
        title.setStyleSheet("color:#F5F7FA; font-size:16px; font-weight:600; letter-spacing:0.5px;")
        meta = QLabel(info)
        meta.setStyleSheet("color:#6B7B8D; font-size:12px;")
        header.addWidget(title)
        header.addStretch()
        header.addWidget(meta)
        outer.addLayout(header)

        self.canvas = _SliceCanvas()
        outer.addWidget(self.canvas, 1)

        slice_row = QHBoxLayout()
        slice_row.setContentsMargins(20, 10, 20, 14)
        lab = QLabel("SLICE")
        lab.setObjectName("FieldLabel")
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(0, 154)
        slider.setValue(96)
        self.count_label = QLabel("96 / 154")
        self.count_label.setObjectName("FieldValueBold")
        slider.valueChanged.connect(lambda v: self.count_label.setText(f"{v} / 154"))
        slice_row.addWidget(lab)
        slice_row.addWidget(slider, 1)
        slice_row.addWidget(self.count_label)
        outer.addLayout(slice_row)


class _SliceCanvas(QFrame):
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor("#0D1117"))

        cx, cy, r = w / 2, h / 2, min(w, h) * 0.34
        grad = QRadialGradient(cx, cy, r)
        grad.setColorAt(0.0, QColor(20, 60, 56))
        grad.setColorAt(0.8, QColor(10, 30, 28))
        grad.setColorAt(1.0, QColor(13, 17, 23))
        p.setBrush(grad)
        p.setPen(QPen(QColor("#20C997"), 2))
        p.drawEllipse(int(cx - r), int(cy - r), int(2 * r), int(2 * r))

        p.setBrush(QColor(200, 70, 60, 200))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(int(cx - 14), int(cy - 14), 28, 28)

        p.setPen(QColor("#6B7B8D"))
        from PyQt6.QtGui import QFont
        p.setFont(QFont("Inter", 10))
        p.drawText(12, 22, "A")
        p.drawText(12, h - 12, "P")
        p.drawText(w - 22, 22, "L")
        p.drawText(12, int(cy), "R")
        p.end()


class RegSegPanel(QFrame):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        # Registration Status
        reg = PanelFrame("Registration Status")
        for lab, val, color in [("Mode", "Rigid + B-Spline", "#E6EDF3"),
                                 ("RMS Error", "0.42 mm", "#20C997"),
                                 ("Iterations", "184", "#E6EDF3"),
                                 ("Confidence", "98.1%", "#20C997")]:
            row = QHBoxLayout()
            l = QLabel(lab)
            l.setObjectName("FieldLabel")
            v = QLabel(val)
            v.setStyleSheet(f"color:{color}; font-size:14px; font-weight:700;")
            row.addWidget(l)
            row.addStretch()
            row.addWidget(v)
            reg.add_layout(row)
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(98)
        bar.setTextVisible(False)
        bar.setFixedHeight(6)
        reg.add_widget(bar)
        layout.addWidget(reg)

        # Segmentation Status
        seg = PanelFrame("Segmentation Status")
        for lab, val, color in [("Organ", "Gallbladder + Bile Duct", "#F5F7FA"),
                                 ("Model", "nnU-Net v2.3", "#E6EDF3"),
                                 ("Dice Score", "0.937", "#20C997"),
                                 ("Voxels", "1.4 M", "#E6EDF3")]:
            row = QHBoxLayout()
            l = QLabel(lab)
            l.setObjectName("FieldLabel")
            v = QLabel(val)
            v.setStyleSheet(f"color:{color}; font-size:14px; font-weight:700;")
            v.setWordWrap(True)
            row.addWidget(l)
            row.addStretch()
            row.addWidget(v)
            seg.add_layout(row)
        bar2 = QProgressBar()
        bar2.setRange(0, 100)
        bar2.setValue(94)
        bar2.setTextVisible(False)
        bar2.setFixedHeight(6)
        seg.add_widget(bar2)
        layout.addWidget(seg)

        # Volume Statistics
        vol = PanelFrame("Volume Statistics")
        for lab, val, color in [("Total Volume", "48.2 cm\u00B3", "#F5F7FA"),
                                 ("Lesion Volume", "1.8 cm\u00B3", "#E5484D"),
                                 ("Min Density", "-120 HU", "#E6EDF3"),
                                 ("Max Density", "+240 HU", "#E6EDF3"),
                                 ("Mean HU", "+62", "#E6EDF3")]:
            row = QHBoxLayout()
            l = QLabel(lab)
            l.setObjectName("FieldLabel")
            v = QLabel(val)
            v.setStyleSheet(f"color:{color}; font-size:14px; font-weight:700;")
            row.addWidget(l)
            row.addStretch()
            row.addWidget(v)
            vol.add_layout(row)
        layout.addWidget(vol)

        layout.addStretch()


class PreopPlanningScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 14, 0, 0)
        outer.setSpacing(16)

        center = QVBoxLayout()
        center.setSpacing(14)

        # Load buttons row
        load_row = QHBoxLayout()
        load_row.setSpacing(12)
        btn_mri = QPushButton("Load MRI Scan")
        btn_mri.setProperty("class", "PrimaryButton")
        btn_mri.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_mri.clicked.connect(lambda: self._load_image("MRI"))
        btn_ct = QPushButton("Load CT Scan")
        btn_ct.setProperty("class", "PrimaryButton")
        btn_ct.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ct.clicked.connect(lambda: self._load_image("CT"))
        load_row.addWidget(btn_mri)
        load_row.addWidget(btn_ct)
        load_row.addStretch()
        center.addLayout(load_row)

        views = QHBoxLayout()
        views.setSpacing(14)
        views.addWidget(ScanViewport("AXIAL  ·  MRI", "LOADED  512x512  ·  16B"))
        views.addWidget(ScanViewport("AXIAL  ·  CT", "LOADED  512x512  ·  16B"))
        center.addLayout(views, 1)

        bottom_cards = QHBoxLayout()
        bottom_cards.setSpacing(12)
        bottom_cards.addWidget(MetricCard("Slices Loaded", "308", sub="MRI 154  ·  CT 154"))
        bottom_cards.addWidget(MetricCard("Voxel Size", "0.5", "mm", "Iso 0.5x0.5x1.0"))
        bottom_cards.addWidget(MetricCard("Fusion Overlap", "96.4", "%", "A/P  ·  L/R aligned", accent="cyan"))
        bottom_cards.addWidget(MetricCard("Landmarks", "12 / 12", sub="All paired"))
        bottom_cards.addWidget(MetricCard("ROI Defined", "3", sub="2 critical, 1 caution", accent="amber"))
        bottom_cards.addWidget(MetricCard("Plan Status", "APPROVED", sub="Voss  ·  07:51 UTC", accent="green", value_color="#20C997"))
        center.addLayout(bottom_cards)

        outer.addLayout(center, 7)
        outer.addWidget(RegSegPanel(), 3)

    def _load_image(self, modality):
        path, _ = QFileDialog.getOpenFileName(
            self, f"Load {modality} Image", "",
            "Medical Images (*.dcm *.nii *.nii.gz *.mha *.nrrd);;Image Files (*.png *.jpg *.bmp);;All Files (*)"
        )
        if path:
            pass  # Integration point for DICOM loading
