#!/usr/bin/env python3
"""
测试包含下划线的抖音链接匹配
"""
import re

def test_underscore_pattern():
    """测试包含下划线的抖音链接匹配"""
    # 测试消息内容（来自日志）
    message_content = "1.05 04/11 aNW:/ b@n.QX 怎么，见了我，卸势都不会了？ # 千夜 # cos # 变装  [https://v.douyin.com/_tNRIScpmpY/](https://v.douyin.com/_tNRIScpmpY/) 复制此链接，打开Dou音搜索，直接观看视频！"
    
    print(f"测试消息内容:")
    print(f"{message_content}")
    print("=" * 80)
    
    # 使用修复后的正则表达式
    douyin_pattern = r'https?://(?:v\.)?douyin\.com/[A-Za-z0-9\-_]+/?'
    matches = re.findall(douyin_pattern, message_content)
    
    print(f"正则表达式: {douyin_pattern}")
    print(f"匹配结果: {matches}")
    print(f"匹配数量: {len(matches)}")
    
    if matches:
        # 去重处理
        unique_matches = list(set(matches))
        print(f"去重后: {unique_matches}")
        
        for i, url in enumerate(unique_matches):
            # 清理URL
            clean_url = url.strip()
            if clean_url.endswith(')'):
                clean_url = clean_url.rstrip(')')
            if '?' in clean_url:
                clean_url = clean_url.split('?')[0]
            if '#' in clean_url:
                clean_url = clean_url.split('#')[0]
            print(f"清理后的URL {i+1}: {clean_url}")
    else:
        print("❌ 没有匹配到任何链接")
    
    print("\n" + "=" * 80)
    print("测试其他包含下划线的链接:")
    
    # 测试其他可能的链接格式
    test_urls = [
        "https://v.douyin.com/_tNRIScpmpY/",
        "https://v.douyin.com/abc123_def456/",
        "https://v.douyin.com/test_123/",
        "https://v.douyin.com/ABC_DEF_GHI/",
        "https://v.douyin.com/123_456_789/",
        "https://v.douyin.com/a-b_c-d_e-f/"
    ]
    
    for url in test_urls:
        match = re.search(douyin_pattern, url)
        print(f"URL: {url}")
        print(f"  匹配: {'✅' if match else '❌'}")
        if match:
            print(f"  匹配内容: {match.group()}")

if __name__ == "__main__":
    test_underscore_pattern()

