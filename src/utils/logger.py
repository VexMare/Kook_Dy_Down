"""
日志工具
"""
import os
import sys
from pathlib import Path
from loguru import logger
from typing import Optional

from config.settings import settings


class Logger:
    """日志管理器"""
    
    def __init__(self):
        self.log_level = settings.LOG_LEVEL
        self.log_file = settings.LOG_FILE
        self.debug = settings.DEBUG
        
        # 创建日志目录
        self._create_log_dir()
        
        # 配置日志
        self._setup_logger()
    
    def _create_log_dir(self):
        """创建日志目录"""
        log_path = Path(self.log_file)
        log_dir = log_path.parent
        log_dir.mkdir(parents=True, exist_ok=True)
    
    def _setup_logger(self):
        """设置日志配置"""
        # 移除默认处理器
        logger.remove()
        
        # 控制台输出
        console_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
        
        logger.add(
            sys.stdout,
            format=console_format,
            level=self.log_level,
            colorize=True,
            backtrace=True,
            diagnose=self.debug
        )
        
        # 文件输出 - 所有日志
        file_format = (
            "{time:YYYY-MM-DD HH:mm:ss} | "
            "{level: <8} | "
            "{name}:{function}:{line} | "
            "{message}"
        )
        
        logger.add(
            self.log_file,
            format=file_format,
            level="DEBUG",
            rotation="10 MB",
            retention="7 days",
            compression="zip",
            backtrace=True,
            diagnose=self.debug
        )
        
        # 错误日志单独文件
        error_log_file = str(Path(self.log_file).parent / "error.log")
        logger.add(
            error_log_file,
            format=file_format,
            level="ERROR",
            rotation="5 MB",
            retention="30 days",
            compression="zip",
            backtrace=True,
            diagnose=True
        )
        
        # 访问日志
        access_log_file = str(Path(self.log_file).parent / "access.log")
        logger.add(
            access_log_file,
            format=file_format,
            level="INFO",
            rotation="10 MB",
            retention="3 days",
            compression="zip",
            filter=lambda record: "access" in record["extra"]
        )
    
    def get_logger(self, name: Optional[str] = None):
        """获取日志记录器"""
        if name:
            return logger.bind(name=name)
        return logger
    
    def log_access(self, message: str, **kwargs):
        """记录访问日志"""
        logger.bind(access=True).info(message, **kwargs)
    
    def log_error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """记录错误日志"""
        if exception:
            logger.exception(message, **kwargs)
        else:
            logger.error(message, **kwargs)
    
    def log_warning(self, message: str, **kwargs):
        """记录警告日志"""
        logger.warning(message, **kwargs)
    
    def log_info(self, message: str, **kwargs):
        """记录信息日志"""
        logger.info(message, **kwargs)
    
    def log_debug(self, message: str, **kwargs):
        """记录调试日志"""
        logger.debug(message, **kwargs)


class BotLogger:
    """机器人专用日志记录器"""
    
    def __init__(self, logger_instance: Logger):
        self.logger = logger_instance.get_logger("bot")
    
    def log_command(self, user_id: str, command: str, args: str = "", guild_id: str = "", channel_id: str = ""):
        """记录命令执行"""
        self.logger.info(
            f"命令执行: {command}",
            extra={
                "user_id": user_id,
                "command": command,
                "args": args,
                "guild_id": guild_id,
                "channel_id": channel_id,
                "access": True
            }
        )
    
    def log_api_call(self, api_name: str, url: str, status_code: int, response_time: float):
        """记录API调用"""
        self.logger.info(
            f"API调用: {api_name}",
            extra={
                "api_name": api_name,
                "url": url,
                "status_code": status_code,
                "response_time": response_time,
                "access": True
            }
        )
    
    def log_audio_play(self, user_id: str, video_id: str, video_title: str, guild_id: str, channel_id: str):
        """记录音频播放"""
        self.logger.info(
            f"音频播放: {video_title}",
            extra={
                "user_id": user_id,
                "video_id": video_id,
                "video_title": video_title,
                "guild_id": guild_id,
                "channel_id": channel_id,
                "access": True
            }
        )
    
    def log_queue_operation(self, user_id: str, operation: str, queue_size: int, guild_id: str):
        """记录队列操作"""
        self.logger.info(
            f"队列操作: {operation}",
            extra={
                "user_id": user_id,
                "operation": operation,
                "queue_size": queue_size,
                "guild_id": guild_id,
                "access": True
            }
        )
    
    def log_error(self, error_type: str, message: str, user_id: str = "", guild_id: str = "", exception: Optional[Exception] = None):
        """记录错误"""
        if exception:
            self.logger.exception(
                f"错误 [{error_type}]: {message}",
                extra={
                    "error_type": error_type,
                    "user_id": user_id,
                    "guild_id": guild_id
                }
            )
        else:
            self.logger.error(
                f"错误 [{error_type}]: {message}",
                extra={
                    "error_type": error_type,
                    "user_id": user_id,
                    "guild_id": guild_id
                }
            )


class APILogger:
    """API专用日志记录器"""
    
    def __init__(self, logger_instance: Logger):
        self.logger = logger_instance.get_logger("api")
    
    def log_request(self, method: str, url: str, params: dict = None, headers: dict = None):
        """记录请求"""
        self.logger.debug(
            f"API请求: {method} {url}",
            extra={
                "method": method,
                "url": url,
                "params": params,
                "headers": headers
            }
        )
    
    def log_response(self, method: str, url: str, status_code: int, response_time: float, response_size: int = 0):
        """记录响应"""
        self.logger.info(
            f"API响应: {method} {url} - {status_code} ({response_time:.2f}s)",
            extra={
                "method": method,
                "url": url,
                "status_code": status_code,
                "response_time": response_time,
                "response_size": response_size,
                "access": True
            }
        )
    
    def log_error(self, method: str, url: str, error: str, status_code: int = None):
        """记录API错误"""
        self.logger.error(
            f"API错误: {method} {url} - {error}",
            extra={
                "method": method,
                "url": url,
                "error": error,
                "status_code": status_code
            }
        )


class AudioLogger:
    """音频处理专用日志记录器"""
    
    def __init__(self, logger_instance: Logger):
        self.logger = logger_instance.get_logger("audio")
    
    def log_download(self, url: str, file_path: str, file_size: int, duration: float):
        """记录音频下载"""
        self.logger.info(
            f"音频下载: {file_path}",
            extra={
                "url": url,
                "file_path": file_path,
                "file_size": file_size,
                "duration": duration,
                "access": True
            }
        )
    
    def log_conversion(self, input_path: str, output_path: str, format: str, success: bool):
        """记录音频转换"""
        status = "成功" if success else "失败"
        self.logger.info(
            f"音频转换: {input_path} -> {output_path} ({format}) - {status}",
            extra={
                "input_path": input_path,
                "output_path": output_path,
                "format": format,
                "success": success,
                "access": True
            }
        )
    
    def log_playback(self, file_path: str, duration: float, position: float, volume: int):
        """记录音频播放"""
        self.logger.debug(
            f"音频播放: {file_path} - {position:.1f}s/{duration:.1f}s (音量: {volume}%)",
            extra={
                "file_path": file_path,
                "duration": duration,
                "position": position,
                "volume": volume
            }
        )
    
    def log_error(self, operation: str, error: str, file_path: str = ""):
        """记录音频处理错误"""
        self.logger.error(
            f"音频处理错误 [{operation}]: {error}",
            extra={
                "operation": operation,
                "error": error,
                "file_path": file_path
            }
        )


# 创建全局日志实例
app_logger = Logger()
bot_logger = BotLogger(app_logger)
api_logger = APILogger(app_logger)
audio_logger = AudioLogger(app_logger)

# 导出主要日志记录器
logger = app_logger.get_logger()
