"""
配置文件
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Settings:
    """配置类"""
    
    # Kook机器人配置
    BOT_TOKEN = os.getenv('BOT_TOKEN', '')
    
    # 抖音解析API配置
    DOUYIN_API_BASE = os.getenv('DOUYIN_API_BASE', 'https://dy.chixiaotao.cn')
    
    # FFmpeg配置
    FFMPEG_PATH = os.getenv('FFMPEG_PATH', 'ffmpeg')
    FFPROBE_PATH = os.getenv('FFPROBE_PATH', 'ffprobe')
    
    # 日志配置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/bot.log')
    
    # 其他配置
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    MAX_QUEUE_SIZE = int(os.getenv('MAX_QUEUE_SIZE', '50'))
    
    @classmethod
    def validate(cls):
        """验证配置"""
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN 未设置")
        return True

# 创建全局配置实例
settings = Settings()
