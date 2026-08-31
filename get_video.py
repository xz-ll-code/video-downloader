import subprocess
import os
import sys
import re
import time

# ============================================================
# 🛠️ 用户可配置选项
# ============================================================
# 下载失败时的最大重试次数
MAX_RETRY_COUNT = 3
# ============================================================


def get_user_input():
    """获取用户输入的配置参数"""
    print("\n" + "=" * 60)
    print("📝 请配置下载参数（直接按回车使用默认值）")
    print("=" * 60)

    # 获取视频 URL
    default_url = "https://www.bilibili.com/video/BV17M496DE9a/"
    print(f"\n📺 视频 URL (默认: {default_url})")
    url_input = input("请输入视频 URL: ").strip()
    video_url = url_input if url_input else default_url

    # 获取输出目录
    default_output_dir = r"E:\Pycharm-Projects\bilibili\MP4"
    print(f"\n📂 输出目录 (默认: {default_output_dir})")
    dir_input = input("请输入输出目录: ").strip()
    output_dir = dir_input if dir_input else default_output_dir

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    return {
        'video_url': video_url,
        'output_dir': output_dir
    }


def confirm_download(config_info):
    """显示配置信息并询问用户是否确认下载"""
    print("\n" + "=" * 60)
    print("📋 请确认以下下载配置")
    print("=" * 60)

    print(f"\n📺 视频链接: {config_info['video_url']}")
    print(f"📂 输出目录: {config_info['output_dir']}")

    print("\n" + "-" * 40)
    confirm = input("✅ 确认以上信息，开始下载？(y/n): ").strip().lower()
    return confirm == 'y'


def download_with_retry(command, max_retries=MAX_RETRY_COUNT):
    """带重试机制的下载函数"""
    print("\n[1/3] 🚀 开始调用 yt-dlp 下载工具...")
    print(f"📋 执行命令: {' '.join(command)}")
    print("─" * 50)

    for attempt in range(1, max_retries + 1):
        if attempt > 1:
            print(f"\n🔄 第 {attempt} 次重试下载...")
            time.sleep(2)

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='ignore',
            bufsize=1
        )

        print("[2/3] ⬇️ 正在下载视频，请稍候...")

        for line in iter(process.stdout.readline, ''):
            if '%' in line and ('MiB' in line or 'KiB' in line):
                print(f"\r{line.strip()}", end='')
                sys.stdout.flush()
            elif any(key in line for key in ['[download] Destination:', '[download]']) and '%' not in line:
                print(f"\n{line.strip()}")

        print("\n[3/3] 📦 下载流程结束，正在处理结果...")

        process.wait()

        if process.returncode == 0:
            return True
        else:
            if attempt < max_retries:
                print(f"⚠️ 下载失败 (返回码: {process.returncode})，正在重试...")
            else:
                print(f"❌ 下载失败，已重试 {max_retries} 次")

    return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🎯 通用视频下载工具 get_video v1.0")
    print("=" * 60)

    config = get_user_input()
    video_url = config['video_url']
    output_dir = config['output_dir']

    # 确认下载
    config_info = {
        'video_url': video_url,
        'output_dir': output_dir
    }

    if not confirm_download(config_info):
        print("❌ 已取消下载")
        sys.exit(0)

    # 构建下载命令 - 不指定 -f，yt-dlp 自动选择最佳音视频组合
    command = [
        'yt-dlp',
        '--output', f'{output_dir}/%(title)s_%(autonumber)s.%(ext)s',
        '--autonumber-size', '2',
        '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        video_url
    ]

    success = download_with_retry(command)

    if success:
        print("\n✅ 下载流程完成！")
        print("🎉 视频下载完毕！")
    else:
        print("\n❌ 下载失败，请检查网络或 URL 是否有效")