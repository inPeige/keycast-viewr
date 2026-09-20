"""Application entry point."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from .listener import InputBridge
from .main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("KeyCast Viewer")

    bridge = InputBridge()
    window = MainWindow(bridge)
    window.show()

    try:
        bridge.start()
    except Exception as exc:  # pragma: no cover
        # Show the error in the overlay area instead of crashing silently.
        from PySide6.QtWidgets import QMessageBox

        QMessageBox.critical(
            window,
            "Input capture failed",
            f"Could not start the global input listener:\n\n{exc}\n\n"
            "On macOS you must grant Accessibility permission. On Windows this "
            "should work out of the box (run as admin if capturing elevated apps).",
        )

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
