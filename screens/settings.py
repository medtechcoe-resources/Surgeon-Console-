"""
Settings tab — Application settings, YOLO configuration, network, etc.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QComboBox, QSlider
from PyQt6.QtCore import Qt
from widgets.card import PanelFrame

def setting_row(label, widget):
    row = QHBoxLayout()
    row.setContentsMargins(0, 8, 0, 8)
    l = QLabel(label)
    l.setObjectName("FieldLabel")
    l.setFixedWidth(200)
    row.addWidget(l)
    from PyQt6.QtWidgets import QLayout
    if isinstance(widget, QLayout):
        row.addLayout(widget)
    else:
        row.addWidget(widget)
    row.addStretch()
    return row

class SettingsScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 14, 0, 0)
        outer.setSpacing(16)

        left = QVBoxLayout()
        left.setSpacing(14)
        
        display = PanelFrame("Display & Interface")
        
        theme_combo = QComboBox()
        theme_combo.addItems(["Dark (Default)", "Light"])
        theme_combo.setFixedWidth(200)
        theme_combo.setStyleSheet("background-color:#1C2333; color:#E6EDF3; border:1px solid #2D3748; padding:6px; border-radius:4px;")
        display.add_layout(setting_row("Application Theme", theme_combo))
        
        res_combo = QComboBox()
        res_combo.addItems(["3440 x 1440 (Native)", "2560 x 1440", "1920 x 1080"])
        res_combo.setFixedWidth(200)
        res_combo.setStyleSheet("background-color:#1C2333; color:#E6EDF3; border:1px solid #2D3748; padding:6px; border-radius:4px;")
        display.add_layout(setting_row("Default Resolution", res_combo))
        
        display.add_stretch()
        left.addWidget(display)

        vision = PanelFrame("Vision & YOLO Pipeline")
        
        model_combo = QComboBox()
        model_combo.addItems(["yolov8x.pt (High Accuracy)", "yolov8m.pt (Balanced)", "yolov8n.pt (Fastest)"])
        model_combo.setFixedWidth(250)
        model_combo.setStyleSheet("background-color:#1C2333; color:#E6EDF3; border:1px solid #2D3748; padding:6px; border-radius:4px;")
        vision.add_layout(setting_row("Detection Model", model_combo))
        
        conf_slider = QSlider(Qt.Orientation.Horizontal)
        conf_slider.setRange(10, 95)
        conf_slider.setValue(70)
        conf_slider.setFixedWidth(200)
        conf_val = QLabel("70%")
        conf_val.setStyleSheet("color:#F5F7FA; font-size:14px; margin-left:12px;")
        conf_slider.valueChanged.connect(lambda v: conf_val.setText(f"{v}%"))
        
        conf_row = QHBoxLayout()
        conf_row.addWidget(conf_slider)
        conf_row.addWidget(conf_val)
        
        vision.add_layout(setting_row("Confidence Threshold", conf_row))
        
        hw_combo = QComboBox()
        hw_combo.addItems(["Auto (TensorRT > CUDA > CPU)", "CUDA Only", "CPU Only"])
        hw_combo.setFixedWidth(250)
        hw_combo.setStyleSheet("background-color:#1C2333; color:#E6EDF3; border:1px solid #2D3748; padding:6px; border-radius:4px;")
        vision.add_layout(setting_row("Hardware Acceleration", hw_combo))
        
        vision.add_stretch()
        left.addWidget(vision)
        
        outer.addLayout(left, 1)
        
        right = QVBoxLayout()
        right.setSpacing(14)
        
        network = PanelFrame("Network & Communication")
        
        pacs_btn = QPushButton("Configure PACS Server")
        pacs_btn.setProperty("class", "SecondaryButton")
        pacs_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        network.add_layout(setting_row("DICOM Integration", pacs_btn))
        
        stream_combo = QComboBox()
        stream_combo.addItems(["H.265 (High Efficiency)", "H.264 (Maximum Compatibility)", "Uncompressed (Diagnostics)"])
        stream_combo.setFixedWidth(250)
        stream_combo.setStyleSheet("background-color:#1C2333; color:#E6EDF3; border:1px solid #2D3748; padding:6px; border-radius:4px;")
        network.add_layout(setting_row("Stream Codec", stream_combo))
        
        network.add_stretch()
        right.addWidget(network)
        
        system = PanelFrame("System Maintenance")
        
        calib_btn = QPushButton("Run Full Calibration")
        calib_btn.setProperty("class", "PrimaryButton")
        calib_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        system.add_layout(setting_row("Kinematics", calib_btn))
        
        log_btn = QPushButton("Export System Logs")
        log_btn.setProperty("class", "SecondaryButton")
        log_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        system.add_layout(setting_row("Diagnostics", log_btn))
        
        reset_btn = QPushButton("Factory Reset")
        reset_btn.setProperty("class", "DangerButton")
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        system.add_layout(setting_row("Danger Zone", reset_btn))
        
        system.add_stretch()
        right.addWidget(system)
        
        outer.addLayout(right, 1)
