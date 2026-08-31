from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service  # 需要导入 Service
from webdriver_manager.chrome import ChromeDriverManager  # 导入管理器
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from bs4 import BeautifulSoup
import requests

# --- 1. 设置Selenium ---
options = Options()
# options.add_argument('--headless')  # 无界面模式，调试时可先注释掉
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')  # 建议加上，避免资源限制问题
# 添加User-Agent避免被识别为机器人
options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

# --- 修改这里：使用 webdriver-manager 自动管理驱动 ---
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# 目标B站视频URL
url = "https://www.bilibili.com/video/BV1EHdUYEEEj/"

try:
    # --- 2. 访问页面并等待关键元素加载 ---
    print("正在通过浏览器访问页面...")
    driver.get(url)
    time.sleep(5)  # 等待一段时间让页面初步加载

    # 可以等待某个特定元素出现，例如视频标题，确保页面加载完成
    # WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".video-title")))

    # --- 3. 获取渲染后的HTML并解析 ---
    html_content = driver.page_source
    print(f"获取到渲染后HTML内容长度: {len(html_content)} 字符")

    soup = BeautifulSoup(html_content, 'html.parser')

    # 尝试查找 video 标签（B站通常仍然不会直接暴露）
    video_tag = soup.find('video')
    if video_tag:
        source_tag = video_tag.find('source')
        if source_tag and source_tag.get('src'):
            video_url = source_tag.get('src')
            print(f"从 <source> 找到视频地址: {video_url}")
        else:
            video_url = video_tag.get('src')
            if video_url:
                print(f"从 <video> 标签的 src 属性找到视频地址: {video_url}")
    else:
        print("⚠️ 未找到 <video> 标签，这与预期一致。")

    # --- 4. 更深入的提取方法：遍历所有脚本，寻找包含视频数据的完整JSON ---
    import json
    import re

    scripts = soup.find_all('script')
    video_url = None

    print(f"总共找到 {len(scripts)} 个 <script> 标签，开始筛选...")

    for idx, script in enumerate(scripts):
        if not script.string:
            continue

        script_content = script.string.strip()

        # 只处理包含 videoData 或 dash 或 pages 的脚本
        if not any(keyword in script_content for keyword in ['videoData', '"dash"', '"pages"', 'baseUrl']):
            continue

        print(f"\n--- 检查第 {idx + 1} 个脚本，长度: {len(script_content)} 字符 ---")

        # 尝试提取 window.__INITIAL_STATE__ 或 __NEXT_DATA__ 或直接是 JSON
        # 方法1：匹配 window.__INITIAL_STATE__ = {...}
        match = re.search(r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});?$', script_content, re.DOTALL)
        if not match:
            # 方法2：匹配 __NEXT_DATA__ = {...} （B站新版架构）
            match = re.search(r'__NEXT_DATA__\s*=\s*(\{.*?\});?$', script_content, re.DOTALL)
        if not match:
            # 方法3：直接尝试解析整个脚本内容（如果它本身就是一个JSON对象）
            try:
                # 尝试直接解析
                json.loads(script_content)
                print("脚本本身是有效的JSON，尝试解析...")
                # 直接当作JSON处理
                data = json.loads(script_content)
                # 处理数据...
                continue
            except:
                pass
            print("  未匹配到已知模式，跳过此脚本")
            continue

        json_str = match.group(1)
        print(f"  提取到 JSON 数据块，长度: {len(json_str)} 字符")

        try:
            data = json.loads(json_str)
            print("  ✅ JSON 解析成功！")

            # --- 提取视频地址（兼容多种数据结构）---
            # 情况1：videoData.pages[0].video.baseUrl
            video_data = data.get('videoData', {})
            pages = video_data.get('pages', [])
            if pages:
                first_page = pages[0]
                video_url = first_page.get('video', {}).get('baseUrl')
                if video_url:
                    print(f"  ✅ 从 videoData.pages 提取到视频地址: {video_url[:80]}...")
                    break

            # 情况2：dash.video[0].baseUrl (新版B站)
            if not video_url:
                dash_data = data.get('dash', {})
                if dash_data:
                    video_infos = dash_data.get('video', [])
                    if video_infos:
                        video_url = video_infos[0].get('baseUrl')
                        if video_url:
                            print(f"  ✅ 从 dash.video 提取到视频地址: {video_url[:80]}...")
                            break

            # 情况3：如果都没有，打印部分数据结构供调试
            if not video_url:
                print("  ⚠️ 数据结构中未找到 'baseUrl'，打印部分结构：")
                # 打印 videoData 或 dash 的键名
                if video_data:
                    print(f"    videoData 的键: {list(video_data.keys())}")
                if dash_data:
                    print(f"    dash 的键: {list(dash_data.keys())}")

        except json.JSONDecodeError as e:
            print(f"  ❌ JSON 解析失败: {e}")
            # 打印前200字符帮助调试
            print(f"  数据开头: {json_str[:200]}")

    # --- 下载视频（如果成功提取到地址）---
    if video_url:
        print(f"\n开始下载视频...")
        try:
            headers = {
                'Referer': 'https://www.bilibili.com/',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            video_response = requests.get(video_url, headers=headers, stream=True, timeout=30)
            if video_response.status_code == 200:
                total_size = int(video_response.headers.get('content-length', 0))
                print(f"视频大小: {total_size / (1024 * 1024):.2f} MB")
                with open('bilibili_video.mp4', 'wb') as f:
                    downloaded = 0
                    for chunk in video_response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                percent = (downloaded / total_size) * 100
                                print(f"\r下载进度: {percent:.1f}%", end='')
                print("\n✅ 视频下载完成！")
            else:
                print(f"❌ 视频下载失败，HTTP状态码: {video_response.status_code}")
                print("💡 提示: 视频地址可能已过期或有访问限制。")
        except Exception as e:
            print(f"❌ 下载过程出错: {e}")
    else:
        print("\n❌ 在所有脚本中均未找到可用的视频地址。")
        print("💡 可能原因: 页面需要登录、视频为付费内容，或B站更新了数据加载方式。")
        print("💡 建议: 可以考虑使用第三方库 'bilibili-api-python' 来获取视频地址。")

    # --- 5. 下载视频 (如果成功提取到地址) ---
    if video_url:
        print(f"\n开始下载视频...")
        try:
            # B站视频有防盗链，需要添加 Referer 头
            headers = {
                'Referer': 'https://www.bilibili.com/',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            # stream=True 用于流式下载大文件
            video_response = requests.get(video_url, headers=headers, stream=True, timeout=30)
            if video_response.status_code == 200:
                total_size = int(video_response.headers.get('content-length', 0))
                print(f"视频大小: {total_size / (1024 * 1024):.2f} MB")

                # 以二进制方式写入文件
                with open('bilibili_video.mp4', 'wb') as f:
                    downloaded = 0
                    for chunk in video_response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            # 简单进度提示
                            if total_size > 0:
                                percent = (downloaded / total_size) * 100
                                print(f"\r下载进度: {percent:.1f}%", end='')
                print("\n✅ 视频下载完成！文件名为: bilibili_video.mp4")
            else:
                print(f"❌ 视频下载失败，HTTP状态码: {video_response.status_code}")
                print("💡 提示: 视频地址可能已过期或有访问限制。")

        except requests.exceptions.RequestException as e:
            print(f"\n❌ 下载过程发生网络错误: {e}")
        except Exception as e:
            print(f"\n❌ 下载过程发生未知错误: {e}")
    else:
        print("\n❌ 未找到视频地址，下载流程结束。")
        print("💡 可能原因: 页面结构变化、需要登录或视频为付费内容。")

except Exception as e:
    print(f"❌ 发生错误: {e}")
finally:
    driver.quit()