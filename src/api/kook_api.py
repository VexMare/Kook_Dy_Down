"""
Kook API封装
"""
import asyncio
from typing import Optional, Dict, Any, List
from loguru import logger

import khl
from khl import Bot, Message, User, Channel, Guild
from khl.card import Card, CardMessage, Module, Element, Struct

from src.models.video import VideoInfo
from src.models.player import PlayerState, PlayerStatus


class KookAPI:
    """Kook API封装类"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
    
    async def send_video_card(self, channel: Channel, video_info: VideoInfo, 
                            player_state: Optional[PlayerState] = None) -> Message:
        """发送视频信息卡片"""
        try:
            # 暂时使用简单文本消息，避免卡片格式问题
            text = f"""🎵 **{video_info.title}**

👤 **作者**: {video_info.author}
⏱️ **时长**: {video_info.duration_str}
👀 **播放量**: {self._format_count(video_info.play_count)}
👍 **点赞**: {self._format_count(video_info.like_count)}
💬 **评论**: {self._format_count(video_info.comment_count)}
📤 **分享**: {self._format_count(video_info.share_count)}

🔗 **视频ID**: {video_info.video_id}
📹 **视频链接**: {video_info.kook_video_url if video_info.kook_video_url else video_info.video_url}"""
            
            msg = await channel.send(text)
            logger.info(f"发送视频信息: {video_info.title}")
            return msg
            
        except Exception as e:
            logger.error(f"发送视频信息失败: {e}")
            # 发送最简单的文本消息作为备选
            text = f"🎵 {video_info.title} - {video_info.author}"
            return await channel.send(text)
    
    def _create_video_card(self, video_info: VideoInfo, 
                          player_state: Optional[PlayerState] = None) -> CardMessage:
        """创建视频信息卡片"""
        card = Card()
        
        # 标题模块
        title_text = video_info.title[:50] + "..." if len(video_info.title) > 50 else video_info.title
        card.append(Module.Header(f"🎵 {title_text}"))
        
        # 分隔线
        card.append(Module.Divider())
        
        # 视频信息模块 - 使用简单文本
        info_text = f"👤 作者: {video_info.author}\n"
        info_text += f"⏱️ 时长: {video_info.duration_str}\n"
        info_text += f"👀 播放量: {self._format_count(video_info.play_count)}\n"
        info_text += f"👍 点赞: {self._format_count(video_info.like_count)}"
        
        card.append(Module.Section(Element.Text(info_text)))
        
        # 如果有封面，添加封面图片
        cover_url = video_info.kook_cover_url if video_info.kook_cover_url else video_info.cover_url
        if cover_url:
            card.append(Module.Container(Element.Image(cover_url)))
        
        return CardMessage(card)
    
    def _create_control_buttons(self, video_info: VideoInfo, 
                               player_state: Optional[PlayerState] = None) -> List[Element.Button]:
        """创建控制按钮"""
        buttons = []
        
        if not player_state or player_state.is_stopped:
            # 播放按钮
            buttons.append(Element.Button(
                text="播放",
                theme="success",
                value=f"play_{video_info.video_id}",
                click="return-val"
            ))
        elif player_state.is_playing:
            # 暂停按钮
            buttons.append(Element.Button(
                text="暂停",
                theme="warning",
                value=f"pause_{video_info.video_id}",
                click="return-val"
            ))
        elif player_state.is_paused:
            # 继续按钮
            buttons.append(Element.Button(
                text="继续",
                theme="success",
                value=f"resume_{video_info.video_id}",
                click="return-val"
            ))
        
        # 添加到队列按钮
        buttons.append(Element.Button(
            text="添加到队列",
            theme="primary",
            value=f"add_{video_info.video_id}",
            click="return-val"
        ))
        
        # 停止按钮
        if player_state and not player_state.is_stopped:
            buttons.append(Element.Button(
                text="停止",
                theme="danger",
                value=f"stop_{video_info.video_id}",
                click="return-val"
            ))
        
        # 队列按钮
        if player_state and player_state.has_queue:
            buttons.append(Element.Button(
                text=f"队列 ({player_state.queue_size})",
                theme="info",
                value=f"queue_{video_info.video_id}",
                click="return-val"
            ))
        
        return buttons
    
    def _get_status_text(self, player_state: PlayerState) -> str:
        """获取播放状态文本"""
        if player_state.is_playing:
            return f"🔊 **正在播放** | 进度: {player_state.current_position_str} | 音量: {player_state.volume}%"
        elif player_state.is_paused:
            return f"⏸️ **已暂停** | 进度: {player_state.current_position_str} | 音量: {player_state.volume}%"
        elif player_state.is_stopped:
            return f"⏹️ **已停止** | 音量: {player_state.volume}%"
        else:
            return f"❓ **状态未知** | 音量: {player_state.volume}%"
    
    def _format_count(self, count: int) -> str:
        """格式化数字显示"""
        if count >= 10000:
            return f"{count/10000:.1f}万"
        elif count >= 1000:
            return f"{count/1000:.1f}千"
        else:
            return str(count)
    
    async def send_queue_card(self, channel: Channel, player_state: PlayerState) -> Message:
        """发送播放队列卡片"""
        try:
            card = Card()
            
            # 标题
            card.append(Module.Header(f"📋 播放队列 ({player_state.queue_size})"))
            card.append(Module.Divider())
            
            if not player_state.has_queue:
                card.append(Module.Section(Element.Text("队列为空", type="kmarkdown")))
            else:
                # 队列信息
                for i, video in enumerate(player_state.queue):
                    is_current = i == player_state.queue_position
                    prefix = "🔊" if is_current else "⏸️"
                    
                    video_text = f"{prefix} **{i+1}.** {video.title[:30]}...\n"
                    video_text += f"👤 {video.author} | ⏱️ {video.duration_str}"
                    
                    card.append(Module.Section(Element.Text(video_text, type="kmarkdown")))
                    
                    # 限制显示数量
                    if i >= 9:  # 最多显示10个
                        remaining = player_state.queue_size - 10
                        if remaining > 0:
                            card.append(Module.Section(Element.Text(f"... 还有 {remaining} 个视频", type="kmarkdown")))
                        break
            
            # 控制按钮
            control_buttons = []
            if player_state.has_queue:
                control_buttons.extend([
                    Element.Button(
                        text="⏭️ 下一首",
                        theme="primary",
                        value="next",
                        click="return-val"
                    ),
                    Element.Button(
                        text="⏮️ 上一首",
                        theme="primary",
                        value="previous",
                        click="return-val"
                    ),
                    Element.Button(
                        text="🗑️ 清空队列",
                        theme="danger",
                        value="clear_queue",
                        click="return-val"
                    )
                ])
            
            if control_buttons:
                card.append(Module.ActionGroup(control_buttons))
            
            msg = await channel.send(CardMessage(card))
            logger.info(f"发送队列卡片: {player_state.queue_size} 个视频")
            return msg
            
        except Exception as e:
            logger.error(f"发送队列卡片失败: {e}")
            # 发送简单文本消息作为备选
            if player_state.has_queue:
                text = f"📋 **播放队列** ({player_state.queue_size})\n"
                for i, video in enumerate(player_state.queue[:5]):
                    is_current = i == player_state.queue_position
                    prefix = "🔊" if is_current else "⏸️"
                    text += f"{prefix} {i+1}. {video.title[:30]}...\n"
                if player_state.queue_size > 5:
                    text += f"... 还有 {player_state.queue_size - 5} 个视频"
            else:
                text = "📋 播放队列为空"
            
            return await channel.send(text)
    
    async def send_status_card(self, channel: Channel, player_state: PlayerState) -> Message:
        """发送状态卡片"""
        try:
            card = Card()
            
            # 标题
            card.append(Module.Header("📊 播放器状态"))
            card.append(Module.Divider())
            
            # 状态信息
            status_text = f"🎵 **状态**: {self._get_status_display(player_state.status)}\n"
            status_text += f"🔊 **音量**: {player_state.volume}%\n"
            status_text += f"📋 **队列**: {player_state.queue_size} 个视频\n"
            
            if player_state.current_video:
                status_text += f"🎬 **当前**: {player_state.current_video.title[:30]}...\n"
                status_text += f"⏱️ **进度**: {player_state.current_position_str} / {player_state.current_video.duration_str}\n"
                status_text += f"📊 **进度条**: {player_state.progress_percentage:.1f}%"
            
            card.append(Module.Section(Element.Text(status_text, type="kmarkdown")))
            
            # 错误信息
            if player_state.error_message:
                card.append(Module.Section(Element.Text(f"❌ **错误**: {player_state.error_message}", type="kmarkdown")))
            
            msg = await channel.send(CardMessage(card))
            logger.info("发送状态卡片")
            return msg
            
        except Exception as e:
            logger.error(f"发送状态卡片失败: {e}")
            # 发送简单文本消息作为备选
            text = f"📊 **播放器状态**\n"
            text += f"🎵 状态: {self._get_status_display(player_state.status)}\n"
            text += f"🔊 音量: {player_state.volume}%\n"
            text += f"📋 队列: {player_state.queue_size} 个视频"
            
            if player_state.current_video:
                text += f"\n🎬 当前: {player_state.current_video.title[:30]}..."
                text += f"\n⏱️ 进度: {player_state.current_position_str} / {player_state.current_video.duration_str}"
            
            return await channel.send(text)
    
    def _get_status_display(self, status: PlayerStatus) -> str:
        """获取状态显示文本"""
        status_map = {
            PlayerStatus.STOPPED: "⏹️ 已停止",
            PlayerStatus.PLAYING: "🔊 播放中",
            PlayerStatus.PAUSED: "⏸️ 已暂停",
            PlayerStatus.LOADING: "⏳ 加载中",
            PlayerStatus.ERROR: "❌ 错误"
        }
        return status_map.get(status, "❓ 未知")
    
    async def send_error_message(self, channel: Channel, error_msg: str) -> Message:
        """发送错误消息"""
        try:
            card = Card()
            card.append(Module.Header("❌ 错误"))
            card.append(Module.Divider())
            card.append(Module.Section(Element.Text(error_msg, type="kmarkdown")))
            
            return await channel.send(CardMessage(card))
        except Exception as e:
            logger.error(f"发送错误消息失败: {e}")
            return await channel.send(f"❌ 错误: {error_msg}")
    
    async def send_success_message(self, channel: Channel, success_msg: str) -> Message:
        """发送成功消息"""
        try:
            card = Card()
            card.append(Module.Header("✅ 成功"))
            card.append(Module.Divider())
            card.append(Module.Section(Element.Text(success_msg, type="kmarkdown")))
            
            return await channel.send(CardMessage(card))
        except Exception as e:
            logger.error(f"发送成功消息失败: {e}")
            return await channel.send(f"✅ {success_msg}")
    
    async def send_help_message(self, channel: Channel) -> Message:
        """发送帮助消息"""
        try:
            card = Card()
            
            # 标题
            card.append(Module.Header("🎵 抖音音乐机器人帮助"))
            card.append(Module.Divider())
            
            # 基本命令
            basic_commands = """
**基本命令:**
`/dy [链接]` - 获取视频信息
`/dyplay [链接]` - 播放音频
`/dyadd [链接]` - 添加到队列
`/dysearch [关键词]` - 搜索视频
            """
            card.append(Module.Section(Element.Text(basic_commands, type="kmarkdown")))
            
            # 播放控制
            control_commands = """
**播放控制:**
`/dypause` - 暂停播放
`/dyresume` - 继续播放
`/dystop` - 停止播放
`/dyskip` - 跳过当前音频
`/dyvolume [0-100]` - 调整音量
            """
            card.append(Module.Section(Element.Text(control_commands, type="kmarkdown")))
            
            # 队列管理
            queue_commands = """
**队列管理:**
`/dyqueue` - 查看播放队列
`/dynow` - 显示当前播放信息
`/dyclear` - 清空播放队列
            """
            card.append(Module.Section(Element.Text(queue_commands, type="kmarkdown")))
            
            # 其他命令
            other_commands = """
**其他命令:**
`/dyhelp` - 显示帮助信息
`/dystatus` - 显示机器人状态
`/dyversion` - 显示版本信息
            """
            card.append(Module.Section(Element.Text(other_commands, type="kmarkdown")))
            
            return await channel.send(CardMessage(card))
            
        except Exception as e:
            logger.error(f"发送帮助消息失败: {e}")
            # 发送简单文本消息作为备选
            text = """🎵 **抖音音乐机器人帮助**

**基本命令:**
`/dy [链接]` - 获取视频信息
`/dyplay [链接]` - 播放音频
`/dyadd [链接]` - 添加到队列
`/dysearch [关键词]` - 搜索视频

**播放控制:**
`/dypause` - 暂停播放
`/dyresume` - 继续播放
`/dystop` - 停止播放
`/dyskip` - 跳过当前音频
`/dyvolume [0-100]` - 调整音量

**队列管理:**
`/dyqueue` - 查看播放队列
`/dynow` - 显示当前播放信息
`/dyclear` - 清空播放队列

**其他命令:**
`/dyhelp` - 显示帮助信息
`/dystatus` - 显示机器人状态
`/dyversion` - 显示版本信息"""
            
            return await channel.send(text)
