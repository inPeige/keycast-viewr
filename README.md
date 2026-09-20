# KeyCast Viewer

实时展示键盘和鼠标操作的可视化小工具（Windows）。窗口可自由缩放，分为两块：

- **上方**：放大显示当前正在按下的组合键 / 鼠标操作（例如按下 `Alt+A` 会显示两个大按键 `Alt` `+` `A`）。
- **下方**：一个虚拟键盘 + 一个鼠标图形，实时高亮你正在按下的按键、鼠标按钮和滚轮方向。

底层用 [`pynput`](https://pypi.org/project/pynput/) 做全局键鼠监听，用 [PySide6](https://pypi.org/project/PySide6/)（Qt）绘制界面，可用 PyInstaller 打包成单个 `.exe`。

---

## 目录结构

```
keycast-viewer/
├── run.py                  # 启动入口
├── requirements.txt
├── keycast.spec            # PyInstaller 打包配置
├── build_windows.bat       # 一键在 Windows 上打包 exe
└── keycast/
    ├── app.py              # QApplication 装配
    ├── main_window.py      # 主窗口：上方overlay + 下方键盘/鼠标
    ├── overlay_view.py     # 上方放大组合键显示
    ├── keyboard_view.py    # 虚拟键盘布局与高亮
    ├── keycap.py           # 单个按键控件（自绘）
    ├── mouse_view.py       # 鼠标图形与按钮/滚轮高亮
    ├── listener.py         # 全局键鼠监听 -> Qt 信号（跨线程安全）
    ├── keydefs.py          # 键盘布局定义 + pynput 事件归一化
    └── theme.py            # 配色常量
```

## 本地运行（开发）

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
python run.py
```

- **Windows**：开箱即用。如果想捕获以管理员权限运行的程序（如某些游戏）内的按键，请以管理员身份运行本程序。
- **macOS**（仅用于开发调试）：需要在「系统设置 → 隐私与安全性 → 辅助功能 / 输入监控」中授予终端或应用权限，否则监听会失败。

## 打包成 Windows exe

在一台安装了 Python 3.9+ 的 Windows 机器上，双击或在命令行运行：

```bat
build_windows.bat
```

完成后可执行文件位于 `dist\KeyCastViewer.exe`，可直接双击运行、拷贝分发（目标机无需安装 Python）。

手动打包等价命令：

```bat
pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm keycast.spec
```

## 使用说明

- 拖动窗口边缘缩放；拖动上下两块之间的分隔条可调整上/下区域比例。
- **右键窗口**弹出菜单：可切换「Always on top（窗口置顶）」或退出。
- 支持标准 TKL（无小键盘）布局：功能键、主键区、导航键、方向键。
- 鼠标图形高亮左键 / 右键 / 中键，滚轮上下滚动时中键位置显示方向箭头。

## 已知说明

- 组合键顺序固定为 `Ctrl → Alt → Shift → Win → 普通键`，左右修饰键在上方显示时会合并为一个（如同时/分别按左右 Ctrl 都显示一个 `Ctrl`），但在下方虚拟键盘上会精确高亮对应的左/右键。
- 物理按键识别在 Windows 上基于虚拟键码（`vk`），因此按 `Shift+2` 时高亮的仍是物理 `2` 键，识别稳定。
