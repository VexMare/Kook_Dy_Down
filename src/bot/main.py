"""
机器人主程序
"""
import asyncio
import signal
import sys
from typing import Dict, Any, Optional
from loguru import logger

import khl
from khl import Bot, Message
from khl.card import CardMessage

from src.api.douyin_api import douyin_api
from src.api.kook_api import KookAPI
from src.models.video import VideoInfo
from src.models.player import PlayerState, PlayerStatus

from src.utils.link_parser import link_validator
from src.utils.logger import bot_logger
from config.settings import settings


class DouyinBot:
    """抖音音乐机器人"""
    
    def __init__(self):
        # 检查是否已经有实例在运行
        if hasattr(DouyinBot, '_instance'):
            logger.warning("检测到重复的机器人实例创建，这可能导致重复执行")
            raise RuntimeError("机器人实例已经存在，请勿重复创建")
        
        # 标记实例已创建
        DouyinBot._instance = self
        
        # 初始化机器人
        self.bot = Bot(token=settings.BOT_TOKEN)
        self.kook_api = KookAPI(self.bot)
        
        # 播放器状态管理
        self.player_states: Dict[str, PlayerState] = {}  # guild_id -> PlayerState
        
        # 消息去重机制
        self.processed_messages: set = set()  # 存储已处理的消息ID
        self.message_lock = asyncio.Lock()  # 消息处理锁
        self.last_message_id = None  # 上一个处理的消息ID
        self.last_message_time = 0  # 上一个处理消息的时间戳
        self.is_processing = False  # 是否正在处理消息
        
        # 注册命令和事件
        self._register_commands()
        self._register_events()
        
        # 设置信号处理
        self._setup_signal_handlers()
        
        # 注册消息事件监听器
        self._register_message_events()
        
        logger.info("抖音音乐机器人初始化完成")
    
    def _get_random_headers(self, content_type='video'):
        """生成随机请求头"""
        import random
        
        # 随机User-Agent列表
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:119.0) Gecko/20100101 Firefox/119.0',
            'Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (X11; Linux x86_64; rv:119.0) Gecko/20100101 Firefox/119.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/119.0.0.0 Safari/537.36'
        ]
        
        # 随机Accept-Language
        accept_languages = [
            'zh-CN,zh;q=0.9,en;q=0.8',
            'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
            'en-US,en;q=0.5'
        ]
        
        # 基础请求头
        headers = {
            'User-Agent': random.choice(user_agents),
            'Accept-Language': random.choice(accept_languages),
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.douyin.com/',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        
        # 根据内容类型添加特定的Accept头
        if content_type == 'video':
            headers['Accept'] = random.choice([
                'video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5',
                'video/mp4,video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5',
                '*/*'
            ])
            headers['Range'] = 'bytes=0-'
        elif content_type == 'image':
            headers['Accept'] = random.choice([
                'image/webp,image/apng,image/*,*/*;q=0.8',
                'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'image/*,*/*;q=0.8'
            ])
        
        return headers
    
    def _register_commands(self):
        """注册命令"""
        # 移除dy命令，改为自动检测抖音链接
        pass
        

        

        

        

        

        

        
        @self.bot.command(name='dyqueue', aliases=['队列'])
        async def dyqueue_command(msg: Message):
            """查看播放队列"""
            await self._handle_dyqueue_command(msg)
        
        @self.bot.command(name='dynow', aliases=['当前'])
        async def dynow_command(msg: Message):
            """显示当前播放信息"""
            await self._handle_dynow_command(msg)
        
        @self.bot.command(name='dyclear', aliases=['清空'])
        async def dyclear_command(msg: Message):
            """清空播放队列"""
            await self._handle_dyclear_command(msg)
        
        @self.bot.command(name='dysearch', aliases=['搜索'])
        async def dysearch_command(msg: Message, keyword: str = ""):
            """搜索抖音视频"""
            await self._handle_dysearch_command(msg, keyword)
        
        @self.bot.command(name='dyvolume', aliases=['音量'])
        async def dyvolume_command(msg: Message, volume: int = 50):
            """调整音量"""
            await self._handle_dyvolume_command(msg, volume)
        
        @self.bot.command(name='dyhelp', aliases=['帮助'])
        async def dyhelp_command(msg: Message):
            """显示帮助信息"""
            await self._handle_dyhelp_command(msg)
        
        @self.bot.command(name='dystatus', aliases=['状态'])
        async def dystatus_command(msg: Message):
            """显示机器人状态"""
            await self._handle_dystatus_command(msg)
        
        @self.bot.command(name='dyversion', aliases=['版本'])
        async def dyversion_command(msg: Message):
            """显示版本信息"""
            await self._handle_dyversion_command(msg)
        
        @self.bot.command(name='dyupload', aliases=['上传帮助'])
        async def dyupload_command(msg: Message):
            """视频上传帮助"""
            await self._handle_dyupload_command(msg)
        
        @self.bot.command(name='testcard', aliases=['测试卡片'])
        async def testcard_command(msg: Message):
            """测试卡片发送"""
            await self._handle_test_card_command(msg)
        
        @self.bot.command(name='testimage', aliases=['测试图片'])
        async def testimage_command(msg: Message):
            """测试图片卡片发送"""
            await self._handle_test_image_command(msg)
        

        
        @self.bot.command(name='dyfetch', aliases=['获取视频'])
        async def dyfetch_command(msg: Message, url: str = ""):
            """获取并上传视频"""
            await self._handle_dyfetch_command(msg, url)
    
    def _register_events(self):
        """注册事件处理器"""
        
        @self.bot.on_event('card_message')
        async def on_card_message(msg: Message):
            """卡片消息事件处理"""
            await self._handle_card_interaction(msg)
    
    def _setup_signal_handlers(self):
        """设置信号处理器"""
        def signal_handler(signum, frame):
            logger.info(f"收到信号 {signum}，强制退出程序...")
            # 直接强制退出，不进行优雅关闭
            import os
            os._exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def _register_message_events(self):
        """注册消息事件监听器"""
        @self.bot.on_message()
        async def on_message(msg: Message):
            """监听所有消息，分析视频内容"""
            # 使用全局标志防止重复处理
            if self.is_processing:
                logger.warning(f"正在处理其他消息，跳过消息 {msg.id}")
                return
            
            # 立即标记为正在处理
            self.is_processing = True
            logger.info(f"开始处理消息: ID={msg.id}, 内容={msg.content[:50] if msg.content else 'None'}")
            
            try:
                # 记录消息日志
                bot_logger.log_command(
                    user_id=msg.author.id,
                    command="message",
                    args=msg.content[:100] if msg.content else "",
                    guild_id=msg.ctx.guild.id if msg.ctx.guild else "",
                    channel_id=msg.ctx.channel.id
                )
                
                # 检查消息是否包含附件
                if hasattr(msg, 'attachments') and msg.attachments:
                    logger.info(f"消息包含 {len(msg.attachments)} 个附件")
                    for i, attachment in enumerate(msg.attachments):
                        logger.info(f"附件 {i+1}: 类型={attachment.type}, URL={attachment.url}")
                        if attachment.type == 'video':
                            logger.info(f"检测到视频消息: {attachment.url}")
                            await self._analyze_video_message(msg, attachment)
                        elif attachment.type == 'image':
                            logger.info(f"检测到图片消息: {attachment.url}")
                        else:
                            logger.info(f"检测到其他类型附件: {attachment.type}")
                
                # 检查消息内容是否包含视频链接
                if msg.content:
                    logger.info(f"消息内容: {msg.content}")
                    
                    # 检查是否是卡片消息（包含视频）
                    if msg.content.startswith('[') and '"type":"card"' in msg.content:
                        logger.info("检测到卡片消息，尝试解析视频信息")
                        await self._analyze_card_message(msg)
                    
                    # 检查是否包含抖音链接
                    import re
                    # 更精确的抖音链接匹配，处理Markdown格式，支持连字符和下划线
                    douyin_pattern = r'https?://(?:v\.)?douyin\.com/[A-Za-z0-9\-_]+/?'
                    matches = re.findall(douyin_pattern, msg.content)
                    if matches:
                        # 去重处理，避免重复处理相同的链接
                        unique_matches = list(set(matches))
                        logger.info(f"找到 {len(matches)} 个抖音链接，去重后 {len(unique_matches)} 个: {unique_matches}")
                        for i, url in enumerate(unique_matches):
                            # 清理URL，移除可能的Markdown格式
                            clean_url = url.strip()
                            # 移除Markdown链接格式中的括号
                            if clean_url.endswith(')'):
                                clean_url = clean_url.rstrip(')')
                            # 移除可能的查询参数和片段
                            if '?' in clean_url:
                                clean_url = clean_url.split('?')[0]
                            if '#' in clean_url:
                                clean_url = clean_url.split('#')[0]
                            logger.info(f"处理第 {i+1} 个抖音链接: {clean_url}")
                            # 使用dy命令的处理逻辑，下载视频并上传到Kook
                            await self._handle_dy_command(msg, clean_url)
                    
                    # 检查是否包含视频文件链接
                    video_pattern = r'https?://[^\s]+\.(?:mp4|avi|mov|wmv|flv|webm|mkv)'
                    video_matches = re.findall(video_pattern, msg.content)
                    if video_matches:
                        for url in video_matches:
                            logger.info(f"检测到视频文件链接: {url}")
                            await self._analyze_video_link(msg, url)
                else:
                    logger.info("消息无文本内容")
                
                # 处理完成
                logger.info(f"消息 {msg.id} 处理完成")
                            
            except Exception as e:
                logger.error(f"分析消息时出错: {e}")
                import traceback
                logger.error(f"错误详情: {traceback.format_exc()}")
            finally:
                # 重置处理标志
                self.is_processing = False
                logger.info(f"重置处理标志，消息 {msg.id} 处理结束")
    
    async def _analyze_card_message(self, msg):
        """分析卡片消息中的视频"""
        try:
            import json
            
            # 解析卡片消息内容
            card_data = json.loads(msg.content)
            logger.info(f"卡片消息解析成功: {len(card_data)} 个卡片")
            
            for card in card_data:
                if 'modules' in card:
                    for module in card['modules']:
                        if module.get('type') == 'video':
                            logger.info(f"检测到视频模块:")
                            logger.info(f"  标题: {module.get('title', '未知')}")
                            logger.info(f"  视频URL: {module.get('src', '未知')}")
                            logger.info(f"  封面URL: {module.get('cover', '未知')}")
                            logger.info(f"  时长: {module.get('duration', '未知')} 秒")
                            logger.info(f"  文件大小: {module.get('size', '未知')} 字节")
                            logger.info(f"  尺寸: {module.get('width', '未知')}x{module.get('height', '未知')}")
                            
                            # 发送分析结果
                            analysis_text = f"""📹 **视频卡片分析**

👤 **发送者**: {msg.author.username}
📺 **频道**: {msg.ctx.channel.name}

📹 **视频信息**:
🎬 标题: {module.get('title', '未知')}
🔗 视频URL: {module.get('src', '未知')}
🖼️ 封面: {module.get('cover', '未知')}
⏱️ 时长: {module.get('duration', '未知')} 秒
📏 尺寸: {module.get('width', '未知')}x{module.get('height', '未知')}
💾 文件大小: {self._format_file_size(module.get('size', 0))}
📥 可下载: {'是' if module.get('canDownload') else '否'}

🎯 **操作建议**:
- 这是一个视频文件，可以直接播放
- 视频已上传到Kook服务器 (使用 /api/v3/asset/create)
- 如果需要提取音频，可以使用音频处理工具
- 视频格式: MP4 (Kook支持 .mp4 .mov 格式)

🔧 **技术信息**:
- 使用Kook媒体上传API: /api/v3/asset/create
- 支持格式: 图片, 视频(.mp4 .mov), 文件
- 上传方式: POST form-data"""

                            await msg.ctx.channel.send(analysis_text)
                            
        except Exception as e:
            logger.error(f"分析卡片消息失败: {e}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
    
    def _format_file_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes == 0:
            return "未知"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    async def _analyze_video_message(self, msg, attachment):
        """分析视频消息"""
        try:
            logger.info(f"视频消息分析:")
            logger.info(f"  用户: {msg.author.username}")
            logger.info(f"  频道: {msg.ctx.channel.name}")
            logger.info(f"  视频URL: {attachment.url}")
            logger.info(f"  文件大小: {attachment.size if hasattr(attachment, 'size') else '未知'}")
            logger.info(f"  文件类型: {attachment.type}")
            
            # 发送分析结果
            analysis_text = f"""📹 **视频消息分析**

👤 **发送者**: {msg.author.username}
📺 **频道**: {msg.ctx.channel.name}
🔗 **视频URL**: {attachment.url}
📁 **文件类型**: {attachment.type}
💾 **文件大小**: {attachment.size if hasattr(attachment, 'size') else '未知'}

🎯 **操作建议**:
- 这是一个视频文件，可以直接播放
- 如果需要提取音频，可以使用 `/dyplay` 命令"""

            await msg.ctx.channel.send(analysis_text)
            
        except Exception as e:
            logger.error(f"分析视频消息失败: {e}")
    
    async def _analyze_douyin_link(self, msg, url):
        """分析抖音链接"""
        try:
            logger.info(f"抖音链接分析:")
            logger.info(f"  用户: {msg.author.username}")
            logger.info(f"  频道: {msg.ctx.channel.name}")
            logger.info(f"  链接: {url}")
            
            # 获取视频信息
            video_info = douyin_api.get_video_info(url)
            if video_info and video_info.is_valid:
                logger.info(f"  视频标题: {video_info.title}")
                logger.info(f"  作者: {video_info.author}")
                logger.info(f"  时长: {video_info.duration_str}")
                logger.info(f"  播放量: {video_info.play_count}")
                logger.info("  开始构建分析结果文本...")
                
                # 发送分析结果
                analysis_text = f"""🔍 **抖音链接分析**

👤 **发送者**: {msg.author.username}
📺 **频道**: {msg.ctx.channel.name}
🔗 **原始链接**: {url}

📹 **视频信息**:
🎵 标题: {video_info.title}
👤 作者: {video_info.author}
⏱️ 时长: {video_info.duration_str}
👀 播放量: {self._format_count(video_info.play_count)}

🎯 **操作建议**:
- 这是一个抖音视频链接
- 可以直接在浏览器中观看"""

                logger.info("  分析结果文本构建完成，准备发送消息...")
                await msg.ctx.channel.send(analysis_text)
                logger.info("  分析结果消息发送完成")
            else:
                await msg.ctx.channel.send(f"❌ 无法解析抖音链接: {url}")
                
        except Exception as e:
            logger.error(f"分析抖音链接失败: {e}")
    
    async def _analyze_video_link(self, msg, url):
        """分析视频文件链接"""
        try:
            logger.info(f"视频文件链接分析:")
            logger.info(f"  用户: {msg.author.username}")
            logger.info(f"  频道: {msg.ctx.channel.name}")
            logger.info(f"  链接: {url}")
            
            # 发送分析结果
            analysis_text = f"""📹 **视频文件链接分析**

👤 **发送者**: {msg.author.username}
📺 **频道**: {msg.ctx.channel.name}
🔗 **视频链接**: {url}

🎯 **操作建议**:
- 这是一个视频文件链接
- 可以直接在浏览器中播放"""

            await msg.ctx.channel.send(analysis_text)
            
        except Exception as e:
            logger.error(f"分析视频文件链接失败: {e}")
    
    async def _handle_dy_command(self, msg: Message, url: str):
        """处理抖音链接"""
        try:
            logger.info(f"=== 开始处理抖音链接 ===")
            logger.info(f"URL: {url}")
            logger.info(f"消息ID: {msg.id}")
            logger.info(f"消息内容: {msg.content[:100] if msg.content else 'None'}")
            import time
            logger.info(f"当前时间: {time.time()}")
            if not url:
                await self.kook_api.send_error_message(msg.ctx.channel, "请提供抖音链接")
                return
            
            # 验证链接
            validation = link_validator.validate_douyin_link(url)
            if not validation['valid']:
                await self.kook_api.send_error_message(msg.ctx.channel, f"链接验证失败: {validation['error']}")
                return
            
            # 获取视频信息
            video_info = douyin_api.get_video_info(url)
            if not video_info or not video_info.is_valid:
                await self.kook_api.send_error_message(msg.ctx.channel, "无法获取视频信息")
                return
            
            # 发送处理中消息
            processing_msg = await msg.ctx.channel.send("🔄 正在下载并上传媒体文件到Kook...")
            
            # 并行处理视频和封面图片
            tasks = []
            
            # 1. 下载并上传视频
            if video_info.video_url:
                tasks.append(self._download_and_upload_video(msg.ctx.channel, video_info))
            
            # 2. 下载并上传封面图片 - 尝试所有可用的封面链接
            cover_urls = video_info.get_available_cover_urls()
            if cover_urls:
                tasks.append(self._download_and_upload_image_with_fallback(msg.ctx.channel, cover_urls, f"{video_info.title} - 封面", video_info))
            
            # 等待所有任务完成
            if tasks:
                import asyncio
                logger.info(f"开始执行 {len(tasks)} 个下载任务...")
                results = await asyncio.gather(*tasks, return_exceptions=True)
                logger.info(f"任务执行结果: {results}")
                success_count = sum(1 for result in results if result is True)
                logger.info(f"成功任务数: {success_count}/{len(tasks)}")
                
                # 检查是否有任何成功的结果
                has_success = success_count > 0
                logger.info(f"是否有成功任务: {has_success}")
                
                # 删除处理消息
                try:
                    await processing_msg.delete()
                except:
                    pass
                
                if has_success:
                    logger.info("发送详细视频信息...")
                    # 发送详细视频信息
                    await self._send_detailed_video_info(msg.ctx.channel, video_info)
                else:
                    logger.info("所有任务失败，但仍显示视频信息...")
                    # 发送提示信息
                    if video_info.kook_video_url:
                        await msg.ctx.channel.send("✅ 视频信息获取成功，但上传到Kook失败")
                    else:
                        await msg.ctx.channel.send("⚠️ 视频下载成功但上传失败，显示原始链接")
                    await self._send_detailed_video_info(msg.ctx.channel, video_info)
            else:
                await processing_msg.edit("❌ 没有找到可处理的媒体文件")
            
            # 记录日志
            bot_logger.log_command(
                user_id=msg.author.id,
                command="dy",
                args=url,
                guild_id=msg.ctx.guild.id,
                channel_id=msg.ctx.channel.id
            )
            
        except Exception as e:
            logger.error(f"处理/dy命令时出错: {e}")
            await self.kook_api.send_error_message(msg.ctx.channel, "处理命令时发生错误")
    

    

    
    async def _handle_dypause_command(self, msg: Message):
        """处理/dypause命令"""
        try:
            player_state = self._get_player_state(msg.ctx.guild.id)
            
            if player_state.is_playing:
                player_state.set_status(PlayerStatus.PAUSED)
                await self.kook_api.send_success_message(msg.ctx.channel, "已暂停播放")
            else:
                await self.kook_api.send_error_message(msg.ctx.channel, "当前没有正在播放的音频")
            
        except Exception as e:
            logger.error(f"处理/dypause命令时出错: {e}")
            await self.kook_api.send_error_message(msg.ctx.channel, "处理命令时发生错误")
    
    async def _handle_dyresume_command(self, msg: Message):
        """处理/dyresume命令"""
        try:
            player_state = self._get_player_state(msg.ctx.guild.id)
            
            if player_state.is_paused:
                player_state.set_status(PlayerStatus.PLAYING)
                await self.kook_api.send_success_message(msg.ctx.channel, "已继续播放")
            else:
                await self.kook_api.send_error_message(msg.ctx.channel, "当前没有暂停的音频")
            
        except Exception as e:
            logger.error(f"处理/dyresume命令时出错: {e}")
            await self.kook_api.send_error_message(msg.ctx.channel, "处理命令时发生错误")
    
    async def _handle_dystop_command(self, msg: Message):
        """处理/dystop命令"""
        try:
            player_state = self._get_player_state(msg.ctx.guild.id)
            
            if not player_state.is_stopped:
                player_state.set_status(PlayerStatus.STOPPED)
                player_state.current_position = 0
                await self.kook_api.send_success_message(msg.ctx.channel, "已停止播放")
            else:
                await self.kook_api.send_error_message(msg.ctx.channel, "当前没有正在播放的音频")
            
        except Exception as e:
            logger.error(f"处理/dystop命令时出错: {e}")
            await self.kook_api.send_error_message(msg.ctx.channel, "处理命令时发生错误")
    
    async def _handle_dyskip_command(self, msg: Message):
        """处理/dyskip命令"""
        try:
            player_state = self._get_player_state(msg.ctx.guild.id)
            
            if player_state.has_queue:
                next_video = player_state.next_video()
                if next_video:
                    player_state.current_video = next_video
                    player_state.current_position = 0
                    player_state.set_status(PlayerStatus.LOADING)
                    
                    await self.kook_api.send_success_message(
                        msg.ctx.channel, 
                        f"已跳过到: {next_video.title}"
                    )
                    
                    # 开始播放新视频
                    await self._start_playback(msg.ctx.guild.id, msg.ctx.channel.id, msg.author.id)
                else:
                    player_state.set_status(PlayerStatus.STOPPED)
                    await self.kook_api.send_success_message(msg.ctx.channel, "已跳过，队列播放完毕")
            else:
                await self.kook_api.send_error_message(msg.ctx.channel, "队列为空")
            
        except Exception as e:
            logger.error(f"处理/dyskip命令时出错: {e}")
            await self.kook_api.send_error_message(msg.ctx.channel, "处理命令时发生错误")
    
    async def _handle_dyqueue_command(self, msg: Message):
        """处理/dyqueue命令"""
        try:
            player_state = self._get_player_state(msg.ctx.guild.id)
            await self.kook_api.send_queue_card(msg.ctx.channel, player_state)
            
        except Exception as e:
            logger.error(f"处理/dyqueue命令时出错: {e}")
            await self.kook_api.send_error_message(msg.ctx.channel, "处理命令时发生错误")
    
    async def _handle_dynow_command(self, msg: Message):
        """处理/dynow命令"""
        try:
            player_state = self._get_player_state(msg.ctx.guild.id)
            
            if player_state.current_video:
                await self.kook_api.send_video_card(msg.ctx.channel, player_state.current_video, player_state)
            else:
                await self.kook_api.send_error_message(msg.ctx.channel, "当前没有播放的视频")
            
        except Exception as e:
            logger.error(f"处理/dynow命令时出错: {e}")
            await self.kook_api.send_error_message(msg.ctx.channel, "处理命令时发生错误")
    
    async def _handle_dyclear_command(self, msg: Message):
        """处理/dyclear命令"""
        try:
            player_state = self._get_player_state(msg.ctx.guild.id)
            
            if player_state.has_queue:
                queue_size = player_state.queue_size
                player_state.clear_queue()
                player_state.set_status(PlayerStatus.STOPPED)
                
                await self.kook_api.send_success_message(
                    msg.ctx.channel, 
                    f"已清空播放队列 ({queue_size} 个视频)"
                )
                
                # 记录日志
                bot_logger.log_queue_operation(
                    user_id=msg.author.id,
                    operation="clear",
                    queue_size=0,
                    guild_id=msg.ctx.guild.id
                )
            else:
                await self.kook_api.send_error_message(msg.ctx.channel, "队列为空")
            
        except Exception as e:
            logger.error(f"处理/dyclear命令时出错: {e}")
            await self.kook_api.send_error_message(msg.ctx.channel, "处理命令时发生错误")
    
    async def _handle_dysearch_command(self, msg: Message, keyword: str):
        """处理/dysearch命令"""
        try:
            if not keyword:
                await self.kook_api.send_error_message(msg.ctx.channel, "请提供搜索关键词")
                return
            
            # 搜索视频
            videos = douyin_api.search_videos(keyword, limit=5)
            
            if not videos:
                await self.kook_api.send_error_message(msg.ctx.channel, "没有找到相关视频")
                return
            
            # 发送搜索结果
            for i, video in enumerate(videos[:3]):  # 只显示前3个结果
                await self.kook_api.send_video_card(msg.ctx.channel, video)
                if i < 2:  # 在结果之间添加分隔
                    await asyncio.sleep(0.5)
            
        except Exception as e:
            logger.error(f"处理/dysearch命令时出错: {e}")
            await self.kook_api.send_error_message(msg.ctx.channel, "处理命令时发生错误")
    
    async def _handle_dyvolume_command(self, msg: Message, volume: int):
        """处理/dyvolume命令"""
        try:
            if not 0 <= volume <= 100:
                await self.kook_api.send_error_message(msg.ctx.channel, "音量必须在0-100之间")
                return
            
            player_state = self._get_player_state(msg.ctx.guild.id)
            player_state.volume = volume
            
            await self.kook_api.send_success_message(
                msg.ctx.channel, 
                f"音量已设置为 {volume}%"
            )
            
        except Exception as e:
            logger.error(f"处理/dyvolume命令时出错: {e}")
            await self.kook_api.send_error_message(msg.ctx.channel, "处理命令时发生错误")
    
    async def _handle_dyhelp_command(self, msg: Message):
        """处理/dyhelp命令"""
        try:
            await self.kook_api.send_help_message(msg.ctx.channel)
            
        except Exception as e:
            logger.error(f"处理/dyhelp命令时出错: {e}")
            await self.kook_api.send_error_message(msg.ctx.channel, "处理命令时发生错误")
    
    async def _handle_dystatus_command(self, msg: Message):
        """处理/dystatus命令"""
        try:
            player_state = self._get_player_state(msg.ctx.guild.id)
            await self.kook_api.send_status_card(msg.ctx.channel, player_state)
            
        except Exception as e:
            logger.error(f"处理/dystatus命令时出错: {e}")
            await self.kook_api.send_error_message(msg.ctx.channel, "处理命令时发生错误")
    
    async def _handle_dyversion_command(self, msg: Message):
        """处理/dyversion命令"""
        try:
            version_info = "🎵 **抖音音乐机器人**\n版本: 1.0.0\n开发者: AI Assistant"
            await self.kook_api.send_success_message(msg.ctx.channel, version_info)
            
        except Exception as e:
            logger.error(f"处理/dyversion命令时出错: {e}")
            await self.kook_api.send_error_message(msg.ctx.channel, "处理命令时发生错误")
    
    async def _handle_dyupload_command(self, msg: Message):
        """处理/dyupload命令"""
        try:
            upload_help = f"""📤 **视频上传帮助**

🔧 **Kook媒体上传API**:
- **接口地址**: `/api/v3/asset/create`
- **请求方式**: POST
- **Content-Type**: form-data

📁 **支持格式**:
- 图片文件
- 视频文件 (.mp4 .mov)
- 其他文件

📋 **上传步骤**:
1. 准备要上传的文件
2. 使用POST请求发送到 `/api/v3/asset/create`
3. 在Header中设置 `Content-Type: form-data`
4. 在body中发送文件数据

📤 **返回格式**:
```json
{{
  "code": 0,
  "message": "操作成功",
  "data": {{
    "url": "https://img.kaiheila.cn/attachments/2021-01/18/xxxxxxxxx.mp4"
  }}
}}
```

🎯 **使用建议**:
- 直接拖拽文件到Kook聊天窗口即可上传
- 机器人会自动分析上传的视频文件
- 支持视频信息提取和音频处理

💡 **提示**: 发送视频文件后，机器人会自动分析并提供详细信息！"""
            
            await msg.ctx.channel.send(upload_help)
            
        except Exception as e:
            logger.error(f"处理/dyupload命令时出错: {e}")
            await self.kook_api.send_error_message(msg.ctx.channel, "获取上传帮助失败")
    
    async def _handle_test_card_command(self, msg: Message):
        """处理/testcard命令"""
        try:
            # 视频信息
            video_url = "https://img.kookapp.cn/attachments/2025-09/03/68b75d7e34311.mp4"
            title = "你说有很多梦都没做#假装快乐#翻唱#弹唱#呆呆破"
            
            await msg.ctx.channel.send("🧪 开始测试视频卡片发送...")
            
            # 测试发送视频卡片
            await self._send_video_card_with_upload(msg.ctx.channel, title, video_url)
            
            await msg.ctx.channel.send("✅ 测试完成！")
            
        except Exception as e:
            logger.error(f"测试卡片命令失败: {e}")
            await msg.ctx.channel.send(f"❌ 测试失败: {e}")
    
    async def _handle_test_image_command(self, msg: Message):
        """处理/testimage命令"""
        try:
            # 测试图片URL
            image_url = "https://img.kaiheila.cn/assets/2021-01/7kr4FkWpLV0ku0ku.jpeg"
            title = "测试图片"
            
            await msg.ctx.channel.send("🖼️ 开始下载图片并上传到Kook...")
            
            # 下载并上传图片，然后发送卡片
            success = await self._download_and_upload_image(msg.ctx.channel, image_url, title)
            
            if success:
                await msg.ctx.channel.send("✅ 图片卡片测试完成！")
            else:
                await msg.ctx.channel.send("❌ 图片卡片测试失败！")
            
        except Exception as e:
            logger.error(f"测试图片命令失败: {e}")
            await msg.ctx.channel.send(f"❌ 测试失败: {e}")
    

    
    async def _download_and_upload_video(self, channel, video_info):
        """下载视频并上传到Kook"""
        try:
            import aiohttp
            import aiofiles
            import os
            import tempfile
            
            logger.info(f"开始下载视频: {video_info.title}")
            logger.info(f"视频URL: {video_info.video_url}")
            
            # 创建临时文件
            temp_dir = tempfile.mkdtemp()
            # 使用随机文件名避免冲突和特殊字符问题
            import uuid
            random_filename = f"{uuid.uuid4().hex}.mp4"
            video_path = os.path.join(temp_dir, random_filename)
            
            # 下载视频，使用随机请求头来绕过防盗链
            async with aiohttp.ClientSession() as session:
                headers = self._get_random_headers('video')
                async with session.get(video_info.video_url, headers=headers) as response:
                    if response.status in [200, 206]:  # 200正常下载，206分片下载
                        async with aiofiles.open(video_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                await f.write(chunk)
                        
                        logger.info(f"视频下载完成: {video_path} (状态码: {response.status})")
                        
                        # 检查文件大小
                        file_size = os.path.getsize(video_path)
                        file_size_mb = file_size / (1024 * 1024)
                        logger.info(f"视频文件大小: {file_size_mb:.2f} MB")
                        
                        # Kook文件大小限制检查（通常限制在50MB以内）
                        if file_size_mb > 50:
                            logger.warning(f"视频文件过大 ({file_size_mb:.2f} MB)，跳过上传到Kook")
                            # 清理临时文件
                            try:
                                os.remove(video_path)
                                os.rmdir(temp_dir)
                            except:
                                pass
                            return False
                        
                        # 上传到Kook，获取返回的链接
                        logger.info("开始上传视频到Kook...")
                        kook_video_url = await self._upload_to_kook(channel, video_path, video_info.title)
                        logger.info(f"Kook上传结果: {kook_video_url}")
                        
                        # 清理临时文件
                        try:
                            os.remove(video_path)
                            os.rmdir(temp_dir)
                        except:
                            pass
                        
                        # 保存Kook链接到video_info
                        if kook_video_url:
                            video_info.kook_video_url = kook_video_url
                            logger.info("视频上传成功，返回True")
                            return True
                        else:
                            logger.warning("视频上传失败，返回False")
                            return False
                    else:
                        logger.error(f"视频下载失败: HTTP {response.status}")
                        logger.error(f"响应头: {dict(response.headers)}")
                        return False
                        
        except Exception as e:
            logger.error(f"下载和上传视频失败: {e}")
            return False
    
    async def _upload_to_kook(self, channel, file_path, title):
        """上传文件到Kook"""
        try:
            import aiohttp
            import aiofiles
            
            logger.info(f"开始上传文件到Kook: {file_path}")
            
            # 准备上传数据
            async with aiofiles.open(file_path, 'rb') as f:
                file_data = await f.read()
            
            # 构建multipart数据
            data = aiohttp.FormData()
            # 使用简单的文件名，避免特殊字符和长度问题
            import uuid
            safe_filename = f"video_{uuid.uuid4().hex[:8]}.mp4"
            data.add_field('file', file_data, filename=safe_filename, content_type='video/mp4')
            
            # 上传到Kook
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bot {settings.BOT_TOKEN}'
                }
                
                async with session.post(
                    'https://www.kookapp.cn/api/v3/asset/create',
                    data=data,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('code') == 0:
                            video_url = result['data']['url']
                            logger.info(f"视频上传成功: {video_url}")
                            
                            # 使用卡片消息发送视频，让用户可以直接在Kook中预览
                            await self._send_video_card_with_upload(channel, title, video_url)
                            return video_url  # 返回Kook链接
                        else:
                            logger.error(f"Kook上传失败: {result.get('message', '未知错误')}")
                            return None
                    else:
                        if response.status == 413:
                            logger.error(f"Kook上传失败: HTTP {response.status} - 文件过大")
                        else:
                            logger.error(f"Kook上传失败: HTTP {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"上传到Kook失败: {e}")
            return None
    
    async def _send_video_card_with_upload(self, channel, title, video_url):
        """发送包含上传视频的卡片消息"""
        try:
            # 方法1: 尝试使用khl.Card类
            try:
                from khl import Card, CardMessage, Module
                
                card = Card()
                card.append(Module.Header(f"📹 {title}"))
                card.append(Module.Video(title, video_url))
                
                card_msg = CardMessage(card)
                await channel.send(card_msg)
                logger.info(f"成功发送视频卡片 (khl.Card): {title}")
                return
                
            except Exception as e:
                logger.warning(f"khl.Card发送失败: {e}")
            
            # 方法2: 尝试使用正确的卡片消息格式
            try:
                import aiohttp
                import json
                
                # 根据你提供的示例，卡片消息应该是数组格式
                card_content = [
                    {
                        "type": "card",
                        "size": "lg",
                        "theme": "secondary",
                        "modules": [
                            {
                                "type": "video",
                                "title": title,
                                "src": video_url
                            }
                        ]
                    }
                ]
                
                # 使用原始API调用
                async with aiohttp.ClientSession() as session:
                    headers = {
                        'Authorization': f'Bot {settings.BOT_TOKEN}',
                        'Content-Type': 'application/json'
                    }
                    
                    payload = {
                        "type": 10,  # 卡片消息类型
                        "channel_id": channel.id,
                        "content": json.dumps(card_content)  # 转换为JSON字符串
                    }
                    
                    async with session.post(
                        'https://www.kookapp.cn/api/v3/message/create',
                        json=payload,
                        headers=headers
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            if result.get('code') == 0:
                                logger.info(f"成功发送视频卡片 (正确格式): {title}")
                                return
                            else:
                                logger.warning(f"API返回错误: {result.get('message', '未知错误')}")
                        else:
                            logger.warning(f"API调用失败: HTTP {response.status}")
                
            except Exception as e:
                logger.warning(f"原始API发送失败: {e}")
            
            # 方法3: 尝试直接发送视频URL（让Kook自动识别）
            try:
                await channel.send(f"📹 **{title}**\n{video_url}")
                logger.info(f"成功发送视频链接: {title}")
                return
                
            except Exception as e:
                logger.warning(f"视频链接发送失败: {e}")
            
            # 如果所有方法都失败，发送错误信息
            await channel.send(f"❌ 无法发送视频卡片，请检查视频URL: {video_url}")
            
        except Exception as e:
            logger.error(f"发送视频卡片失败: {e}")
            # 最后的回退方案
            await channel.send(f"📹 **{title}**\n{video_url}")
    
    async def _download_and_upload_image(self, channel, image_url, title="", video_info=None):
        """下载图片并上传到Kook"""
        try:
            import aiohttp
            import aiofiles
            import tempfile
            import os
            
            logger.info(f"开始下载图片: {title}")
            logger.info(f"图片URL: {image_url}")
            
            # 创建临时目录
            temp_dir = tempfile.mkdtemp()
            # 使用随机文件名避免冲突和特殊字符问题
            import uuid
            random_filename = f"{uuid.uuid4().hex}.jpg"
            temp_file = os.path.join(temp_dir, random_filename)
            
            # 下载图片，使用随机请求头来绕过防盗链
            async with aiohttp.ClientSession() as session:
                headers = self._get_random_headers('image')
                async with session.get(image_url, headers=headers) as response:
                    if response.status == 200:
                        async with aiofiles.open(temp_file, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                await f.write(chunk)
                        logger.info(f"图片下载完成: {temp_file}")
                    else:
                        logger.warning(f"图片下载失败: HTTP {response.status}，跳过图片上传")
                        logger.warning(f"响应头: {dict(response.headers)}")
                        # 清理临时文件
                        try:
                            os.remove(temp_file)
                            os.rmdir(temp_dir)
                        except:
                            pass
                        return False
            
            # 上传到Kook，获取返回的链接
            kook_image_url = await self._upload_image_to_kook(channel, temp_file, title)
            
            # 清理临时文件
            try:
                os.remove(temp_file)
                os.rmdir(temp_dir)
            except:
                pass
            
            # 如果有video_info，保存Kook链接
            if video_info and kook_image_url:
                video_info.kook_cover_url = kook_image_url
            
            return kook_image_url is not None
            
        except Exception as e:
            logger.error(f"下载和上传图片失败: {e}")
            return False
    
    async def _download_and_upload_image_with_fallback(self, channel, image_urls, title, video_info=None):
        """下载并上传图片，支持多个备用链接"""
        try:
            logger.info(f"开始尝试下载图片，共有 {len(image_urls)} 个链接")
            
            for i, image_url in enumerate(image_urls):
                logger.info(f"尝试第 {i+1} 个图片链接: {image_url[:50]}...")
                
                try:
                    # 尝试下载当前链接
                    success = await self._download_and_upload_image(channel, image_url, title, video_info)
                    if success:
                        logger.info(f"第 {i+1} 个图片链接下载成功")
                        return True
                    else:
                        logger.warning(f"第 {i+1} 个图片链接下载失败，尝试下一个")
                        continue
                        
                except Exception as e:
                    logger.warning(f"第 {i+1} 个图片链接下载出错: {e}，尝试下一个")
                    continue
            
            logger.error("所有图片链接都下载失败")
            return False
            
        except Exception as e:
            logger.error(f"图片下载备用机制失败: {e}")
            return False
    
    async def _upload_image_to_kook(self, channel, file_path, title):
        """上传图片到Kook"""
        try:
            import aiohttp
            import aiofiles
            
            logger.info(f"开始上传图片到Kook: {file_path}")
            
            # 准备上传数据
            async with aiofiles.open(file_path, 'rb') as f:
                file_data = await f.read()
            
            # 构建multipart数据
            data = aiohttp.FormData()
            # 使用简单的文件名，避免特殊字符和长度问题
            import uuid
            safe_filename = f"image_{uuid.uuid4().hex[:8]}.jpg"
            data.add_field('file', file_data, filename=safe_filename, content_type='image/jpeg')
            
            # 上传到Kook
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bot {settings.BOT_TOKEN}'
                }
                
                async with session.post(
                    'https://www.kookapp.cn/api/v3/asset/create',
                    data=data,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('code') == 0:
                            image_url = result['data']['url']
                            logger.info(f"图片上传成功: {image_url}")
                            
                            # 发送图片卡片
                            await self._send_image_card_with_upload(channel, title, image_url)
                            return image_url  # 返回Kook链接
                        else:
                            logger.error(f"Kook图片上传失败: {result.get('message', '未知错误')}")
                            return None
                    else:
                        logger.error(f"Kook图片上传失败: HTTP {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"上传图片到Kook失败: {e}")
            return None
    
    async def _send_image_card_with_upload(self, channel, title, image_url):
        """发送包含上传图片的卡片消息"""
        try:
            import aiohttp
            import json
            
            # 图片卡片数据结构
            card_content = [
                {
                    "type": "card",
                    "theme": "secondary",
                    "size": "lg",
                    "modules": [
                        {
                            "type": "container",
                            "elements": [
                                {
                                    "type": "image",
                                    "src": image_url
                                }
                            ]
                        }
                    ]
                }
            ]
            
            # 使用原始API调用
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bot {settings.BOT_TOKEN}',
                    'Content-Type': 'application/json'
                }
                
                payload = {
                    "type": 10,  # 卡片消息类型
                    "channel_id": channel.id,
                    "content": json.dumps(card_content)
                }
                
                async with session.post(
                    'https://www.kookapp.cn/api/v3/message/create',
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('code') == 0:
                            logger.info(f"成功发送图片卡片: {title}")
                            return True
                        else:
                            logger.warning(f"图片卡片API返回错误: {result.get('message', '未知错误')}")
                    else:
                        logger.warning(f"图片卡片API调用失败: HTTP {response.status}")
            
        except Exception as e:
            logger.error(f"发送图片卡片失败: {e}")
        
        # 回退方案
        try:
            await channel.send(f"🖼️ **{title}**\n{image_url}")
            return True
        except Exception as e:
            logger.error(f"发送图片链接失败: {e}")
            return False
    

    

    
    async def _handle_card_interaction(self, msg: Message):
        """处理卡片交互"""
        try:
            # 这里需要根据实际的卡片交互事件来处理
            # 由于Kook.py的卡片交互机制，这里需要根据实际情况调整
            pass
            
        except Exception as e:
            logger.error(f"处理卡片交互时出错: {e}")
    
    def _get_player_state(self, guild_id: str) -> PlayerState:
        """获取播放器状态"""
        if guild_id not in self.player_states:
            self.player_states[guild_id] = PlayerState(guild_id=guild_id)
        return self.player_states[guild_id]
    
    async def _find_user_voice_channel(self, guild_id: str, user_id: str) -> Optional[str]:
        """查找用户所在的语音频道"""
        try:
            # 使用Kook API获取用户所在的语音频道
            response = await self.bot.client.gate.request(
                'GET', 
                'channel-user/get-joined-channel',
                params={'guild_id': guild_id, 'user_id': user_id}
            )
            
            if response and "items" in response:
                voice_channels = response["items"]
                if voice_channels:
                    voice_channel_id = voice_channels[0]['id']
                    logger.info(f"用户 {user_id} 当前语音频道ID: {voice_channel_id}")
                    return voice_channel_id
            
            logger.warning(f"用户 {user_id} 不在任何语音频道")
            return None
            
        except Exception as e:
            logger.error(f"获取用户语音频道异常: {e}")
            return None
    
    async def _send_detailed_video_info(self, channel, video_info):
        """发送详细的视频信息"""
        try:
            # 格式化创建时间
            create_time_str = "未知"
            if video_info.create_time:
                create_time_str = video_info.create_time.strftime("%Y-%m-%d %H:%M:%S")
            
            # 发送详细信息
            text = f"""🎵 **{video_info.title}**

👤 **作者**: {video_info.author}
⏱️ **时长**: {video_info.duration_str}
📅 **发布时间**: {create_time_str}

📊 **数据统计**:
👀 播放量: {self._format_count(video_info.play_count)}
👍 点赞: {self._format_count(video_info.like_count)}
💬 评论: {self._format_count(video_info.comment_count)}
📤 分享: {self._format_count(video_info.share_count)}

📹 **视频链接**:
{video_info.kook_video_url if video_info.kook_video_url else video_info.video_url}

🔗 **其他链接**:
视频ID: `{video_info.video_id}`
封面链接: {video_info.kook_cover_url if video_info.kook_cover_url else video_info.cover_url}

📝 **描述**: {video_info.description[:200] + '...' if len(video_info.description) > 200 else video_info.description}"""

            await channel.send(text)
            logger.info(f"发送详细视频信息: {video_info.title}")
            
        except Exception as e:
            logger.error(f"发送详细视频信息失败: {e}")
            # 发送简化版本作为备选
            text = f"🎵 {video_info.title} - {video_info.author}\n⏱️ {video_info.duration_str}\n👀 {self._format_count(video_info.play_count)}\n📹 {video_info.kook_video_url if video_info.kook_video_url else video_info.video_url}"
            await channel.send(text)
    
    def _format_count(self, count: int) -> str:
        """格式化数字显示"""
        try:
            logger.debug(f"格式化数字: {count} (类型: {type(count)})")
            if count >= 100000000:  # 1亿
                result = f"{count / 100000000:.1f}亿"
            elif count >= 10000:  # 1万
                result = f"{count / 10000:.1f}万"
            else:
                result = str(count)
            logger.debug(f"格式化结果: {result}")
            return result
        except Exception as e:
            logger.error(f"格式化数字失败: {e}, count={count}, type={type(count)}")
            return str(count) if count is not None else "0"
    
    async def _start_playback(self, guild_id: str, channel_id: str, user_id: str):
        """开始播放音频"""
        try:
            player_state = self._get_player_state(guild_id)
            
            if not player_state.current_video:
                return
            
            # 获取音频流URL
            audio_url = douyin_api.get_audio_stream_url(player_state.current_video)
            if not audio_url:
                player_state.set_status(PlayerStatus.ERROR, "无法获取音频流")
                return
            
            # 创建音频流
            stream_id = f"{guild_id}_{player_state.current_video.video_id}"
            audio_path = await audio_streamer.create_stream(audio_url, stream_id)
            
            if not audio_path:
                player_state.set_status(PlayerStatus.ERROR, "音频下载失败")
                return
            
            # 设置播放状态
            player_state.set_status(PlayerStatus.PLAYING)
            
            # 使用Kook语音播放功能
            channel = None
            try:
                # 获取频道对象
                channel = await self.bot.fetch_public_channel(channel_id)
                
                # 检查是否为语音频道
                if hasattr(channel, 'type') and channel.type == 2:  # 语音频道类型
                    logger.info(f"检测到语音频道: {channel.name}")
                    voice_channel_id = channel_id
                else:
                    # 如果不是语音频道，尝试找到用户所在的语音频道
                    logger.info(f"频道 {channel.name if channel else '未知'} 不是语音频道，尝试查找用户语音频道")
                    
                    # 查找用户所在的语音频道
                    voice_channel_id = await self._find_user_voice_channel(guild_id, user_id)
                    if not voice_channel_id:
                        player_state.set_status(PlayerStatus.ERROR, "请先加入语音频道")
                        await self.kook_api.send_error_message(
                            channel, 
                            "❌ 请先加入语音频道，然后再使用播放命令"
                        )
                        return
                    
                    logger.info(f"找到用户语音频道: {voice_channel_id}")
                
                # 导入Kook语音播放器
                import sys
                import os
                sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'windows'))
                
                try:
                    import kookvoice
                    
                    # 配置FFmpeg路径（Linux环境）
                    ffmpeg_path = settings.FFMPEG_PATH
                    ffprobe_path = settings.FFPROBE_PATH
                    
                    logger.info(f"配置FFmpeg路径: {ffmpeg_path}")
                    logger.info(f"配置FFprobe路径: {ffprobe_path}")
                    
                    # 设置FFmpeg路径
                    kookvoice.set_ffmpeg(ffmpeg_path)
                    kookvoice.configure_logging(True)  # 启用详细日志
                    
                    # 创建播放器实例
                    player = kookvoice.Player(guild_id, voice_channel_id, settings.BOT_TOKEN)
                    
                    # 添加音频到播放队列
                    extra_data = {
                        "音乐名字": player_state.current_video.title,
                        "点歌人": user_id,
                        "文字频道": channel_id,
                        "来源": "抖音"
                    }
                    
                    logger.info(f"添加音频到播放队列: {audio_path}")
                    player.add_music(audio_path, extra_data)
                    
                    # 加入语音频道并开始播放
                    logger.info(f"尝试加入语音频道: {voice_channel_id}")
                    
                    # 添加延迟，避免操作过于频繁
                    import time
                    time.sleep(2)  # 等待2秒
                    
                    player.join()
                    
                    # 发送播放开始消息
                    await self.kook_api.send_success_message(
                        channel, 
                        f"🎵 开始播放: {player_state.current_video.title}\n"
                        f"⏱️ 时长: {player_state.current_video.duration_str}\n"
                        f"👤 作者: {player_state.current_video.author}\n"
                        f"🎤 语音频道: {voice_channel_id}\n"
                        f"📁 音频文件: {audio_path}"
                    )
                    
                    logger.info(f"已添加音频到播放队列并开始播放: {player_state.current_video.title}")
                    
                except ImportError as e:
                    logger.error(f"无法导入kookvoice模块: {e}")
                    # 发送错误消息
                    if channel:
                        await self.kook_api.send_error_message(
                            channel, 
                            "❌ 语音播放模块加载失败，请检查配置"
                        )
                    player_state.set_status(PlayerStatus.ERROR, "语音播放模块加载失败")
                except Exception as e:
                    logger.error(f"播放器启动失败: {e}")
                    # 发送错误消息
                    if channel:
                        await self.kook_api.send_error_message(
                            channel, 
                            f"❌ 播放器启动失败: {e}"
                        )
                    player_state.set_status(PlayerStatus.ERROR, f"播放器启动失败: {e}")
                
            except Exception as voice_error:
                logger.error(f"语音播放失败: {voice_error}")
                player_state.set_status(PlayerStatus.ERROR, f"语音播放失败: {voice_error}")
                if channel:
                    await self.kook_api.send_error_message(
                        channel, 
                        f"❌ 语音播放失败: {voice_error}"
                    )
            
        except Exception as e:
            logger.error(f"开始播放时出错: {e}")
            player_state = self._get_player_state(guild_id)
            player_state.set_status(PlayerStatus.ERROR, str(e))
    
    async def start(self):
        """启动机器人"""
        try:
            logger.info("正在启动抖音音乐机器人...")
            await self.bot.start()
        except Exception as e:
            logger.error(f"启动机器人失败: {e}")
            raise
    
    async def shutdown(self):
        """关闭机器人"""
        logger.info("正在关闭抖音音乐机器人...")
        
        # 直接强制退出，不进行复杂清理
        import os
        os._exit(0)


# 创建全局机器人实例
bot_instance = DouyinBot()


async def main():
    """主函数"""
    try:
        # 验证配置
        settings.validate()
        
        # 启动机器人
        await bot_instance.start()
        
    except KeyboardInterrupt:
        logger.info("收到中断信号")
    except Exception as e:
        logger.error(f"运行机器人时出错: {e}")
    finally:
        await bot_instance.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
