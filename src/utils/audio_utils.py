"""
音频处理工具
"""
import os
import asyncio
import subprocess
import tempfile
from typing import Optional, Dict, Any
from pathlib import Path
from loguru import logger

from pydub import AudioSegment
from pydub.utils import which

from config.settings import settings


class AudioProcessor:
    """音频处理器"""
    
    def __init__(self):
        self.ffmpeg_path = settings.FFMPEG_PATH
        self.ffprobe_path = settings.FFPROBE_PATH
        self.temp_dir = Path(tempfile.gettempdir()) / "kook_dy_bot"
        self.temp_dir.mkdir(exist_ok=True)
        
        # 验证FFmpeg是否可用
        self._check_ffmpeg()
    
    def _check_ffmpeg(self):
        """检查FFmpeg是否可用"""
        try:
            # 检查ffmpeg
            ffmpeg_cmd = which(self.ffmpeg_path)
            if not ffmpeg_cmd:
                logger.warning(f"FFmpeg not found at {self.ffmpeg_path}")
                return False
            
            # 检查ffprobe
            ffprobe_cmd = which(self.ffprobe_path)
            if not ffprobe_cmd:
                logger.warning(f"FFprobe not found at {self.ffprobe_path}")
                return False
            
            logger.info(f"FFmpeg found: {ffmpeg_cmd}")
            logger.info(f"FFprobe found: {ffprobe_cmd}")
            return True
            
        except Exception as e:
            logger.error(f"检查FFmpeg时出错: {e}")
            return False
    
    async def download_audio(self, audio_url: str, output_path: Optional[str] = None) -> Optional[str]:
        """下载音频文件"""
        try:
            if not output_path:
                # 生成临时文件路径
                output_path = self.temp_dir / f"audio_{hash(audio_url)}.mp3"
            
            # 使用FFmpeg下载音频
            cmd = [
                self.ffmpeg_path,
                '-i', audio_url,
                '-vn',  # 不处理视频
                '-acodec', 'mp3',  # 输出MP3格式
                '-ab', '128k',  # 音频比特率
                '-ar', '44100',  # 采样率
                '-y',  # 覆盖输出文件
                str(output_path)
            ]
            
            logger.info(f"下载音频: {audio_url}")
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"音频下载成功: {output_path}")
                return str(output_path)
            else:
                logger.error(f"音频下载失败: {stderr.decode()}")
                return None
                
        except Exception as e:
            logger.error(f"下载音频时出错: {e}")
            return None
    
    async def get_audio_info(self, audio_path: str) -> Optional[Dict[str, Any]]:
        """获取音频文件信息"""
        try:
            cmd = [
                self.ffprobe_path,
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                audio_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                import json
                info = json.loads(stdout.decode())
                
                # 提取音频信息
                format_info = info.get('format', {})
                duration = float(format_info.get('duration', 0))
                bitrate = int(format_info.get('bit_rate', 0))
                
                # 查找音频流
                audio_stream = None
                for stream in info.get('streams', []):
                    if stream.get('codec_type') == 'audio':
                        audio_stream = stream
                        break
                
                if audio_stream:
                    sample_rate = int(audio_stream.get('sample_rate', 0))
                    channels = int(audio_stream.get('channels', 0))
                    codec = audio_stream.get('codec_name', '')
                else:
                    sample_rate = 0
                    channels = 0
                    codec = ''
                
                return {
                    'duration': duration,
                    'bitrate': bitrate,
                    'sample_rate': sample_rate,
                    'channels': channels,
                    'codec': codec,
                    'size': os.path.getsize(audio_path)
                }
            else:
                logger.error(f"获取音频信息失败: {stderr.decode()}")
                return None
                
        except Exception as e:
            logger.error(f"获取音频信息时出错: {e}")
            return None
    
    async def convert_audio(self, input_path: str, output_path: str, 
                          format: str = 'mp3', bitrate: str = '128k') -> bool:
        """转换音频格式"""
        try:
            cmd = [
                self.ffmpeg_path,
                '-i', input_path,
                '-acodec', format,
                '-ab', bitrate,
                '-ar', '44100',
                '-y',
                output_path
            ]
            
            logger.info(f"转换音频: {input_path} -> {output_path}")
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"音频转换成功: {output_path}")
                return True
            else:
                logger.error(f"音频转换失败: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"转换音频时出错: {e}")
            return False
    
    async def trim_audio(self, input_path: str, output_path: str, 
                        start_time: float, duration: float) -> bool:
        """裁剪音频"""
        try:
            cmd = [
                self.ffmpeg_path,
                '-i', input_path,
                '-ss', str(start_time),
                '-t', str(duration),
                '-acodec', 'copy',
                '-y',
                output_path
            ]
            
            logger.info(f"裁剪音频: {input_path} ({start_time}s-{duration}s)")
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"音频裁剪成功: {output_path}")
                return True
            else:
                logger.error(f"音频裁剪失败: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"裁剪音频时出错: {e}")
            return False
    
    async def adjust_volume(self, input_path: str, output_path: str, 
                           volume_change: float) -> bool:
        """调整音频音量"""
        try:
            # volume_change: 正数增加音量，负数减少音量
            # 例如: 0.5 表示增加50%音量，-0.5 表示减少50%音量
            volume_filter = f"volume={1 + volume_change}"
            
            cmd = [
                self.ffmpeg_path,
                '-i', input_path,
                '-af', volume_filter,
                '-y',
                output_path
            ]
            
            logger.info(f"调整音量: {input_path} (变化: {volume_change})")
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"音量调整成功: {output_path}")
                return True
            else:
                logger.error(f"音量调整失败: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"调整音量时出错: {e}")
            return False
    
    def cleanup_temp_file(self, file_path: str):
        """清理临时文件"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"清理临时文件: {file_path}")
        except Exception as e:
            logger.error(f"清理临时文件失败: {e}")
    
    def cleanup_temp_dir(self):
        """清理临时目录"""
        try:
            for file_path in self.temp_dir.glob("*"):
                if file_path.is_file():
                    file_path.unlink()
            logger.info("清理临时目录完成")
        except Exception as e:
            logger.error(f"清理临时目录失败: {e}")
    
    async def validate_audio_file(self, file_path: str) -> bool:
        """验证音频文件是否有效"""
        try:
            if not os.path.exists(file_path):
                return False
            
            # 尝试获取音频信息
            info = await self.get_audio_info(file_path)
            return info is not None
            
        except Exception as e:
            logger.error(f"验证音频文件失败: {e}")
            return False


class AudioStreamer:
    """音频流处理器"""
    
    def __init__(self, audio_processor: AudioProcessor):
        self.audio_processor = audio_processor
        self.active_streams: Dict[str, Any] = {}
    
    async def create_stream(self, audio_url: str, stream_id: str) -> Optional[str]:
        """创建音频流"""
        try:
            # 下载音频文件
            audio_path = await self.audio_processor.download_audio(audio_url)
            if not audio_path:
                return None
            
            # 验证音频文件
            if not await self.audio_processor.validate_audio_file(audio_path):
                self.audio_processor.cleanup_temp_file(audio_path)
                return None
            
            # 存储流信息
            self.active_streams[stream_id] = {
                'audio_path': audio_path,
                'audio_url': audio_url,
                'created_at': asyncio.get_event_loop().time()
            }
            
            logger.info(f"创建音频流: {stream_id}")
            return audio_path
            
        except Exception as e:
            logger.error(f"创建音频流失败: {e}")
            return None
    
    async def get_stream(self, stream_id: str) -> Optional[str]:
        """获取音频流路径"""
        stream_info = self.active_streams.get(stream_id)
        if stream_info:
            return stream_info['audio_path']
        return None
    
    async def cleanup_stream(self, stream_id: str):
        """清理音频流"""
        try:
            stream_info = self.active_streams.get(stream_id)
            if stream_info:
                audio_path = stream_info['audio_path']
                self.audio_processor.cleanup_temp_file(audio_path)
                del self.active_streams[stream_id]
                logger.info(f"清理音频流: {stream_id}")
        except Exception as e:
            logger.error(f"清理音频流失败: {e}")
    
    async def cleanup_expired_streams(self, max_age: int = 3600):
        """清理过期的音频流"""
        try:
            current_time = asyncio.get_event_loop().time()
            expired_streams = []
            
            for stream_id, stream_info in self.active_streams.items():
                age = current_time - stream_info['created_at']
                if age > max_age:
                    expired_streams.append(stream_id)
            
            for stream_id in expired_streams:
                await self.cleanup_stream(stream_id)
            
            if expired_streams:
                logger.info(f"清理了 {len(expired_streams)} 个过期音频流")
                
        except Exception as e:
            logger.error(f"清理过期音频流失败: {e}")


# 创建全局实例
audio_processor = AudioProcessor()
audio_streamer = AudioStreamer(audio_processor)
