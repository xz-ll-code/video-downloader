import os
import sys
import glob
import subprocess
import time

# 字幕生成工具
# ============================================================
# 🛠️ 默认配置
# ============================================================
DEFAULT_MODEL_DIR = r"E:\Pycharm-Projects\WhisperModels"
DEFAULT_VIDEO_DIR = r"E:\Pycharm-Projects\bilibili\MP4"
DEFAULT_OUTPUT_DIR = r"E:\Pycharm-Projects\bilibili\MP4"
DEFAULT_MODEL = "medium"
DEFAULT_LANGUAGE = "zh"
# ============================================================


def get_directory(prompt, default_dir, must_exist=False):
    """
    获取用户输入的目录路径
    """
    print(f"\n📂 {prompt}")
    print(f"   默认: {default_dir}")
    user_input = input("请输入目录路径（直接回车使用默认）: ").strip()
    target_dir = user_input if user_input else default_dir

    # 如果目录不存在，询问是否创建
    if not os.path.exists(target_dir):
        if must_exist:
            print(f"❌ 目录不存在: {target_dir}")
            return None
        else:
            create = input(f"⚠️ 目录不存在，是否创建？(y/n): ").strip().lower()
            if create == 'y':
                os.makedirs(target_dir, exist_ok=True)
                print(f"✅ 已创建目录: {target_dir}")
            else:
                return None

    return target_dir


def list_video_files(directory):
    """
    列出目录中的所有视频文件（支持常见视频格式）
    """
    video_extensions = ['*.mp4', '*.mkv', '*.avi', '*.mov', '*.flv', '*.wmv', '*.webm', '*.m4v']
    all_videos = []
    for ext in video_extensions:
        all_videos.extend(glob.glob(os.path.join(directory, ext)))

    if not all_videos:
        print("⚠️ 该目录中没有找到任何视频文件")
        return None

    print(f"\n📁 找到 {len(all_videos)} 个视频文件:")
    for i, f in enumerate(all_videos, 1):
        size_mb = os.path.getsize(f) // (1024 * 1024)
        filename = os.path.basename(f)
        print(f"   {i}. {filename} ({size_mb} MB)")

    return all_videos


def select_file(file_list, prompt):
    """
    让用户从列表中选择一个文件
    """
    print(f"\n🎬 {prompt}")

    while True:
        try:
            choice = input(f"请输入序号 (1-{len(file_list)}): ").strip()
            if not choice:
                print("❌ 必须选择一个文件")
                continue
            idx = int(choice) - 1
            if 0 <= idx < len(file_list):
                return file_list[idx]
            else:
                print(f"⚠️ 请输入 1 到 {len(file_list)} 之间的数字")
        except ValueError:
            print("⚠️ 请输入有效的数字")


def get_model_choice():
    """
    让用户选择 Whisper 模型
    """
    print("\n" + "=" * 60)
    print("🤖 请选择 Whisper 模型")
    print("=" * 60)
    print("   1. tiny     (极快，准确率低)")
    print("   2. base     (很快，准确率一般)")
    print("   3. small    (较快，准确率较好)")
    print("   4. medium   (较慢，准确率高) [默认]")
    print("   5. large    (很慢，准确率最高)")

    choice = input("\n请输入序号 (1-5，直接回车使用默认 medium): ").strip()

    models = {
        '1': 'tiny',
        '2': 'base',
        '3': 'small',
        '4': 'medium',
        '5': 'large'
    }

    if choice in models:
        return models[choice]
    else:
        print("✅ 使用默认模型: medium")
        return "medium"


def get_language_choice():
    """
    让用户选择视频语言
    """
    print("\n" + "=" * 60)
    print("🌐 请选择视频语言")
    print("=" * 60)
    print("   1. zh   (中文) [默认]")
    print("   2. en   (英文)")
    print("   3. ja   (日文)")
    print("   4. ko   (韩文)")
    print("   5. auto (自动检测)")

    choice = input("\n请输入序号 (1-5，直接回车使用默认 zh): ").strip()

    languages = {
        '1': 'zh',
        '2': 'en',
        '3': 'ja',
        '4': 'ko',
        '5': 'auto'
    }

    if choice in languages:
        selected = languages[choice]
        if selected == 'auto':
            return None  # None 表示自动检测
        return selected
    else:
        print("✅ 使用默认语言: zh")
        return "zh"


def get_output_format():
    """
    让用户选择输出格式
    """
    print("\n" + "=" * 60)
    print("📝 请选择字幕输出格式")
    print("=" * 60)
    print("   1. srt  (最通用) [默认]")
    print("   2. vtt  (WebVTT)")
    print("   3. txt  (纯文本)")

    choice = input("\n请输入序号 (1-3，直接回车使用默认 srt): ").strip()

    formats = {
        '1': 'srt',
        '2': 'vtt',
        '3': 'txt'
    }

    if choice in formats:
        return formats[choice]
    else:
        print("✅ 使用默认格式: srt")
        return "srt"


def confirm_generation(config_info):
    """
    显示所有配置信息并确认
    """
    print("\n" + "=" * 60)
    print("📋 请确认以下配置信息")
    print("=" * 60)

    print(f"\n📂 模型存放目录: {config_info['model_dir']}")
    print(f"🤖 使用模型: {config_info['model']}")
    print(f"🌐 视频语言: {config_info['language'] if config_info['language'] else '自动检测'}")
    print(f"📂 视频文件: {os.path.basename(config_info['video_file'])}")
    print(f"📂 字幕输出目录: {config_info['output_dir']}")
    print(f"📝 输出格式: {config_info['output_format']}")

    print("\n" + "-" * 40)
    confirm = input("✅ 确认以上信息，开始生成字幕？(y/n): ").strip().lower()
    return confirm == 'y'


def run_whisper(config_info):
    """
    执行 Whisper 命令
    """
    # 构建命令 - 关键：必须包含 --output_dir
    command = [
        'whisper',
        config_info['video_file'],
        '--model', config_info['model'],
        '--model_dir', config_info['model_dir'],
        '--output_format', config_info['output_format'],
        '--output_dir', config_info['output_dir'],
    ]

    # 如果指定了语言，添加 --language 参数
    if config_info['language']:
        command.extend(['--language', config_info['language']])

    # 计算预期输出文件名
    base_name = os.path.basename(config_info['video_file']).rsplit('.', 1)[0]
    expected_file = os.path.join(config_info['output_dir'], f"{base_name}.{config_info['output_format']}")

    print("\n" + "=" * 60)
    print("🚀 开始生成字幕...")
    print("=" * 60)
    print(f"📋 执行命令: {' '.join(command)}")
    print(f"📄 预期输出文件: {expected_file}")
    print("─" * 50)

    try:
        # 直接运行命令，输出会显示在终端
        result = subprocess.run(command, check=True)

        # 等待一秒让文件系统完成写入
        time.sleep(1)

        # 检查文件是否真的生成了
        if os.path.exists(expected_file):
            file_size = os.path.getsize(expected_file) // 1024
            print("\n" + "=" * 60)
            print("✅ 字幕生成完成！")
            print("=" * 60)
            print(f"📂 字幕文件已保存到: {config_info['output_dir']}")
            print(f"📝 文件名: {base_name}.{config_info['output_format']}")
            print(f"📦 文件大小: {file_size} KB")
            return True
        else:
            # 尝试查找是否有其他文件生成
            print("\n⚠️ 预期文件未找到，正在扫描目录...")
            all_files = glob.glob(os.path.join(config_info['output_dir'], f"*{config_info['output_format']}"))
            if all_files:
                print(f"📁 找到以下 {config_info['output_format']} 文件:")
                for f in all_files:
                    print(f"   - {os.path.basename(f)}")
                return True
            else:
                print(f"❌ 未找到任何 {config_info['output_format']} 文件")
                print("💡 提示: 请检查 Whisper 输出信息，可能文件被保存到了其他位置")
                return False

    except subprocess.CalledProcessError as e:
        print(f"\n❌ 字幕生成失败: {e}")
        if e.stderr:
            print(f"错误详情: {e.stderr[:500]}...")
        return False


def main():
    print("\n" + "=" * 60)
    print("🎯 Whisper 字幕生成工具 v1.0")
    print("=" * 60)

    # ============================================================
    # 1. 获取模型存放目录
    # ============================================================
    model_dir = get_directory(
        "请输入 Whisper 模型存放目录",
        DEFAULT_MODEL_DIR,
        must_exist=False
    )
    if not model_dir:
        print("❌ 未指定模型目录，程序退出")
        sys.exit(1)

    # ============================================================
    # 2. 获取视频文件目录
    # ============================================================
    video_dir = get_directory(
        "请输入视频文件所在目录",
        DEFAULT_VIDEO_DIR,
        must_exist=True
    )
    if not video_dir:
        print("❌ 视频目录不存在，程序退出")
        sys.exit(1)

    # ============================================================
    # 3. 列出视频文件并让用户选择
    # ============================================================
    video_files = list_video_files(video_dir)
    if not video_files:
        print("❌ 没有找到任何视频文件，程序退出")
        sys.exit(1)

    video_file = select_file(video_files, "请选择要生成字幕的视频文件")

    # ============================================================
    # 4. 获取字幕输出目录
    # ============================================================
    output_dir = get_directory(
        "请输入字幕文件输出目录",
        DEFAULT_OUTPUT_DIR,
        must_exist=False
    )
    if not output_dir:
        print("❌ 未指定输出目录，程序退出")
        sys.exit(1)

    # ============================================================
    # 5. 选择模型
    # ============================================================
    model = get_model_choice()

    # ============================================================
    # 6. 选择语言
    # ============================================================
    language = get_language_choice()

    # ============================================================
    # 7. 选择输出格式
    # ============================================================
    output_format = get_output_format()

    # ============================================================
    # 8. 确认并执行
    # ============================================================
    config_info = {
        'model_dir': model_dir,
        'model': model,
        'language': language,
        'video_file': video_file,
        'output_dir': output_dir,
        'output_format': output_format
    }

    if not confirm_generation(config_info):
        print("❌ 已取消操作")
        sys.exit(0)

    # ============================================================
    # 9. 执行 Whisper
    # ============================================================
    success = run_whisper(config_info)

    if success:
        print("\n🎉 全部完成！")
    else:
        print("\n⚠️ 生成过程中遇到问题，请检查错误信息")


if __name__ == "__main__":
    main()