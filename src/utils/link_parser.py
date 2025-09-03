"""
链接解析工具
"""
import re
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse, parse_qs
from loguru import logger


class LinkParser:
    """链接解析器"""
    
    def __init__(self):
        # 抖音链接模式
        self.douyin_patterns = [
            # 短链接，支持连字符和下划线
            r'https?://v\.douyin\.com/[A-Za-z0-9\-_]+/?',
            # 长链接
            r'https?://www\.douyin\.com/video/(\d+)',
            r'https?://m\.douyin\.com/video/(\d+)',
            # 其他格式
            r'https?://www\.iesdouyin\.com/share/video/(\d+)',
            r'https?://www\.iesdouyin\.com/share/video/(\d+)/\?region=',
        ]
        
        # 编译正则表达式
        self.compiled_patterns = [re.compile(pattern) for pattern in self.douyin_patterns]
    
    def is_douyin_link(self, url: str) -> bool:
        """检查是否为抖音链接"""
        if not url:
            return False
        
        url = url.strip()
        
        for pattern in self.compiled_patterns:
            if pattern.search(url):
                return True
        
        return False
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """从抖音链接中提取视频ID"""
        if not self.is_douyin_link(url):
            return None
        
        url = url.strip()
        
        for i, pattern in enumerate(self.compiled_patterns):
            match = pattern.search(url)
            if match:
                # 如果有捕获组，直接返回
                if match.groups():
                    return match.group(1)
                # 对于短链接，需要进一步处理
                elif i == 0:  # 短链接模式
                    return self._extract_from_short_url(url)
        
        return None
    
    def _extract_from_short_url(self, url: str) -> Optional[str]:
        """从短链接中提取视频ID"""
        try:
            import requests
            import re
            
            # 清理URL，移除Markdown格式
            clean_url = url.strip()
            if clean_url.startswith('[') and clean_url.endswith(')'):
                # 处理Markdown格式的链接 [text](url)
                match = re.search(r'\]\(([^)]+)\)', clean_url)
                if match:
                    clean_url = match.group(1)
            
            # 获取重定向后的URL
            response = requests.head(clean_url, allow_redirects=True, timeout=10)
            final_url = response.url
            
            # 从最终URL中提取视频ID
            video_id_pattern = r'/video/(\d+)'
            match = re.search(video_id_pattern, final_url)
            if match:
                return match.group(1)
            
            logger.warning(f"无法从短链接提取视频ID: {clean_url} -> {final_url}")
            return None
            
        except Exception as e:
            logger.error(f"处理短链接时出错: {e}")
            return None
    
    def normalize_url(self, url: str) -> Optional[str]:
        """标准化抖音链接"""
        if not self.is_douyin_link(url):
            return None
        
        video_id = self.extract_video_id(url)
        if not video_id:
            return None
        
        # 返回标准格式的链接
        return f"https://www.douyin.com/video/{video_id}"
    
    def parse_url_params(self, url: str) -> Dict[str, Any]:
        """解析URL参数"""
        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            
            # 将列表值转换为单个值
            result = {}
            for key, value in params.items():
                if len(value) == 1:
                    result[key] = value[0]
                else:
                    result[key] = value
            
            return result
            
        except Exception as e:
            logger.error(f"解析URL参数失败: {e}")
            return {}
    
    def validate_url(self, url: str) -> bool:
        """验证URL格式"""
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except Exception:
            return False
    
    def extract_domain(self, url: str) -> Optional[str]:
        """提取域名"""
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except Exception:
            return None
    
    def is_supported_platform(self, url: str) -> bool:
        """检查是否为支持的平台"""
        if not url:
            return False
        
        domain = self.extract_domain(url)
        if not domain:
            return False
        
        # 支持的平台域名
        supported_domains = [
            'douyin.com',
            'v.douyin.com',
            'm.douyin.com',
            'iesdouyin.com'
        ]
        
        for supported_domain in supported_domains:
            if domain.endswith(supported_domain):
                return True
        
        return False
    
    def clean_url(self, url: str) -> str:
        """清理URL"""
        if not url:
            return ""
        
        # 移除前后空格
        url = url.strip()
        
        # 移除多余的参数
        if '?' in url:
            base_url = url.split('?')[0]
            # 保留必要的参数
            if 'region=' in url:
                region_match = re.search(r'region=([^&]+)', url)
                if region_match:
                    url = f"{base_url}?region={region_match.group(1)}"
            else:
                url = base_url
        
        return url
    
    def extract_links_from_text(self, text: str) -> List[str]:
        """从文本中提取所有链接"""
        if not text:
            return []
        
        # URL正则表达式
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        matches = re.findall(url_pattern, text)
        
        # 过滤出抖音链接
        douyin_links = []
        for match in matches:
            if self.is_douyin_link(match):
                douyin_links.append(match)
        
        return douyin_links
    
    def get_link_info(self, url: str) -> Dict[str, Any]:
        """获取链接信息"""
        info = {
            'url': url,
            'is_douyin': False,
            'is_supported': False,
            'video_id': None,
            'normalized_url': None,
            'domain': None,
            'is_valid': False
        }
        
        if not url:
            return info
        
        # 清理URL
        clean_url = self.clean_url(url)
        info['url'] = clean_url
        
        # 验证URL格式
        info['is_valid'] = self.validate_url(clean_url)
        if not info['is_valid']:
            return info
        
        # 检查是否为抖音链接
        info['is_douyin'] = self.is_douyin_link(clean_url)
        
        # 检查是否为支持的平台
        info['is_supported'] = self.is_supported_platform(clean_url)
        
        # 提取域名
        info['domain'] = self.extract_domain(clean_url)
        
        # 如果是抖音链接，提取更多信息
        if info['is_douyin']:
            info['video_id'] = self.extract_video_id(clean_url)
            info['normalized_url'] = self.normalize_url(clean_url)
        
        return info


class LinkValidator:
    """链接验证器"""
    
    def __init__(self):
        self.parser = LinkParser()
    
    def validate_douyin_link(self, url: str) -> Dict[str, Any]:
        """验证抖音链接"""
        result = {
            'valid': False,
            'error': None,
            'video_id': None,
            'normalized_url': None
        }
        
        if not url:
            result['error'] = "链接为空"
            return result
        
        # 检查是否为抖音链接
        if not self.parser.is_douyin_link(url):
            result['error'] = "不是有效的抖音链接"
            return result
        
        # 提取视频ID
        video_id = self.parser.extract_video_id(url)
        if not video_id:
            result['error'] = "无法提取视频ID"
            return result
        
        # 标准化链接
        normalized_url = self.parser.normalize_url(url)
        if not normalized_url:
            result['error'] = "无法标准化链接"
            return result
        
        result['valid'] = True
        result['video_id'] = video_id
        result['normalized_url'] = normalized_url
        
        return result
    
    def validate_multiple_links(self, urls: List[str]) -> List[Dict[str, Any]]:
        """验证多个链接"""
        results = []
        for url in urls:
            result = self.validate_douyin_link(url)
            results.append(result)
        return results


# 创建全局实例
link_parser = LinkParser()
link_validator = LinkValidator()
