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

## 在 macOS 上调试（推荐用来打磨视觉效果）

app 本身跨平台，可直接在 Mac 上运行调试：

```bash
./run_mac.sh          # 自动建 venv、装依赖并启动
# 或手动:
./.venv/bin/python run.py
```

**关键：授予权限**。macOS 出于安全限制，全局键鼠监听必须授权，否则窗口能开但**捕获不到按键**：

1. 打开「系统设置 → 隐私与安全性」
2. 分别在 **「输入监控」** 和 **「辅助功能」** 里，把你运行命令的**终端 App**（Terminal.app 或 iTerm）打勾开启
3. **完全退出终端并重开**，再运行 `./run_mac.sh`

调试循环：改代码 → 重新运行 `./run_mac.sh` 看效果，满意后再 `git push` 让云端出新的 Windows exe。

> 说明：这是给 Windows 用的软件，所以键盘布局刻意保留 Windows 样式（含 `Win`、`Menu` 键）。在 Mac 上按 `⌘` 会点亮 `Win` 键位，这是预期行为。

### 打包成 macOS .app（可选）

```bash
./build_mac.sh        # 产物: dist/KeyCastViewer.app
open dist/KeyCastViewer.app
```

打包后的 `.app` 首次运行同样需要在「辅助功能/输入监控」里给 **KeyCastViewer** 单独授权。

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

- **默认悬浮置顶**：窗口始终浮在其他软件之上，且**不会抢走键盘焦点**——你点击/操作别的软件、正常打字时，它只是静静飘在上层显示，不会被切到后台。
- **右键窗口**弹出菜单：可切换「Always on top（窗口置顶）」或退出。
- 拖动窗口边缘缩放；拖动上下两块之间的分隔条可调整上/下区域比例。
- 支持标准 TKL（无小键盘）布局：功能键、主键区、导航键、方向键。
- 鼠标图形高亮左键 / 右键 / 中键，滚轮上下滚动时中键位置显示方向箭头。

> macOS 上若想让它同时**浮在全屏应用之上、并出现在所有 Spaces（虚拟桌面）**，需要 `pyobjc`（`run_mac.sh` 会自动安装，见 `requirements-mac.txt`）。缺少时会自动降级为普通置顶，不影响 Windows。

## 已知说明

- 组合键顺序固定为 `Ctrl → Alt → Shift → Win → 普通键`，左右修饰键在上方显示时会合并为一个（如同时/分别按左右 Ctrl 都显示一个 `Ctrl`），但在下方虚拟键盘上会精确高亮对应的左/右键。
- 物理按键识别在 Windows 上基于虚拟键码（`vk`），因此按 `Shift+2` 时高亮的仍是物理 `2` 键，识别稳定。
