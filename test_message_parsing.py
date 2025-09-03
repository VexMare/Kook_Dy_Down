#!/usr/bin/env python3
"""
测试消息解析功能
"""
import re

def test_message_parsing():
    """测试消息解析"""
    message_content = "9.76 05/01 j@c.aN Rxf:/ 这是缘 亦是命中最美的相见 # 叹云兮 # 翻唱 # 芸汐传 # 鞠婧祎 # 这是缘亦是命中最美的相见  [https://v.douyin.com/Det5gcK62-4/](https://v.douyin.com/Det5gcK62-4/) 复制此链接，打开Dou音搜索，直接观看视频！"
    
    print(f"消息内容: {message_content}")
    print("=" * 80)
    
    # 使用修复后的正则表达式
    douyin_pattern = r'https?://(?:v\.)?douyin\.com/[A-Za-z0-9\-]+/?'
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
    
    # 测试更宽松的正则表达式
    print("\n" + "=" * 80)
    print("测试更宽松的正则表达式:")
    loose_pattern = r'https?://v\.douyin\.com/[A-Za-z0-9\-]+/?'
    loose_matches = re.findall(loose_pattern, message_content)
    print(f"宽松正则: {loose_pattern}")
    print(f"匹配结果: {loose_matches}")

if __name__ == "__main__":
    test_message_parsing()
