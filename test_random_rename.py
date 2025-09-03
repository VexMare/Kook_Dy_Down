#!/usr/bin/env python3
"""
测试随机重命名功能
"""
import uuid
import os
import tempfile

def test_random_filename_generation():
    """测试随机文件名生成"""
    print("测试随机文件名生成:")
    print("=" * 50)
    
    # 测试视频文件名
    for i in range(3):
        video_filename = f"{uuid.uuid4().hex}.mp4"
        print(f"视频文件名 {i+1}: {video_filename}")
        print(f"  长度: {len(video_filename)} 字符")
        special_chars = '[](){}!@#$%^&*+=|\\:";\'<>?,/'
        has_special = any(c in video_filename for c in special_chars)
        print(f"  是否包含特殊字符: {'是' if has_special else '否'}")
    
    print()
    
    # 测试图片文件名
    for i in range(3):
        image_filename = f"{uuid.uuid4().hex}.jpg"
        print(f"图片文件名 {i+1}: {image_filename}")
        print(f"  长度: {len(image_filename)} 字符")
        special_chars = '[](){}!@#$%^&*+=|\\:";\'<>?,/'
        has_special = any(c in image_filename for c in special_chars)
        print(f"  是否包含特殊字符: {'是' if has_special else '否'}")
    
    print()
    
    # 测试临时文件路径
    temp_dir = tempfile.mkdtemp()
    print(f"临时目录: {temp_dir}")
    
    video_path = os.path.join(temp_dir, f"{uuid.uuid4().hex}.mp4")
    image_path = os.path.join(temp_dir, f"{uuid.uuid4().hex}.jpg")
    
    print(f"视频路径: {video_path}")
    print(f"图片路径: {image_path}")
    
    # 清理测试目录
    try:
        os.rmdir(temp_dir)
        print("测试目录清理完成")
    except:
        print("测试目录清理失败")

if __name__ == "__main__":
    test_random_filename_generation()
