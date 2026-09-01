markdown
# 🎬 B站视频下载工具集

一个功能完整的视频下载、字幕生成、音视频处理工具集，主要针对 B站 视频，支持批量处理、自动合并、字幕生成等功能。

---

bbb

aaa

## 📁 项目结构
E:\Pycharm-Projects\bilibili
├── get_video.py # 通用视频下载工具（核心）
├── generate_subtitle.py # Whisper 字幕生成工具
├── ffmpeg_merge_tool.py # 音视频合并工具
├── bilibili.py # B站 视频下载工具（完整版）
├── uise.py # 网站爬虫实验脚本
├── script.py # 示例脚本
├── MP4/ # 视频输出目录
├── .venv/ # Python 虚拟环境
├── *.txt # Cookie 文件（站点认证）
└── README.md # 项目说明

text

---

## 🛠️ 工具说明

### 1. `get_video.py` - 通用视频下载工具（推荐使用）

最稳定的视频下载工具，基于 `yt-dlp`，支持主流视频网站。

**功能特性：**
- ✅ 支持 B站、Tokyomotion 等主流视频网站
- ✅ 自动选择最佳音视频组合并合并
- ✅ 交互式配置（URL、输出目录）
- ✅ 自动重命名避免文件覆盖
- ✅ 下载失败自动重试（默认3次）
- ✅ 实时下载进度显示

**使用方法：**

# ```bash

python get_video.py
交互流程：

输入视频 URL（直接回车使用默认示例）

输入输出目录（直接回车使用默认）

确认下载信息

自动下载并合并音视频

2. generate_subtitle.py - Whisper 字幕生成工具
基于 OpenAI Whisper 的本地字幕生成工具，支持多种语言和模型。

功能特性：

✅ 支持多种 Whisper 模型（tiny ~ large）

✅ 支持多种语言（中文、英文、日文、韩文、自动检测）

✅ 支持多种输出格式（srt、vtt、txt）

✅ 交互式配置（模型目录、视频选择、输出目录）

✅ 自动检查文件生成状态

使用方法：

bash
# python generate_subtitle.py
交互流程：

设置 Whisper 模型存放目录

选择视频文件所在目录

从列表中选择要处理的视频

设置字幕输出目录

选择模型、语言、输出格式

确认并开始生成

3. ffmpeg_merge_tool.py - 音视频合并工具
用于手动合并分离的视频和音频文件，基于 FFmpeg。

功能特性：

✅ 列出目录中所有 MP4 文件

✅ 手动选择视频和音频文件

✅ 自定义输出文件名

✅ 支持跳过音频（只保留视频）

使用方法：

bash
# python ffmpeg_merge_tool.py
交互流程：

选择文件目录

选择视频文件

选择音频文件（可跳过）

设置输出文件名

确认并执行合并

4. bilibili.py - B站 视频下载工具（完整版）
基于 you-get 的 B站 专用下载工具，支持清晰度选择和音视频合并。

功能特性：

✅ 自动清理 URL 追踪参数

✅ 获取视频信息并选择清晰度

✅ 音视频合并（手动选择）

✅ 自动重试机制

使用方法：

bash
# python bilibili.py
📦 依赖安装
创建虚拟环境
bash
# python -m venv .venv
.venv\Scripts\activate  # Windows
安装依赖
bash
# pip install yt-dlp           # get_video.py 核心依赖
# pip install openai-whisper   # 字幕生成工具
# pip install ffmpeg-python    # 音视频处理（可选）
外部工具
FFmpeg：音视频处理核心，需单独安装并添加到 PATH

下载地址：https://ffmpeg.org/download.html

或使用国内镜像：https://www.gyan.dev/ffmpeg/builds/

Whisper 模型：首次运行时会自动下载到 E:\Pycharm-Projects\WhisperModels

🔧 配置说明
路径配置
各工具中的默认路径可根据实际情况修改：

工具	配置项	默认路径
get_video.py	default_url	B站示例视频
get_video.py	default_output_dir	E:\Pycharm-Projects\bilibili\MP4
generate_subtitle.py	DEFAULT_MODEL_DIR	E:\Pycharm-Projects\WhisperModels
generate_subtitle.py	DEFAULT_VIDEO_DIR	E:\Pycharm-Projects\bilibili\MP4
ffmpeg_merge_tool.py	FFMPEG_PATH	FFmpeg 可执行文件路径
Cookie 配置
部分工具可能需要 Cookie 文件进行认证：

www.bilibili.com_cookies.txt：B站 认证 Cookie

uise-official.com_cookies.txt：UISE 网站认证 Cookie

注意：Cookie 文件使用 Netscape 格式，可通过浏览器扩展导出。

🚀 快速开始
下载视频（最常用）
bash
# python get_video.py
生成字幕
bash
# python generate_subtitle.py
合并音视频
bash
# python ffmpeg_merge_tool.py
⚠️ 注意事项
视频版权：请仅下载您有权获取的内容，遵守目标网站的服务条款。

Cookie 时效性：Cookie 文件会过期，如遇认证失败请重新导出。

FFmpeg 依赖：确保 FFmpeg 已正确安装并可在命令行中调用。

Whisper 模型：首次使用需下载模型文件（约 1-3 GB），请耐心等待。

网络环境：部分网站可能需要特定网络环境才能访问。

📝 更新日志
版本	日期	更新内容
v1.0	2026-08-30	初始版本，核心功能完成
📄 许可证
仅供个人学习研究使用。

🤝 贡献
欢迎提出问题和改进建议！

text