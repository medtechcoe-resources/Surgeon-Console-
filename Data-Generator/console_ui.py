# ═══════════════════════════════════════════════════════════════════
#  DATA GENERATOR — TERMINAL CONSOLE UI
#  Renders a live ANSI-formatted dashboard to stdout.
#  Updates every 500 ms via a QTimer so it shares the Qt event loop.
#  Keyboard input (Q / P) is handled via a non-blocking stdin thread.
# ═══════════════════════════════════════════════════════════════════

import sys
import os
import threading
import time
from datetime import datetime, timedelta

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

# ── ANSI colour helpers ───────────────────────────────────────────

RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"

# Foreground
FG_WHITE   = "\033[97m"
FG_CYAN    = "\033[96m"
FG_GREEN   = "\033[92m"
FG_YELLOW  = "\033[93m"
FG_RED     = "\033[91m"
FG_MAGENTA = "\033[95m"
FG_BLUE    = "\033[94m"
FG_GRAY    = "\033[90m"

# Background
BG_BLACK   = "\033[40m"
BG_BLUE    = "\033[44m"
BG_DARK    = "\033[48;5;234m"

def _c(text: str, *codes: str) -> str:
    """Wrap text in ANSI codes, resetting afterwards."""
    return "".join(codes) + str(text) + RESET

def _pad(text: str, width: int, fill: str = " ") -> str:
    """Left-align text padded to *width* visible characters (ignores ANSI)."""
    visible = _strip_ansi(text)
    pad_needed = max(0, width - len(visible))
    return text + fill * pad_needed

def _strip_ansi(s: str) -> str:
    """Remove ANSI escape sequences to compute visible length."""
    import re
    return re.sub(r"\033\[[0-9;]*m", "", s)

def _rpad(text: str, width: int, fill: str = " ") -> str:
    """Right-align text padded to *width* visible characters."""
    visible = _strip_ansi(text)
    pad_needed = max(0, width - len(visible))
    return fill * pad_needed + text

# ── Terminal helpers ──────────────────────────────────────────────

def _clear():
    """Clear the terminal screen."""
    if sys.platform == "win32":
        os.system("cls")
    else:
        os.system("clear")

def _move_home():
    """Move cursor to top-left without clearing (flicker-free)."""
    sys.stdout.write("\033[H")
    sys.stdout.flush()

def _hide_cursor():
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()

def _show_cursor():
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()


# ═══════════════════════════════════════════════════════════════════
#  CONSOLE UI
# ═══════════════════════════════════════════════════════════════════

class ConsoleUI(QObject):
    """Renders a live terminal dashboard and emits user commands.

    Signals
    -------
    quit_requested      User pressed Q.
    pause_requested     User pressed P (toggle).
    """

    quit_requested  = pyqtSignal()
    pause_requested = pyqtSignal()

    # Refresh rate
    REFRESH_MS = 500

    def __init__(self, publisher, parent=None):
        super().__init__(parent)
        self._pub = publisher
        self._start_time = datetime.now()
        self._last_publish_times: dict[str, str] = {}
        self._recent_events: list[str] = []
        self._paused = False
        self._frame = 0

        # ── Render timer ──────────────────────────────────────────
        self._timer = QTimer(self)
        self._timer.setInterval(self.REFRESH_MS)
        self._timer.timeout.connect(self._render)

        # ── Wire publisher signals ────────────────────────────────
        publisher.connected.connect(self._on_connected)
        publisher.disconnected.connect(self._on_disconnected)
        publisher.error_occurred.connect(self._on_error)
        publisher.log_message.connect(self._on_log)
        publisher.published.connect(self._on_published)

        # ── Keyboard input thread (non-blocking) ──────────────────
        self._input_thread = threading.Thread(
            target=self._keyboard_loop, daemon=True
        )
        self._conn_status = "CONNECTING…"
        self._conn_color  = FG_YELLOW

    # ── Public API ────────────────────────────────────────────────

    def start(self):
        """Start the UI render loop."""
        _hide_cursor()
        _clear()
        self._timer.start()
        self._input_thread.start()

    def stop(self):
        """Stop the UI render loop and restore terminal."""
        self._timer.stop()
        _show_cursor()
        print()

    def notify_paused(self, paused: bool):
        """Called by main when pause state changes."""
        self._paused = paused

    # ── Signal handlers ───────────────────────────────────────────

    def _on_connected(self):
        self._conn_status = "CONNECTED"
        self._conn_color  = FG_GREEN
        self._add_event(_c("● Broker connection established", FG_GREEN, BOLD))

    def _on_disconnected(self):
        self._conn_status = "DISCONNECTED"
        self._conn_color  = FG_RED
        self._add_event(_c("● Broker connection lost — reconnecting…", FG_RED))

    def _on_error(self, msg: str):
        self._add_event(_c(f"✖ ERROR: {msg}", FG_RED))

    def _on_log(self, level: str, message: str):
        color = FG_CYAN if level == "INFO" else FG_YELLOW if level == "WARNING" else FG_RED
        self._add_event(_c(f"[{level}] {message}", color))

    def _on_published(self, topic: str, payload: dict):
        ts = datetime.now().strftime("%H:%M:%S")
        self._last_publish_times[topic] = ts

    def _add_event(self, msg: str):
        ts = _c(datetime.now().strftime("%H:%M:%S"), FG_GRAY)
        self._recent_events.insert(0, f"{ts}  {msg}")
        self._recent_events = self._recent_events[:12]

    # ── Render ────────────────────────────────────────────────────

    def _render(self):
        """Render one frame to the terminal."""
        self._frame += 1
        lines = self._build_frame()
        _move_home()
        sys.stdout.write("\n".join(lines) + "\n")
        sys.stdout.flush()

    def _build_frame(self) -> list[str]:
        W = 78   # total dashboard width
        pub = self._pub
        now = datetime.now()
        uptime = str(timedelta(seconds=int((now - self._start_time).total_seconds())))

        # Spinner
        spinner = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"[self._frame % 10]

        lines: list[str] = []

        # ── Top border ────────────────────────────────────────────
        lines.append(_c("╔" + "═" * (W - 2) + "╗", FG_CYAN, BOLD))

        # Title bar
        title = "  AETHER  //  DATA GENERATOR BACKEND"
        version = "v4.2  "
        mid_space = " " * (W - 2 - len(title) - len(version))
        lines.append(
            _c("║", FG_CYAN, BOLD)
            + _c(title, FG_WHITE, BOLD)
            + mid_space
            + _c(version, FG_GRAY)
            + _c("║", FG_CYAN, BOLD)
        )
        lines.append(_c("╠" + "═" * (W - 2) + "╣", FG_CYAN, BOLD))

        # ── Status row ────────────────────────────────────────────
        conn_indicator = _c(f" ● {self._conn_status} ", self._conn_color, BOLD)
        host_str = _c(f" {pub.host}:{pub.port}", FG_GRAY)
        pause_str = (_c("  ⏸  PAUSED  ", FG_YELLOW, BOLD)
                     if self._paused else _c("  ▶  RUNNING  ", FG_GREEN, BOLD))
        spin_str = _c(f" {spinner}", FG_CYAN)
        time_str = _c(now.strftime("  %H:%M:%S"), FG_GRAY)
        uptime_str = _c(f"  UP {uptime}", FG_GRAY)

        status_left  = f"║{conn_indicator}{host_str}{pause_str}"
        status_right = f"{spin_str}{time_str}{uptime_str} ║"
        gap = W - len(_strip_ansi(status_left)) - len(_strip_ansi(status_right))
        lines.append(status_left + " " * max(0, gap) + status_right)
        lines.append(_c("╠" + "═" * (W - 2) + "╣", FG_CYAN, BOLD))

        # ── Generator stats table header ──────────────────────────
        lines.append(
            _c("║", FG_CYAN, BOLD)
            + _c("  GENERATOR          STATUS    INTERVAL   SENT       LAST PUBLISH      ", FG_MAGENTA, BOLD)
            + _c("║", FG_CYAN, BOLD)
        )
        lines.append(_c("╠" + "─" * (W - 2) + "╣", FG_CYAN))

        # ── Per-generator rows ────────────────────────────────────
        gen_rows = [
            (
                "patient_vitals",
                "Patient Vitals",
                pub.vitals_gen,
                "1 000 ms",
            ),
            (
                "robot_telemetry",
                "Robot Telemetry",
                pub.telemetry_gen,
                "  600 ms",
            ),
            (
                "alerts",
                "Alert System",
                pub.alert_gen,
                "60 000 ms",
            ),
        ]

        for topic, label, gen, interval in gen_rows:
            status = (_c("▶ ACTIVE ", FG_GREEN, BOLD)
                      if gen.is_running else _c("⏸ PAUSED ", FG_YELLOW))
            sent   = _rpad(_c(str(gen.message_count), FG_WHITE, BOLD), 12)
            last   = _c(self._last_publish_times.get(topic, "---"), FG_GRAY)
            lbl    = _pad(_c(f"  {label}", FG_CYAN), 22)
            intv   = _pad(_c(interval, FG_GRAY), 12)

            row_left  = f"║{lbl}{status}  {intv}{sent}  {last}"
            gap = W - len(_strip_ansi(row_left)) - 1
            lines.append(row_left + " " * max(0, gap) + _c("║", FG_CYAN, BOLD))

        lines.append(_c("╠" + "═" * (W - 2) + "╣", FG_CYAN, BOLD))

        # ── Live data preview ─────────────────────────────────────
        lines.append(
            _c("║", FG_CYAN, BOLD)
            + _c("  LIVE DATA PREVIEW                                                      ", FG_MAGENTA, BOLD)
            + _c("║", FG_CYAN, BOLD)
        )
        lines.append(_c("╠" + "─" * (W - 2) + "╣", FG_CYAN))

        # Vitals preview
        v = pub.vitals_gen.latest
        if v:
            bp = v.get("blood_pressure", "---")
            vrow = (
                f"  {_c('VITALS', FG_GREEN, BOLD)}  "
                f"HR {_c(str(v.get('heart_rate','---')), FG_WHITE)} bpm  "
                f"SpO2 {_c(str(v.get('spo2','---')), FG_CYAN)}%  "
                f"BP {_c(bp, FG_MAGENTA)} mmHg  "
                f"RR {_c(str(int(v.get('respiration',0))), FG_YELLOW)} br/m  "
                f"T {_c(str(v.get('temperature','---')), FG_RED)}°C"
            )
        else:
            vrow = f"  {_c('VITALS', FG_GREEN, BOLD)}  {_c('Waiting for first frame…', FG_GRAY)}"
        vrow_left = f"║{vrow}"
        gap = W - len(_strip_ansi(vrow_left)) - 1
        lines.append(vrow_left + " " * max(0, gap) + _c("║", FG_CYAN, BOLD))

        # Telemetry preview (joint angles)
        t = pub.telemetry_gen.latest
        if t:
            ja = t.get("joint_angles", {})
            angle_strs = "  ".join(
                f"J{i+1}={_c(str(ja.get(f'j{i+1}',0.0)), FG_WHITE)}°"
                for i in range(6)
            )
            tp = t.get("tool_position", {})
            trow = (
                f"  {_c('TELEMET', FG_MAGENTA, BOLD)}  {angle_strs}"
            )
            trow2 = (
                f"           XYZ ({_c(str(tp.get('x',0.0)), FG_CYAN)}, "
                f"{_c(str(tp.get('y',0.0)), FG_CYAN)}, "
                f"{_c(str(tp.get('z',0.0)), FG_CYAN)}) mm  "
                f"State: {_c(t.get('motion_state','---'), FG_YELLOW)}"
            )
        else:
            trow  = f"  {_c('TELEMET', FG_MAGENTA, BOLD)}  {_c('Waiting for first frame…', FG_GRAY)}"
            trow2 = ""

        trow_left = f"║{trow}"
        gap = W - len(_strip_ansi(trow_left)) - 1
        lines.append(trow_left + " " * max(0, gap) + _c("║", FG_CYAN, BOLD))
        if trow2:
            trow2_left = f"║{trow2}"
            gap = W - len(_strip_ansi(trow2_left)) - 1
            lines.append(trow2_left + " " * max(0, gap) + _c("║", FG_CYAN, BOLD))

        # Alert preview
        a = pub.alert_gen.latest
        if a:
            sev_color = FG_RED if a["severity"] == "CRITICAL" else (
                FG_YELLOW if a["severity"] == "WARNING" else FG_CYAN)
            arow = (
                f"  {_c('ALERTS ', FG_RED, BOLD)}  "
                f"{_c(a['severity'], sev_color, BOLD)}  "
                f"{_c(a['source'], FG_GRAY)}  "
                f"{_c(a['message'], FG_WHITE)}  "
                f"[total: {_c(str(pub.alert_gen.message_count), FG_WHITE)}]"
            )
        else:
            arow = f"  {_c('ALERTS ', FG_RED, BOLD)}  {_c('No alerts yet', FG_GRAY)}"
        arow_left = f"║{arow}"
        gap = W - len(_strip_ansi(arow_left)) - 1
        lines.append(arow_left + " " * max(0, gap) + _c("║", FG_CYAN, BOLD))

        lines.append(_c("╠" + "═" * (W - 2) + "╣", FG_CYAN, BOLD))

        # ── Event log ─────────────────────────────────────────────
        lines.append(
            _c("║", FG_CYAN, BOLD)
            + _c("  SYSTEM EVENT LOG                                                       ", FG_MAGENTA, BOLD)
            + _c("║", FG_CYAN, BOLD)
        )
        lines.append(_c("╠" + "─" * (W - 2) + "╣", FG_CYAN))

        for i in range(5):
            if i < len(self._recent_events):
                entry = self._recent_events[i]
            else:
                entry = _c("  ---", FG_GRAY)
            row = f"║  {entry}"
            gap = W - len(_strip_ansi(row)) - 1
            lines.append(row + " " * max(0, gap) + _c("║", FG_CYAN, BOLD))

        lines.append(_c("╠" + "═" * (W - 2) + "╣", FG_CYAN, BOLD))

        # ── Network stats ─────────────────────────────────────────
        stats = pub.get_stats() if pub.is_connected else {}
        total_sent = (
            pub.vitals_gen.message_count +
            pub.telemetry_gen.message_count +
            pub.alert_gen.message_count
        )
        pkts_out  = _c(str(stats.get("packets_sent", 0)), FG_WHITE, BOLD)
        bytes_out = _c(f"{stats.get('bytes_sent', 0):,}", FG_WHITE)
        rate_out  = _c(f"{stats.get('data_rate_out', 0.0):.0f} B/s", FG_GREEN)
        errs      = _c(str(stats.get("errors", 0)), FG_RED if stats.get("errors", 0) else FG_GRAY)
        total_str = _c(str(total_sent), FG_CYAN, BOLD)

        stats_row = (
            f"║  Pkts Out: {pkts_out}   Bytes: {bytes_out}   "
            f"Rate: {rate_out}   Errors: {errs}   Total Published: {total_str}"
        )
        gap = W - len(_strip_ansi(stats_row)) - 1
        lines.append(stats_row + " " * max(0, gap) + _c("║", FG_CYAN, BOLD))

        lines.append(_c("╠" + "═" * (W - 2) + "╣", FG_CYAN, BOLD))

        # ── Help bar ──────────────────────────────────────────────
        help_text = (
            f"  {_c('[P]', FG_YELLOW, BOLD)} Pause/Resume    "
            f"{_c('[Q]', FG_RED, BOLD)} Quit"
        )
        help_row = f"║{help_text}"
        gap = W - len(_strip_ansi(help_row)) - 1
        lines.append(help_row + " " * max(0, gap) + _c("║", FG_CYAN, BOLD))

        lines.append(_c("╚" + "═" * (W - 2) + "╝", FG_CYAN, BOLD))

        return lines

    # ── Keyboard input loop (daemon thread) ───────────────────────

    def _keyboard_loop(self):
        """Blocking keyboard reader running in a daemon thread."""
        if sys.platform == "win32":
            self._keyboard_loop_win()
        else:
            self._keyboard_loop_unix()

    def _keyboard_loop_win(self):
        import msvcrt
        while True:
            if msvcrt.kbhit():
                ch = msvcrt.getwch().lower()
                if ch == "q":
                    self.quit_requested.emit()
                    break
                elif ch == "p":
                    self.pause_requested.emit()
            time.sleep(0.05)

    def _keyboard_loop_unix(self):
        import tty
        import termios
        import select
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            while True:
                r, _, _ = select.select([sys.stdin], [], [], 0.05)
                if r:
                    ch = sys.stdin.read(1).lower()
                    if ch == "q":
                        self.quit_requested.emit()
                        break
                    elif ch == "p":
                        self.pause_requested.emit()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
