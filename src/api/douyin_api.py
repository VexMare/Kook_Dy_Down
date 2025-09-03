"""
抖音解析API接口
"""
import requests
import re
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs
from loguru import logger

from src.models.video import VideoInfo
from config.settings import settings


class DouyinAPI:
    """抖音解析API类"""
    
    def __init__(self):
        # 使用你之前验证过的API
        self.base_url = "https://dy.gglz.cn/api/hybrid/video_data"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def parse_url(self, url: str) -> Optional[str]:
        """解析抖音链接，提取视频ID"""
        if not url:
            return None
        
        # 清理URL，移除Markdown格式
        clean_url = url.strip()
        if clean_url.startswith('[') and clean_url.endswith(')'):
            # 处理Markdown格式的链接 [text](url)
            match = re.search(r'\]\(([^)]+)\)', clean_url)
            if match:
                clean_url = match.group(1)
        
        # 支持的抖音链接格式
        patterns = [
            r'https?://v\.douyin\.com/[A-Za-z0-9]+/?',
            r'https?://www\.douyin\.com/video/(\d+)',
            r'https?://m\.douyin\.com/video/(\d+)',
            r'https?://www\.iesdouyin\.com/share/video/(\d+)',
            r'https?://www\.iesdouyin\.com/share/video/(\d+)/\?region=',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, clean_url)
            if match:
                if len(match.groups()) > 0:
                    return match.group(1)
                else:
                    # 对于短链接，需要进一步处理
                    return self._extract_video_id_from_short_url(clean_url)
        
        logger.warning(f"不支持的抖音链接格式: {clean_url}")
        return None
    
    def _extract_video_id_from_short_url(self, url: str) -> Optional[str]:
        """从短链接中提取视频ID"""
        try:
            # 先获取重定向后的URL
            response = self.session.head(url, allow_redirects=True, timeout=10)
            final_url = response.url
            
            # 从最终URL中提取视频ID
            video_id_pattern = r'/video/(\d+)'
            match = re.search(video_id_pattern, final_url)
            if match:
                return match.group(1)
            
            logger.warning(f"无法从短链接提取视频ID: {url} -> {final_url}")
            return None
            
        except Exception as e:
            logger.error(f"处理短链接时出错: {e}")
            return None
    
    def get_video_info(self, url: str) -> Optional[VideoInfo]:
        """获取视频信息"""
        try:
            # 清理URL，移除Markdown格式
            clean_url = url.strip()
            if clean_url.startswith('[') and clean_url.endswith(')'):
                # 处理Markdown格式的链接 [text](url)
                match = re.search(r'\]\(([^)]+)\)', clean_url)
                if match:
                    clean_url = match.group(1)
            
            logger.info(f"原始URL: {url}")
            logger.info(f"清理后URL: {clean_url}")
            
            # 解析URL获取视频ID
            video_id = self.parse_url(clean_url)
            if not video_id:
                logger.error(f"无法解析视频ID: {clean_url}")
                return None
            
            # 使用你之前验证过的API调用方式
            logger.info(f"使用API: {self.base_url}")
            logger.info(f"请求参数: url={clean_url}")
            
            params = {'url': clean_url}
            logger.info("  开始发送API请求...")
            response = self.session.get(self.base_url, params=params, timeout=30)
            logger.info("  API请求完成")
            
            logger.info(f"响应状态码: {response.status_code}")
            logger.info(f"响应头: {dict(response.headers)}")
            
            logger.info("  开始解析响应...")
            response.raise_for_status()
            data = response.json()
            logger.info("  响应解析完成")
            
            logger.info(f"响应数据: {data}")
            
            # 检查API响应状态
            if data.get('code') != 200:
                logger.error(f"API错误: {data.get('msg', '未知错误')}")
                return None
            
            # 解析视频信息
            logger.info("  开始解析视频数据...")
            video_data = data.get('data', {})
            result = self._parse_video_data(video_data, clean_url)
            logger.info("  视频数据解析完成")
            return result
            
        except Exception as e:
            logger.error(f"获取视频信息时出错: {e}")
            return None
    
    def _parse_video_data(self, data: Dict[str, Any], original_url: str) -> VideoInfo:
        """解析API返回的视频数据"""
        try:
            logger.info("    开始解析视频基本信息...")
            # 基本信息 - 使用你之前的数据结构
            video_id = data.get('aweme_id', '')  # 使用aweme_id作为视频ID
            description = data.get('desc', '')
            logger.info(f"    视频ID: {video_id}")
            logger.info(f"    描述: {description[:50]}...")
            
            logger.info("    开始解析作者信息...")
            # 作者信息
            author_info = data.get('author', {})
            author_nickname = author_info.get('nickname', '')
            author_id = author_info.get('uid', '')
            logger.info(f"    作者昵称: {author_nickname}")
            logger.info(f"    作者ID: {author_id}")
            
            logger.info("    开始解析视频链接...")
            # 视频链接
            video_url_watermark = data.get('video', {}).get('play_addr', {}).get('url_list', [''])[0]
            video_url_no_watermark = video_url_watermark  # 通常相同
            logger.info(f"    视频链接: {video_url_watermark[:50]}...")
            
            # 音频链接 - 从视频中提取
            audio_url = data.get('video', {}).get('play_addr', {}).get('url_list', [''])[0]
            logger.info(f"    音频链接: {audio_url[:50]}...")
            
            # 封面链接 - 获取所有可用的链接
            cover_url_list = data.get('video', {}).get('cover', {}).get('url_list', [])
            cover_url = cover_url_list[0] if cover_url_list else ""
            cover_urls = [url for url in cover_url_list if url.strip()]  # 过滤空链接
            logger.info(f"    封面链接数量: {len(cover_urls)}")
            for i, url in enumerate(cover_urls):
                logger.info(f"    封面链接 {i+1}: {url[:50]}...")
            
            logger.info("    开始解析时长和统计信息...")
            # 时长
            duration = data.get('video', {}).get('duration', 0) // 1000  # 转换为秒
            logger.info(f"    时长: {duration}秒")
            
            # 统计信息
            statistics = data.get('statistics', {})
            play_count = statistics.get('play_count', 0)
            like_count = statistics.get('digg_count', 0)
            comment_count = statistics.get('comment_count', 0)
            share_count = statistics.get('share_count', 0)
            logger.info(f"    播放量: {play_count}")
            logger.info(f"    点赞数: {like_count}")
            logger.info(f"    评论数: {comment_count}")
            logger.info(f"    分享数: {share_count}")
            
            logger.info("    开始创建VideoInfo对象...")
            # 创建VideoInfo对象
            video_info = VideoInfo(
                title=description,  # 使用描述作为标题
                author=author_nickname,
                author_id=author_id,
                video_id=video_id,
                cover_url=cover_url,
                cover_urls=cover_urls,
                audio_url=audio_url,
                video_url=video_url_watermark,
                duration=duration,
                play_count=play_count,
                like_count=like_count,
                comment_count=comment_count,
                share_count=share_count,
                description=description,
                tags=[],  # 暂时为空
                raw_data=data
            )
            logger.info("    VideoInfo对象创建完成")
            
            logger.info(f"成功解析视频: {description} - {author_nickname}")
            return video_info
            
        except Exception as e:
            logger.error(f"解析视频数据时出错: {e}")
            return VideoInfo()
    
    def search_videos(self, keyword: str, page: int = 1, limit: int = 10) -> list[VideoInfo]:
        """搜索抖音视频"""
        try:
            api_url = f"{self.base_url}/api/douyin/search"
            params = {
                'keyword': keyword,
                'page': page,
                'limit': limit
            }
            
            logger.info(f"搜索抖音视频: {keyword}")
            response = self.session.get(api_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('code') != 200:
                logger.error(f"搜索API返回错误: {data.get('message', '未知错误')}")
                return []
            
            # 解析搜索结果
            videos = []
            results = data.get('data', {}).get('videos', [])
            
            for video_data in results:
                video_info = self._parse_video_data(video_data, '')
                if video_info.is_valid:
                    videos.append(video_info)
            
            logger.info(f"搜索到 {len(videos)} 个视频")
            return videos
            
        except requests.exceptions.RequestException as e:
            logger.error(f"搜索请求失败: {e}")
            return []
        except Exception as e:
            logger.error(f"搜索视频时出错: {e}")
            return []
    
    def validate_audio_url(self, audio_url: str) -> bool:
        """验证音频URL是否有效"""
        try:
            if not audio_url:
                return False
            
            response = self.session.head(audio_url, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"验证音频URL失败: {e}")
            return False
    
    def get_audio_stream_url(self, video_info: VideoInfo) -> Optional[str]:
        """获取音频流URL"""
        if not video_info.audio_url:
            return None
        
        # 验证音频URL
        if self.validate_audio_url(video_info.audio_url):
            return video_info.audio_url
        
        # 如果原始URL无效，尝试获取新的音频URL
        try:
            api_url = f"{self.base_url}/api/douyin/audio"
            params = {
                'video_id': video_info.video_id
            }
            
            response = self.session.get(api_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('code') == 200:
                audio_url = data.get('data', {}).get('audio_url', '')
                if audio_url and self.validate_audio_url(audio_url):
                    return audio_url
            
            return None
            
        except Exception as e:
            logger.error(f"获取音频流URL失败: {e}")
            return None
    
    def _create_mock_video_info(self, url: str, video_id: str) -> VideoInfo:
        """创建模拟视频信息用于测试"""
        return VideoInfo(
            title=f"测试视频 - {video_id}",
            author="测试作者",
            author_id="test_author",
            video_id=video_id,
            cover_url="https://via.placeholder.com/300x400/FF6B6B/FFFFFF?text=Test+Video",
            audio_url="https://www.soundjay.com/misc/sounds/bell-ringing-05.wav",  # 测试音频
            video_url=url,
            duration=30,
            play_count=1000,
            like_count=100,
            comment_count=50,
            share_count=20,
            description="这是一个测试视频，用于演示机器人功能",
            tags=["测试", "演示"],
            raw_data={"mock": True, "url": url, "video_id": video_id}
        )


# 创建全局API实例
douyin_api = DouyinAPI()
