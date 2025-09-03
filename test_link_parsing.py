#!/usr/bin/env python3
"""
测试链接解析功能
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.link_parser import link_parser, link_validator

def test_problematic_link():
    """测试有问题的链接"""
    test_url = "https://v.douyin.com/Det5gcK62-4/"
    
    print(f"测试链接: {test_url}")
    print("=" * 50)
    
    # 测试链接解析器
    print("1. 测试 is_douyin_link:")
    is_douyin = link_parser.is_douyin_link(test_url)
    print(f"   结果: {is_douyin}")
    
    print("\n2. 测试 extract_video_id:")
    video_id = link_parser.extract_video_id(test_url)
    print(f"   结果: {video_id}")
    
    print("\n3. 测试 link_validator:")
    validation = link_validator.validate_douyin_link(test_url)
    print(f"   结果: {validation}")
    
    print("\n4. 测试正则表达式匹配:")
    import re
    douyin_pattern = r'https?://v\.douyin\.com/[A-Za-z0-9]+/?'
    match = re.search(douyin_pattern, test_url)
    print(f"   正则匹配: {match}")
    if match:
        print(f"   匹配内容: {match.group()}")

if __name__ == "__main__":
    test_problematic_link()

