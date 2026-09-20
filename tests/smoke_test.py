"""Headless smoke test: build the UI, simulate input, force painting."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from keycast.listener import InputBridge
from keycast.main_window import MainWindow

app = QApplication([])
bridge = InputBridge()          # do NOT start() -> avoids OS permission needs
w = MainWindow(bridge)
w.resize(1000, 560)
w.show()
app.processEvents()

failures = []

def check(cond, msg):
    if not cond:
        failures.append(msg)

# 0) Floating-overlay behavior
from PySide6.QtCore import Qt
check(bool(w.windowFlags() & Qt.WindowStaysOnTopHint), "should be always-on-top by default")
check(bool(w.windowFlags() & Qt.WindowDoesNotAcceptFocus), "should not accept keyboard focus")
check(w.testAttribute(Qt.WA_ShowWithoutActivating), "should show without activating")

# 1) Simulate Alt + A
bridge.keyPressed.emit("alt_l")
bridge.keyPressed.emit("a")
app.processEvents()
tokens = w._compute_tokens()
check(tokens == ["Alt", "A"], f"combo Alt+A expected, got {tokens}")
check(w.keyboard._caps["a"][0]._active, "key 'a' cap should be active")
check(w.keyboard._caps["alt_l"][0]._active, "alt_l cap should be active")

# 2) Release A, Alt
bridge.keyReleased.emit("a")
bridge.keyReleased.emit("alt_l")
app.processEvents()
check(w._compute_tokens() == [], f"combo should be empty after release, got {w._compute_tokens()}")
check(not w.keyboard._caps["a"][0]._active, "key 'a' cap should be inactive after release")

# 3) Ctrl+Shift+K ordering (press K then shift then ctrl -> still Ctrl,Shift,K)
bridge.keyPressed.emit("k")
bridge.keyPressed.emit("shift_r")
bridge.keyPressed.emit("ctrl_l")
app.processEvents()
tokens = w._compute_tokens()
check(tokens == ["Ctrl", "Shift", "K"], f"ordering expected Ctrl,Shift,K got {tokens}")
bridge.keyReleased.emit("k"); bridge.keyReleased.emit("shift_r"); bridge.keyReleased.emit("ctrl_l")
app.processEvents()

# 4) Mouse click lights the mouse graphic but must NOT appear in the top combo
bridge.buttonPressed.emit("mouse_left")
app.processEvents()
check("mouse_left" in w.mouse._active, "mouse_left should light the mouse graphic")
check("L-Click" not in w._compute_tokens(), "mouse click must NOT appear in top combo")
check(w._compute_tokens() == [], f"combo should stay empty on mouse click, got {w._compute_tokens()}")
bridge.buttonReleased.emit("mouse_left")
bridge.scrolled.emit("scroll_up")
app.processEvents()
check(w.mouse._scroll_dir == "scroll_up", "scroll_up should flash")
check("Scroll\u2191" not in w._compute_tokens(), "scroll must NOT appear in top combo")

# 5) Force every custom widget to paint (catches paint-time exceptions)
for widget in (w.overlay, w.keyboard, w.mouse):
    _ = widget.grab()
# also paint with an active combo showing in overlay
bridge.keyPressed.emit("ctrl_l"); bridge.keyPressed.emit("c")
app.processEvents()
_ = w.overlay.grab()
_ = w.grab()

if failures:
    print("SMOKE TEST FAILED:")
    for f in failures:
        print("  -", f)
    raise SystemExit(1)
print("SMOKE TEST PASSED")
