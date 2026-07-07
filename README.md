# AETHER \u00B7 SURGICAL — Robotic Console (PyQt6)

A pixel-faithful PyQt6 reimplementation of the AETHER Surgical Console reference UI.
Five screens are implemented as **separate, independent modules** (not a single
monolithic copy), sharing common chrome (header, nav tabs, patient sidebar,
status bar, floating emergency-stop).

## Run it

```bash
pip install PyQt6
python3 main.py
```

## Project layout

```
aether_console/
├── main.py                     # App entry point — assembles header/nav/sidebar/screens/status bar
├── styles/
│   └── theme.qss                # Dark medical-grade QSS theme (colors, cards, buttons, sliders…)
├── widgets/                     # Shared chrome, reused across every screen
│   ├── header.py                 # Brand, local/UTC clock, system status, theme toggle
│   ├── nav_tabs.py               # 5-tab navigation bar
│   ├── patient_sidebar.py        # Left "Patient Information" + "Procedure Information" cards
│   ├── status_bar.py             # Bottom telemetry strip
│   ├── card.py                   # Reusable MetricCard + PanelFrame primitives
│   └── estop.py                  # Always-visible floating Emergency Stop button
└── screens/                     # Each screen is its own file/class — built independently
    ├── preop_planning.py         # Pre-Operative Planning  (MRI/CT viewers, registration, segmentation)
    ├── live_video.py             # Live Video              (endoscopic feed, YOLO overlays, pipeline controls)
    ├── live_control.py           # Live Control            (manipulator telemetry, joint limits, system health)
    ├── end_effector.py           # End-Effector Camera     (tool tip view, world coordinates, tool status)
    └── postop_analytics.py       # Post-Operative Analytics (charts, summary, outcome metrics, insights)
```

## Notes for further development

- All visuals (scan viewports, the endoscopic feed gradient, the tool-tip
  sketch, and the analytics charts) are drawn with `QPainter` directly onto
  `QFrame` subclasses — no external image assets are required, and these are
  trivial to swap for real `QOpenGLWidget`/`OpenCV` video frames or live
  `QChart`/pyqtgraph plots later.
- Every metric card, panel, table, and progress bar is themed purely through
  the QSS file (`styles/theme.qss`) using Qt dynamic properties
  (`accent="cyan"`, `level="caution"`, `active="true"`, etc.) — no inline
  styling is required to re-skin the app (e.g. for a Light theme).
- The `EmergencyStopButton` is parented to the content area and re-centers
  itself on resize, so it always floats top-center above the live content,
  independent of which screen is active.
- Each screen file constructs its widgets with stretch factors balanced for
  a 1920\u00D71080+ ultra-wide display, and the whole window opens maximized.
