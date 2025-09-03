"""
播放器状态模型
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime
from .video import VideoInfo

class PlayerStatus(Enum):
    """播放器状态枚举"""
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    LOADING = "loading"
    ERROR = "error"

@dataclass
class PlayerState:
    """播放器状态数据类"""
    
    # 基本信息
    guild_id: str = ""
    channel_id: str = ""
    user_id: str = ""
    
    # 播放状态
    status: PlayerStatus = PlayerStatus.STOPPED
    current_video: Optional[VideoInfo] = None
    current_position: int = 0  # 当前播放位置（秒）
    volume: int = 50  # 音量 0-100
    
    # 队列管理
    queue: List[VideoInfo] = field(default_factory=list)
    queue_position: int = 0  # 当前队列位置
    
    # 时间信息
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # 其他信息
    loop_mode: bool = False  # 循环播放
    shuffle_mode: bool = False  # 随机播放
    error_message: str = ""
    
    @property
    def is_playing(self) -> bool:
        """是否正在播放"""
        return self.status == PlayerStatus.PLAYING
    
    @property
    def is_paused(self) -> bool:
        """是否暂停"""
        return self.status == PlayerStatus.PAUSED
    
    @property
    def is_stopped(self) -> bool:
        """是否停止"""
        return self.status == PlayerStatus.STOPPED
    
    @property
    def has_queue(self) -> bool:
        """是否有队列"""
        return len(self.queue) > 0
    
    @property
    def queue_size(self) -> int:
        """队列大小"""
        return len(self.queue)
    
    @property
    def current_position_str(self) -> str:
        """格式化当前播放位置"""
        if self.current_position <= 0:
            return "00:00"
        
        minutes = self.current_position // 60
        seconds = self.current_position % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    @property
    def progress_percentage(self) -> float:
        """播放进度百分比"""
        if not self.current_video or self.current_video.duration <= 0:
            return 0.0
        
        return min(100.0, (self.current_position / self.current_video.duration) * 100)
    
    def add_to_queue(self, video: VideoInfo) -> bool:
        """添加视频到队列"""
        if not video.is_valid:
            return False
        
        self.queue.append(video)
        self.updated_at = datetime.now()
        return True
    
    def remove_from_queue(self, index: int) -> Optional[VideoInfo]:
        """从队列中移除视频"""
        if 0 <= index < len(self.queue):
            video = self.queue.pop(index)
            self.updated_at = datetime.now()
            
            # 调整队列位置
            if index < self.queue_position:
                self.queue_position -= 1
            elif index == self.queue_position and self.queue_position >= len(self.queue):
                self.queue_position = max(0, len(self.queue) - 1)
            
            return video
        return None
    
    def clear_queue(self):
        """清空队列"""
        self.queue.clear()
        self.queue_position = 0
        self.updated_at = datetime.now()
    
    def next_video(self) -> Optional[VideoInfo]:
        """获取下一个视频"""
        if not self.has_queue:
            return None
        
        if self.shuffle_mode:
            # 随机播放模式
            import random
            if len(self.queue) > 1:
                available_indices = [i for i in range(len(self.queue)) if i != self.queue_position]
                self.queue_position = random.choice(available_indices)
        else:
            # 顺序播放模式
            if self.loop_mode:
                self.queue_position = (self.queue_position + 1) % len(self.queue)
            else:
                self.queue_position += 1
                if self.queue_position >= len(self.queue):
                    return None
        
        if 0 <= self.queue_position < len(self.queue):
            return self.queue[self.queue_position]
        return None
    
    def previous_video(self) -> Optional[VideoInfo]:
        """获取上一个视频"""
        if not self.has_queue:
            return None
        
        if self.shuffle_mode:
            # 随机播放模式不支持上一首
            return None
        
        if self.loop_mode:
            self.queue_position = (self.queue_position - 1) % len(self.queue)
        else:
            self.queue_position -= 1
            if self.queue_position < 0:
                return None
        
        if 0 <= self.queue_position < len(self.queue):
            return self.queue[self.queue_position]
        return None
    
    def get_current_video(self) -> Optional[VideoInfo]:
        """获取当前播放的视频"""
        if 0 <= self.queue_position < len(self.queue):
            return self.queue[self.queue_position]
        return None
    
    def set_status(self, status: PlayerStatus, error_message: str = ""):
        """设置播放状态"""
        self.status = status
        self.error_message = error_message
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'guild_id': self.guild_id,
            'channel_id': self.channel_id,
            'user_id': self.user_id,
            'status': self.status.value,
            'current_video': self.current_video.to_dict() if self.current_video else None,
            'current_position': self.current_position,
            'current_position_str': self.current_position_str,
            'progress_percentage': self.progress_percentage,
            'volume': self.volume,
            'queue': [video.to_dict() for video in self.queue],
            'queue_position': self.queue_position,
            'queue_size': self.queue_size,
            'loop_mode': self.loop_mode,
            'shuffle_mode': self.shuffle_mode,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
