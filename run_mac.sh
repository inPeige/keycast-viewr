#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# 在 macOS 上直接运行 KeyCast Viewer 进行调试。
# 首次运行需在「系统设置 → 隐私与安全性 → 辅助功能 / 输入监控」中
# 给你的终端 App（Terminal / iTerm）授权，否则捕获不到全局按键。
# ---------------------------------------------------------------------------
set -e
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "[setup] 创建虚拟环境..."
  python3 -m venv .venv
  ./.venv/bin/python -m pip install --upgrade pip -q
  ./.venv/bin/pip install -r requirements.txt -q
fi

# macOS 悬浮增强（跨 Spaces / 全屏应用之上），静默安装、失败不影响运行
./.venv/bin/pip install -r requirements-mac.txt -q 2>/dev/null || true

echo "[run] 启动 KeyCast Viewer... (关闭窗口即退出)"
exec ./.venv/bin/python run.py
