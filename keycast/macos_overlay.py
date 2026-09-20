"""macOS-only helper to make the window a true floating overlay.

Sets the native NSWindow level and collection behavior so the window:
  * floats above normal windows of *other* apps,
  * shows on every Space (virtual desktop),
  * appears over fullscreen apps.

This is best-effort: it requires ``pyobjc`` (``pyobjc-framework-Cocoa``) which
is macOS-only. On Windows / Linux, or if pyobjc is missing, it simply does
nothing and the plain Qt ``WindowStaysOnTopHint`` still applies.
"""

from __future__ import annotations

import sys


def make_window_float(widget) -> bool:
    """Elevate the given QWidget's native window. Returns True on success."""
    if sys.platform != "darwin":
        return False

    # Only touch native Cocoa objects when the real Cocoa GUI backend is
    # active. Under 'offscreen' (tests/CI) winId() is not a valid NSView and
    # messaging it would crash the process, which try/except cannot catch.
    try:
        from PySide6.QtGui import QGuiApplication
        if QGuiApplication.platformName() != "cocoa":
            return False
    except Exception:
        return False

    try:
        import objc
        from AppKit import (
            NSWindowCollectionBehaviorCanJoinAllSpaces,
            NSWindowCollectionBehaviorStationary,
            NSWindowCollectionBehaviorFullScreenAuxiliary,
        )
    except Exception:
        return False

    try:
        wid = int(widget.winId())
        if not wid:
            return False
        # winId() returns the NSView* on macOS; grab its parent NSWindow.
        view = objc.objc_object(c_void_p=wid)
        win = view.window()
        if win is None:
            return False

        # NSFloatingWindowLevel == 3: above normal windows, below system UI.
        win.setLevel_(3)
        win.setCollectionBehavior_(
            NSWindowCollectionBehaviorCanJoinAllSpaces
            | NSWindowCollectionBehaviorStationary
            | NSWindowCollectionBehaviorFullScreenAuxiliary
        )
        return True
    except Exception:
        return False
