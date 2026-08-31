import subprocess
import os
import sys
import glob
import re
import time

# 下载B站视频工具
# ============================================================
# 🛠️ 用户可配置选项
# ============================================================
# 设置为 True  → 合并后自动删除原始分离的音视频文件
# 设置为 False → 合并后保留原始分离的音视频文件
DELETE_ORIGINAL_AFTER_MERGE = False  # ← 在这里修改默认行为
# 下载失败时的最大重试次数
MAX_RETRY_COUNT = 3
# ============================================================


def clean_bilibili_url(url):
    """
    清理 B站 URL，只保留 BV 号部分
    """
    # 提取 BV 号
    bv_match = re.search(r'BV[a-zA-Z0-9]+', url)
    if bv_match:
        bv = bv_match.group(0)
        return f"https://www.bilibili.com/video/{bv}/"
    return url


def get_user_input():
    """
    获取用户输入的配置参数
    """
    print("\n" + "=" * 60)
    print("📝 请配置下载参数（直接按回车使用默认值）")
    print("=" * 60)

    # 获取视频 URL
    default_url = "https://www.bilibili.com/video/BV1EHdUYEEEj/"
    print(f"\n📺 视频 URL (默认: {default_url})")
    url_input = input("请输入视频 URL: ").strip()
    video_url = url_input if url_input else default_url

    # ============================================================
    # 清理 URL，移除追踪参数
    # ============================================================
    video_url = clean_bilibili_url(video_url)
    print(f"✅ 已清理 URL: {video_url}")
    # ============================================================

    # 从 URL 中提取 BV 号
    bv_match = re.search(r'BV[a-zA-Z0-9]+', video_url)
    bv = bv_match.group(0) if bv_match else "BV1EHdUYEEEj"

    # 获取输出目录
    default_output_dir = r"E:\Pycharm-Projects\bilibili\MP4"
    print(f"\n📂 输出目录 (默认: {default_output_dir})")
    dir_input = input("请输入输出目录: ").strip()
    output_dir = dir_input if dir_input else default_output_dir

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # ============================================================
    # 获取下载文件名
    # ============================================================
    print(f"\n📝 下载文件名（不含扩展名，默认使用视频标题）")
    filename_input = input("请输入下载文件名: ").strip()
    # ============================================================

    return {
        'video_url': video_url,
        'bv': bv,
        'output_dir': output_dir,
        'filename': filename_input
    }


def preview_and_get_quality(video_url):
    """
    预览视频信息并让用户选择清晰度（一次性完成，避免重复请求）
    """
    print("\n" + "=" * 60)
    print("🔍 正在获取视频信息...")
    print("=" * 60)

    preview_cmd = [
        'you-get',
        '--cookies', 'www.bilibili.com_cookies.txt',
        '--info',
        video_url
    ]

    try:
        result = subprocess.run(preview_cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', check=True)
        output = result.stdout

        # 提取标题
        title_match = re.search(r'title:\s*(.+?)(?:\n|$)', output)
        if title_match:
            print(f"📺 视频标题: {title_match.group(1).strip()}")

        # 解析清晰度选项
        quality_pattern = r'- format:\s+(\S+)\s+container:\s+(\S+)\s+quality:\s+(.+?)(?:\n|$)'
        matches = re.findall(quality_pattern, output)

        if not matches:
            print("⚠️ 未能解析到清晰度选项，将使用默认清晰度")
            return None

        # 显示选项列表
        print("\n" + "=" * 60)
        print("📊 可用的清晰度选项:")
        print("=" * 60)

        quality_list = []
        for i, (fmt, container, quality) in enumerate(matches, 1):
            quality_clean = quality.strip()
            resolution_match = re.search(r'(\d+P)', quality_clean)
            resolution = resolution_match.group(1) if resolution_match else quality_clean
            # 提取文件大小
            size_match = re.search(r'size:\s+([\d.]+)\s+([KM]iB)', output)
            size_info = f" ({size_match.group(1)} {size_match.group(2)})" if size_match else ""
            print(f"   {i}. {resolution} ({fmt}){size_info}")
            quality_list.append({
                'index': i,
                'format': fmt,
                'container': container,
                'quality': quality_clean,
                'display': f"{resolution} ({fmt})"
            })

        # 让用户选择
        print(f"\n📌 默认选择: {quality_list[0]['display']}")
        choice = input("请输入序号选择清晰度（直接回车使用默认）: ").strip()

        if not choice:
            selected = quality_list[0]
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(quality_list):
                    selected = quality_list[idx]
                else:
                    print(f"⚠️ 无效序号，使用默认: {quality_list[0]['display']}")
                    selected = quality_list[0]
            except ValueError:
                print(f"⚠️ 无效输入，使用默认: {quality_list[0]['display']}")
                selected = quality_list[0]

        print(f"\n✅ 已选择: {selected['display']}")
        return selected

    except subprocess.CalledProcessError as e:
        print(f"❌ 获取视频信息失败: {e}")
        print("💡 提示: 请检查网络连接或 Cookies 是否有效")
        return None


def get_delete_choice():
    """
    询问用户是否删除原始分离文件
    """
    print("\n" + "=" * 60)
    print("🗑️ 原始文件处理选项")
    print("=" * 60)
    print("\n合并完成后，是否删除原始的分离文件（[00].mp4 和 [01].mp4）？")
    print("   y → 保留原始文件")
    print("   n → 删除原始文件（仅保留合并后的完整视频）")

    choice = input("\n请选择 (y/n，直接回车默认保留): ").strip().lower()

    if choice == 'n':
        return False  # 删除
    else:
        return True  # 保留（默认）


def confirm_download(config_info):
    """
    显示所有配置信息并询问用户是否确认下载
    """
    print("\n" + "=" * 60)
    print("📋 请确认以下下载配置")
    print("=" * 60)

    print(f"\n📺 视频链接: {config_info['video_url']}")
    print(f"📂 输出目录: {config_info['output_dir']}")
    print(f"📝 下载文件名: {config_info['filename'] if config_info['filename'] else '(使用视频标题)'}")
    print(f"🎬 选择清晰度: {config_info['quality_display']}")
    print(f"🗑️ 原始文件: {'保留' if config_info['delete_original'] else '删除'}")

    print("\n" + "-" * 40)
    confirm = input("✅ 确认以上信息，开始下载？(y/n): ").strip().lower()
    return confirm == 'y'


def download_with_retry(command, max_retries=MAX_RETRY_COUNT):
    """
    带重试机制的下载函数
    """
    print("\n[1/3] 🚀 开始调用 you-get 下载工具...")
    print(f"📋 执行命令: {' '.join(command)}")
    print("─" * 50)

    for attempt in range(1, max_retries + 1):
        if attempt > 1:
            print(f"\n🔄 第 {attempt} 次重试下载...")
            time.sleep(2)  # 等待2秒后再重试

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='ignore',
            bufsize=1
        )

        print("[2/3] ⬇️ 正在下载视频，请稍候...")

        # 实时读取标准输出
        for line in iter(process.stdout.readline, ''):
            if '%' in line and 'MB' in line:
                print(f"\r{line.strip()}", end='')
                sys.stdout.flush()
            elif any(key in line for key in ['site:', 'title:', 'Downloading', 'size:']):
                print(f"\n{line.strip()}")

        print("\n[3/3] 📦 下载流程结束，正在处理结果...")

        # 读取所有错误输出
        stderr_output = process.stderr.read()
        if stderr_output:
            print("\n💡 提示信息:")
            print(stderr_output.strip())

        process.wait()

        if process.returncode == 0:
            return True
        else:
            if attempt < max_retries:
                print(f"⚠️ 下载失败 (返回码: {process.returncode})，正在重试...")
            else:
                print(f"❌ 下载失败，已重试 {max_retries} 次")

    return False


def merge_video_with_ffmpeg(output_dir, delete_original):
    """
    列出目录中的视频和音频文件，让用户手动选择要合并的文件
    """
    print("\n" + "=" * 60)
    print("🎬 开始音视频合并流程")
    print("=" * 60)

    print(f"\n📍 当前工作目录: {output_dir}")

    # 切换到输出目录
    os.chdir(output_dir)
    print("✅ 已切换到输出目录")

    # 查找所有 .mp4 文件
    print("\n🔍 正在扫描目录中的 .mp4 文件...")
    all_mp4 = glob.glob("*.mp4")

    if not all_mp4:
        print("⚠️ 没有找到任何 MP4 文件")
        return False

    print(f"\n📁 找到 {len(all_mp4)} 个 MP4 文件:")
    for i, f in enumerate(all_mp4, 1):
        size_mb = os.path.getsize(f) // (1024 * 1024)
        print(f"   {i}. {f} ({size_mb} MB)")

    # ============================================================
    # 让用户选择视频文件
    # ============================================================
    print("\n" + "-" * 40)
    print("🎬 请选择视频文件（通常包含画面，文件较大）")

    while True:
        try:
            video_choice = input(f"请输入序号 (1-{len(all_mp4)}): ").strip()
            if not video_choice:
                print("❌ 必须选择一个文件")
                continue
            video_idx = int(video_choice) - 1
            if 0 <= video_idx < len(all_mp4):
                video_file = all_mp4[video_idx]
                break
            else:
                print(f"⚠️ 请输入 1 到 {len(all_mp4)} 之间的数字")
        except ValueError:
            print("⚠️ 请输入有效的数字")

    # ============================================================
    # 让用户选择音频文件
    # ============================================================
    print("\n🎵 请选择音频文件（通常包含声音，文件较小）")
    print("   (可以选择与视频相同的文件，或直接回车跳过)")

    while True:
        try:
            audio_choice = input(f"请输入序号 (1-{len(all_mp4)}，回车跳过): ").strip()
            if not audio_choice:
                audio_file = None
                print("⏭️ 已跳过音频选择（将只保留视频）")
                break
            audio_idx = int(audio_choice) - 1
            if 0 <= audio_idx < len(all_mp4):
                audio_file = all_mp4[audio_idx]
                if audio_file == video_file:
                    print("⚠️ 音频文件不能与视频文件相同，请重新选择")
                    continue
                break
            else:
                print(f"⚠️ 请输入 1 到 {len(all_mp4)} 之间的数字")
        except ValueError:
            print("⚠️ 请输入有效的数字")

    # ============================================================
    # 生成输出文件名
    # ============================================================
    base_name = re.sub(r'\.mp4$', '', video_file)
    default_output_name = f"{base_name}_合并"
    print(f"\n📝 合并后的文件名 (默认: {default_output_name}.mp4)")
    name_input = input("请输入文件名（不含扩展名）: ").strip()
    output_name = name_input if name_input else default_output_name
    output_file = f"{output_name}.mp4"

    # ============================================================
    # 显示合并信息并确认
    # ============================================================
    print("\n" + "-" * 40)
    print("📊 合并信息确认:")
    print(f"   🎬 视频文件: {video_file} ({os.path.getsize(video_file) // (1024 * 1024)} MB)")
    if audio_file:
        print(f"   🎵 音频文件: {audio_file} ({os.path.getsize(audio_file) // (1024 * 1024)} MB)")
    else:
        print("   🎵 音频文件: (无)")
    print(f"   📄 输出文件: {output_file}")
    print("-" * 40)

    confirm = input("✅ 确认合并？(y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ 已取消合并")
        return False

    # ============================================================
    # 构建 FFmpeg 命令
    # ============================================================
    if audio_file:
        ffmpeg_cmd = [
            r'E:\ffmpeg\ffmpeg-9.0.1-essentials_build\bin\ffmpeg.exe',
            '-i', video_file,
            '-i', audio_file,
            '-c', 'copy',
            '-y',
            output_file
        ]
    else:
        # 如果没有音频文件，直接复制视频
        ffmpeg_cmd = [
            r'E:\ffmpeg\ffmpeg-9.0.1-essentials_build\bin\ffmpeg.exe',
            '-i', video_file,
            '-c', 'copy',
            '-y',
            output_file
        ]

    print("\n⚙️ 执行合并命令:")
    print(f"   {' '.join(ffmpeg_cmd)}")
    print("\n⏳ 正在处理，请稍候...")

    try:
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore',
                                check=True)
        print("\n✅ 合并完成！")
        print(f"📂 完整视频已保存为: {output_file}")
        print(f"📦 文件大小: {os.path.getsize(output_file) // (1024 * 1024)} MB")

        # ============================================================
        # 根据用户选择处理原始文件
        # ============================================================
        if delete_original:
            # 保留原始文件
            print("\n📁 原始文件已保留")
            print(f"   🎬 {video_file}")
            if audio_file:
                print(f"   🎵 {audio_file}")
        else:
            # 删除原始文件
            try:
                os.remove(video_file)
                print(f"   ✅ 已删除: {video_file}")
                if audio_file:
                    os.remove(audio_file)
                    print(f"   ✅ 已删除: {audio_file}")
                print("\n🗑️ 原始分离文件已删除")
            except Exception as e:
                print(f"\n⚠️ 删除原始文件时出错: {e}")
        # ============================================================

        return True

    except subprocess.CalledProcessError as e:
        print(f"\n❌ 合并失败: {e}")
        if e.stderr:
            print(f"错误详情: {e.stderr[:500]}...")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🎯 B站视频下载工具 v1.0")
    print("=" * 60)

    # ============================================================
    # 获取用户配置
    # ============================================================
    config = get_user_input()
    video_url = config['video_url']
    bv = config['bv']
    output_dir = config['output_dir']
    filename = config['filename']
    # ============================================================

    print(f"\n📺 目标视频: {video_url}")
    print(f"📂 输出目录: {output_dir}")

    # ============================================================
    # 一次性获取信息并选择清晰度
    # ============================================================
    selected_quality = preview_and_get_quality(video_url)
    # ============================================================

    # ============================================================
    # 询问是否删除原始文件
    # ============================================================
    delete_original = get_delete_choice()
    # ============================================================

    # ============================================================
    # 确认下载
    # ============================================================
    config_info = {
        'video_url': video_url,
        'output_dir': output_dir,
        'filename': filename,
        'quality_display': selected_quality['display'] if selected_quality else '(默认)',
        'delete_original': delete_original
    }

    if not confirm_download(config_info):
        print("❌ 已取消下载")
        sys.exit(0)
    # ============================================================

    # ============================================================
    # 构建下载命令
    # ============================================================
    command = [
        'you-get',
        '--cookies', 'www.bilibili.com_cookies.txt',
        '--no-caption',
        '--output-dir', output_dir,
    ]

    if selected_quality:
        command.extend(['--format', selected_quality['format']])

    if filename:
        command.extend(['--output-filename', filename])

    command.append(video_url)
    # ============================================================

    # 执行下载（带重试）
    success = download_with_retry(command)

    if success:
        print("\n✅ 下载流程完成！")
        # 自动合并音视频
        merge_result = merge_video_with_ffmpeg(output_dir, delete_original)
        if merge_result:
            print("\n" + "=" * 60)
            print("🎉 全部完成！视频已下载并合并完毕！")
            print("=" * 60)
        else:
            print("\n⚠️ 合并过程遇到问题，请检查文件")
    else:
        print("\n❌ 下载失败，请检查网络或 Cookie 是否有效")