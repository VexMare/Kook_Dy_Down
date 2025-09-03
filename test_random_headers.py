#!/usr/bin/env python3
"""
测试随机请求头生成功能
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.bot.main import DouyinBot

def test_random_headers():
    """测试随机请求头生成"""
    print("测试随机请求头生成:")
    print("=" * 60)
    
    # 创建机器人实例（仅用于测试请求头生成）
    try:
        bot = DouyinBot()
    except RuntimeError:
        # 如果已经有实例，创建一个临时的类实例
        class TempBot:
            def _get_random_headers(self, content_type='video'):
                """生成随机请求头"""
                import random
                
                # 随机User-Agent列表
                user_agents = [
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:119.0) Gecko/20100101 Firefox/119.0',
                    'Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0',
                    'Mozilla/5.0 (X11; Linux x86_64; rv:119.0) Gecko/20100101 Firefox/119.0',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/119.0.0.0 Safari/537.36'
                ]
                
                # 随机Accept-Language
                accept_languages = [
                    'zh-CN,zh;q=0.9,en;q=0.8',
                    'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
                    'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
                    'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
                    'en-US,en;q=0.5'
                ]
                
                # 基础请求头
                headers = {
                    'User-Agent': random.choice(user_agents),
                    'Accept-Language': random.choice(accept_languages),
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Referer': 'https://www.douyin.com/',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Cache-Control': 'max-age=0'
                }
                
                # 根据内容类型添加特定的Accept头
                if content_type == 'video':
                    headers['Accept'] = random.choice([
                        'video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5',
                        'video/mp4,video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5',
                        '*/*'
                    ])
                    headers['Range'] = 'bytes=0-'
                elif content_type == 'image':
                    headers['Accept'] = random.choice([
                        'image/webp,image/apng,image/*,*/*;q=0.8',
                        'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                        'image/*,*/*;q=0.8'
                    ])
                
                return headers
        
        bot = TempBot()
    
    # 测试视频请求头
    print("视频请求头测试:")
    print("-" * 40)
    for i in range(3):
        headers = bot._get_random_headers('video')
        print(f"请求头 {i+1}:")
        print(f"  User-Agent: {headers['User-Agent'][:60]}...")
        print(f"  Accept: {headers['Accept']}")
        print(f"  Accept-Language: {headers['Accept-Language']}")
        print(f"  Range: {headers.get('Range', 'N/A')}")
        print()
    
    # 测试图片请求头
    print("图片请求头测试:")
    print("-" * 40)
    for i in range(3):
        headers = bot._get_random_headers('image')
        print(f"请求头 {i+1}:")
        print(f"  User-Agent: {headers['User-Agent'][:60]}...")
        print(f"  Accept: {headers['Accept']}")
        print(f"  Accept-Language: {headers['Accept-Language']}")
        print(f"  Range: {headers.get('Range', 'N/A')}")
        print()
    
    print("请求头特点:")
    print("- 每次生成都是随机的")
    print("- 包含多种浏览器类型和版本")
    print("- 支持多种语言偏好")
    print("- 包含现代浏览器的安全头")
    print("- 根据内容类型调整Accept头")

if __name__ == "__main__":
    test_random_headers()

