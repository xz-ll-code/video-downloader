import os
import sys
import glob
import re
import subprocess

# 合并B站音视频分离工具
# ============================================================
# 🛠️ 用户可配置选项
# ============================================================
# FFmpeg 可执行文件的路径（根据你的实际情况修改）
FFMPEG_PATH = r"E:\ffmpeg\ffmpeg-9.0.1-essentials_build\bin\ffmpeg.exe"
# ============================================================


def get_directory():
    """
    获取用户输入的文件路径
    """
    print("\n" + "=" * 60)
    print("📂 请指定包含视频文件的目录")
    print("=" * 60)

    default_dir = r"E:\Pycharm-Projects\bilibili\MP4"
    print(f"\n📁 默认目录: {default_dir}")
    dir_input = input("请输入目录路径（直接回车使用默认）: ").strip()
    target_dir = dir_input if dir_input else default_dir

    # 检查目录是否存在
    if not os.path.exists(target_dir):
        print(f"❌ 目录不存在: {target_dir}")
        return None

    if not os.path.isdir(target_dir):
        print(f"❌ 路径不是目录: {target_dir}")
        return None

    return target_dir


def list_mp4_files(directory):
    """
    列出目录中的所有 MP4 文件
    """
    os.chdir(directory)
    all_mp4 = glob.glob("*.mp4")

    if not all_mp4:
        print("⚠️ 该目录中没有找到任何 MP4 文件")
        return None

    print(f"\n📁 找到 {len(all_mp4)} 个 MP4 文件:")
    for i, f in enumerate(all_mp4, 1):
        size_mb = os.path.getsize(f) // (1024 * 1024)
        print(f"   {i}. {f} ({size_mb} MB)")

    return all_mp4


def select_file(all_mp4, prompt, allow_skip=False):
    """
    让用户从列表中选择一个文件
    """
    print("\n" + "-" * 40)
    print(prompt)

    while True:
        try:
            if allow_skip:
                choice = input(f"请输入序号 (1-{len(all_mp4)}，回车跳过): ").strip()
                if not choice:
                    return None
            else:
                choice = input(f"请输入序号 (1-{len(all_mp4)}): ").strip()
                if not choice:
                    print("❌ 必须选择一个文件")
                    continue

            idx = int(choice) - 1
            if 0 <= idx < len(all_mp4):
                return all_mp4[idx]
            else:
                print(f"⚠️ 请输入 1 到 {len(all_mp4)} 之间的数字")
        except ValueError:
            print("⚠️ 请输入有效的数字")


def confirm_merge(video_file, audio_file, output_file, directory):
    """
    显示合并信息并确认
    """
    print("\n" + "-" * 40)
    print("📊 合并信息确认:")
    print(f"   📂 目录: {directory}")
    print(f"   🎬 视频文件: {video_file} ({os.path.getsize(video_file) // (1024 * 1024)} MB)")
    if audio_file:
        print(f"   🎵 音频文件: {audio_file} ({os.path.getsize(audio_file) // (1024 * 1024)} MB)")
    else:
        print("   🎵 音频文件: (无)")
    print(f"   📄 输出文件: {output_file}")
    print("-" * 40)

    confirm = input("✅ 确认合并？(y/n): ").strip().lower()
    return confirm == 'y'


def merge_with_ffmpeg(directory, video_file, audio_file, output_file):
    """
    执行 FFmpeg 合并
    """
    # 切换到目标目录
    os.chdir(directory)

    # 构建 FFmpeg 命令
    if audio_file:
        ffmpeg_cmd = [
            FFMPEG_PATH,
            '-i', video_file,
            '-i', audio_file,
            '-c', 'copy',
            '-y',
            output_file
        ]
    else:
        # 如果没有音频文件，直接复制视频
        ffmpeg_cmd = [
            FFMPEG_PATH,
            '-i', video_file,
            '-c', 'copy',
            '-y',
            output_file
        ]

    print("\n⚙️ 执行合并命令:")
    print(f"   {' '.join(ffmpeg_cmd)}")
    print("\n⏳ 正在处理，请稍候...")

    try:
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', check=True)
        print("\n✅ 合并完成！")
        print(f"📂 完整视频已保存为: {output_file}")
        print(f"📦 文件大小: {os.path.getsize(output_file) // (1024 * 1024)} MB")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 合并失败: {e}")
        if e.stderr:
            print(f"错误详情: {e.stderr[:500]}...")
        return False


def main():
    print("\n" + "=" * 60)
    print("🎬 音视频合并工具 v1.0")
    print("=" * 60)

    # 1. 获取目录
    directory = get_directory()
    if not directory:
        sys.exit(1)

    # 2. 列出 MP4 文件
    all_mp4 = list_mp4_files(directory)
    if not all_mp4:
        sys.exit(1)

    # 3. 选择视频文件
    video_file = select_file(
        all_mp4,
        "🎬 请选择视频文件（通常包含画面，文件较大）",
        allow_skip=False
    )
    if not video_file:
        print("❌ 必须选择一个视频文件")
        sys.exit(1)

    # 4. 选择音频文件
    audio_file = select_file(
        all_mp4,
        "🎵 请选择音频文件（通常包含声音，文件较小）\n   (回车跳过，将只保留视频)",
        allow_skip=True
    )

    # 5. 生成输出文件名
    base_name = re.sub(r'\.mp4$', '', video_file)
    default_output_name = f"{base_name}_合并"
    print(f"\n📝 合并后的文件名 (默认: {default_output_name}.mp4)")
    name_input = input("请输入文件名（不含扩展名）: ").strip()
    output_name = name_input if name_input else default_output_name
    output_file = f"{output_name}.mp4"

    # 6. 确认合并
    if not confirm_merge(video_file, audio_file, output_file, directory):
        print("❌ 已取消合并")
        sys.exit(0)

    # 7. 执行合并
    success = merge_with_ffmpeg(directory, video_file, audio_file, output_file)

    if success:
        print("\n" + "=" * 60)
        print("🎉 合并完成！")
        print("=" * 60)
    else:
        print("\n❌ 合并失败，请检查文件")


if __name__ == "__main__":
    main()