"""
视频信息模型
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

@dataclass
class VideoInfo:
    """视频信息数据类"""
    
    # 基本信息
    title: str = ""
    author: str = ""
    author_id: str = ""
    video_id: str = ""
    
    # 媒体信息
    cover_url: str = ""
    cover_urls: list = None  # 多个封面链接
    audio_url: str = ""
    video_url: str = ""
    duration: int = 0  # 秒
    
    # Kook上传后的链接
    kook_video_url: str = ""
    kook_cover_url: str = ""
    
    # 统计信息
    play_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    
    # 其他信息
    description: str = ""
    tags: list = None
    create_time: Optional[datetime] = None
    
    # 原始数据
    raw_data: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.cover_urls is None:
            self.cover_urls = []
    
    @property
    def duration_str(self) -> str:
        """格式化时长"""
        if self.duration <= 0:
            return "未知"
        
        minutes = self.duration // 60
        seconds = self.duration % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    @property
    def is_valid(self) -> bool:
        """检查视频信息是否有效"""
        return bool(self.video_id and self.title)
    
    def get_available_cover_urls(self) -> list:
        """获取所有可用的封面链接"""
        urls = []
        if self.cover_url:
            urls.append(self.cover_url)
        if self.cover_urls:
            urls.extend(self.cover_urls)
        # 去重并过滤空字符串
        return list(set([url for url in urls if url.strip()]))
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'title': self.title,
            'author': self.author,
            'author_id': self.author_id,
            'video_id': self.video_id,
            'cover_url': self.cover_url,
            'audio_url': self.audio_url,
            'video_url': self.video_url,
            'kook_video_url': self.kook_video_url,
            'kook_cover_url': self.kook_cover_url,
            'duration': self.duration,
            'duration_str': self.duration_str,
            'play_count': self.play_count,
            'like_count': self.like_count,
            'comment_count': self.comment_count,
            'share_count': self.share_count,
            'description': self.description,
            'tags': self.tags,
            'create_time': self.create_time.isoformat() if self.create_time else None,
            'is_valid': self.is_valid
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VideoInfo':
        """从字典创建实例"""
        return cls(
            title=data.get('title', ''),
            author=data.get('author', ''),
            author_id=data.get('author_id', ''),
            video_id=data.get('video_id', ''),
            cover_url=data.get('cover_url', ''),
            audio_url=data.get('audio_url', ''),
            video_url=data.get('video_url', ''),
            kook_video_url=data.get('kook_video_url', ''),
            kook_cover_url=data.get('kook_cover_url', ''),
            duration=data.get('duration', 0),
            play_count=data.get('play_count', 0),
            like_count=data.get('like_count', 0),
            comment_count=data.get('comment_count', 0),
            share_count=data.get('share_count', 0),
            description=data.get('description', ''),
            tags=data.get('tags', []),
            create_time=datetime.fromisoformat(data['create_time']) if data.get('create_time') else None,
            raw_data=data.get('raw_data')
        )
