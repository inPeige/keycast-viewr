#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# 把 KeyCast Viewer 打包成 macOS 的 .app（用于分发/调试成品形态）。
# 产物: dist/KeyCastViewer.app
# 注意: .app 首次运行同样需要在「辅助功能/输入监控」里给它授权。
# ---------------------------------------------------------------------------
set -e
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  ./.venv/bin/python -m pip install --upgrade pip -q
fi
./.venv/bin/pip install -r requirements.txt pyinstaller -q

echo "[build] 正在用 PyInstaller 打包 .app ..."
./.venv/bin/pyinstaller --noconfirm --clean \
  --windowed \
  --name "KeyCastViewer" \
  run.py

echo "[done] 产物: dist/KeyCastViewer.app"
echo "运行: open dist/KeyCastViewer.app  (首次需授权 辅助功能/输入监控)"
