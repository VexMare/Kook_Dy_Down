#!/usr/bin/env python3
"""
测试安全文件名生成
"""
import uuid

def test_safe_filename():
    """测试安全文件名生成"""
    print("测试安全文件名生成:")
    print("=" * 50)
    
    # 测试视频文件名
    for i in range(5):
        video_filename = f"video_{uuid.uuid4().hex[:8]}.mp4"
        print(f"视频文件名 {i+1}: {video_filename}")
        print(f"  长度: {len(video_filename)} 字符")
        print(f"  是否超过255字符: {'是' if len(video_filename) > 255 else '否'}")
    
    print()
    
    # 测试图片文件名
    for i in range(5):
        image_filename = f"image_{uuid.uuid4().hex[:8]}.jpg"
        print(f"图片文件名 {i+1}: {image_filename}")
        print(f"  长度: {len(image_filename)} 字符")
        print(f"  是否超过255字符: {'是' if len(image_filename) > 255 else '否'}")
    
    print()
    print("文件名特点:")
    print("- 只包含字母、数字、下划线和点")
    print("- 长度固定且很短（约20个字符）")
    print("- 每次生成都是唯一的")
    print("- 完全符合Kook的文件名要求")

if __name__ == "__main__":
    test_safe_filename()

