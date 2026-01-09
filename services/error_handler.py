# -*- coding: utf-8 -*-
"""
錯誤分類與智能重試策略
"""

from enum import Enum
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
import re


class ErrorCategory(Enum):
    """錯誤類別"""
    RATE_LIMITED = "rate_limited"       # 頻率限制 - 等待後重試
    GEO_BLOCKED = "geo_blocked"         # 地區限制 - 需要代理
    PRIVATE_VIDEO = "private_video"     # 私人影片 - 無法下載
    AGE_RESTRICTED = "age_restricted"   # 年齡限制 - 需要 cookies
    NETWORK_ERROR = "network_error"     # 網路錯誤 - 立即重試
    PROXY_ERROR = "proxy_error"         # 代理錯誤 - 換代理重試
    FORMAT_ERROR = "format_error"       # 格式錯誤 - 降級畫質
    VIDEO_UNAVAILABLE = "unavailable"   # 影片不存在
    COPYRIGHT = "copyright"             # 版權問題 - 無法下載
    LIVE_STREAM = "live_stream"         # 直播中 - 無法下載
    UNKNOWN = "unknown"                 # 未知錯誤


@dataclass
class RetryStrategy:
    """重試策略"""
    should_retry: bool              # 是否應該重試
    max_retries: int               # 最大重試次數
    delay_seconds: int             # 重試延遲秒數
    change_proxy: bool             # 是否需要換代理
    downgrade_quality: bool        # 是否需要降級畫質
    message: str                   # 給使用者的訊息
    message_zh: str                # 中文訊息


# 錯誤模式匹配規則
ERROR_PATTERNS: Dict[ErrorCategory, list] = {
    ErrorCategory.RATE_LIMITED: [
        r'HTTP Error 429',
        r'rate.?limit',
        r'too many requests',
        r'quota exceeded',
        r'請求過於頻繁',
    ],
    ErrorCategory.GEO_BLOCKED: [
        r'geo.?blocked',
        r'not available in your country',
        r'video is not available',
        r'地區限制',
        r'The uploader has not made this video available in your country',
    ],
    ErrorCategory.PRIVATE_VIDEO: [
        r'private video',
        r'video is private',
        r'私人影片',
        r'Sign in to confirm your age',
    ],
    ErrorCategory.AGE_RESTRICTED: [
        r'age.?restrict',
        r'confirm your age',
        r'年齡限制',
        r'Sign in to confirm',
    ],
    ErrorCategory.NETWORK_ERROR: [
        r'connection reset',
        r'connection refused',
        r'connection timed out',
        r'network is unreachable',
        r'socket timeout',
        r'read timed out',
        r'urlopen error',
        r'getaddrinfo failed',
        r'Name or service not known',
        r'Temporary failure in name resolution',
    ],
    ErrorCategory.PROXY_ERROR: [
        r'proxy',
        r'tunnel connection failed',
        r'Cannot connect to proxy',
        r'407 Proxy Authentication Required',
    ],
    ErrorCategory.FORMAT_ERROR: [
        r'requested format not available',
        r'format.?not.?available',
        r'no video formats',
        r'格式不可用',
    ],
    ErrorCategory.VIDEO_UNAVAILABLE: [
        r'Video unavailable',
        r'This video is unavailable',
        r'影片不存在',
        r'This video has been removed',
        r'This video is no longer available',
    ],
    ErrorCategory.COPYRIGHT: [
        r'copyright',
        r'blocked.*copyright',
        r'This video contains content from',
        r'版權',
    ],
    ErrorCategory.LIVE_STREAM: [
        r'live stream',
        r'is live',
        r'Premieres in',
        r'直播',
    ],
}

# 各錯誤類別的重試策略
RETRY_STRATEGIES: Dict[ErrorCategory, RetryStrategy] = {
    ErrorCategory.RATE_LIMITED: RetryStrategy(
        should_retry=True,
        max_retries=3,
        delay_seconds=60,
        change_proxy=True,
        downgrade_quality=False,
        message="Rate limited by YouTube. Will retry with different proxy.",
        message_zh="YouTube 頻率限制，將使用不同代理重試"
    ),
    ErrorCategory.GEO_BLOCKED: RetryStrategy(
        should_retry=True,
        max_retries=5,
        delay_seconds=2,
        change_proxy=True,
        downgrade_quality=False,
        message="Video is geo-blocked. Trying different proxy.",
        message_zh="影片有地區限制，嘗試使用其他代理"
    ),
    ErrorCategory.PRIVATE_VIDEO: RetryStrategy(
        should_retry=False,
        max_retries=0,
        delay_seconds=0,
        change_proxy=False,
        downgrade_quality=False,
        message="This video is private and cannot be downloaded.",
        message_zh="這是私人影片，無法下載"
    ),
    ErrorCategory.AGE_RESTRICTED: RetryStrategy(
        should_retry=False,
        max_retries=0,
        delay_seconds=0,
        change_proxy=False,
        downgrade_quality=False,
        message="Age-restricted video. Please provide YouTube cookies.",
        message_zh="年齡限制影片，需要提供 YouTube cookies"
    ),
    ErrorCategory.NETWORK_ERROR: RetryStrategy(
        should_retry=True,
        max_retries=5,
        delay_seconds=5,
        change_proxy=False,
        downgrade_quality=False,
        message="Network error. Retrying...",
        message_zh="網路錯誤，正在重試..."
    ),
    ErrorCategory.PROXY_ERROR: RetryStrategy(
        should_retry=True,
        max_retries=10,
        delay_seconds=2,
        change_proxy=True,
        downgrade_quality=False,
        message="Proxy error. Switching to different proxy.",
        message_zh="代理錯誤，切換到其他代理"
    ),
    ErrorCategory.FORMAT_ERROR: RetryStrategy(
        should_retry=True,
        max_retries=3,
        delay_seconds=1,
        change_proxy=False,
        downgrade_quality=True,
        message="Requested format not available. Trying lower quality.",
        message_zh="指定格式不可用，嘗試較低畫質"
    ),
    ErrorCategory.VIDEO_UNAVAILABLE: RetryStrategy(
        should_retry=False,
        max_retries=0,
        delay_seconds=0,
        change_proxy=False,
        downgrade_quality=False,
        message="Video is unavailable or has been removed.",
        message_zh="影片不存在或已被移除"
    ),
    ErrorCategory.COPYRIGHT: RetryStrategy(
        should_retry=False,
        max_retries=0,
        delay_seconds=0,
        change_proxy=False,
        downgrade_quality=False,
        message="Video blocked due to copyright.",
        message_zh="影片因版權問題無法下載"
    ),
    ErrorCategory.LIVE_STREAM: RetryStrategy(
        should_retry=False,
        max_retries=0,
        delay_seconds=0,
        change_proxy=False,
        downgrade_quality=False,
        message="Cannot download live streams. Please wait until the stream ends.",
        message_zh="無法下載直播中的影片，請等待直播結束"
    ),
    ErrorCategory.UNKNOWN: RetryStrategy(
        should_retry=True,
        max_retries=2,
        delay_seconds=10,
        change_proxy=True,
        downgrade_quality=False,
        message="Unknown error occurred. Retrying...",
        message_zh="發生未知錯誤，正在重試..."
    ),
}


def classify_error(error_message: str) -> Tuple[ErrorCategory, RetryStrategy]:
    """
    分類錯誤並返回對應的重試策略

    Args:
        error_message: 錯誤訊息字串

    Returns:
        (錯誤類別, 重試策略)
    """
    if not error_message:
        return ErrorCategory.UNKNOWN, RETRY_STRATEGIES[ErrorCategory.UNKNOWN]

    error_lower = error_message.lower()

    # 依序檢查各錯誤類別的模式
    for category, patterns in ERROR_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, error_lower, re.IGNORECASE):
                return category, RETRY_STRATEGIES[category]

    return ErrorCategory.UNKNOWN, RETRY_STRATEGIES[ErrorCategory.UNKNOWN]


def get_downgraded_format(current_format: str) -> Optional[str]:
    """
    取得降級後的格式

    Args:
        current_format: 當前格式選項

    Returns:
        降級後的格式，如果已經是最低則返回 None
    """
    format_hierarchy = ["best", "1080p", "720p", "480p", "360p"]

    try:
        current_index = format_hierarchy.index(current_format)
        if current_index < len(format_hierarchy) - 1:
            return format_hierarchy[current_index + 1]
    except ValueError:
        # 如果是自訂格式，降到 720p
        return "720p"

    return None


def format_error_response(
    error_message: str,
    category: ErrorCategory,
    strategy: RetryStrategy,
    retry_count: int = 0
) -> Dict[str, Any]:
    """
    格式化錯誤回應

    Args:
        error_message: 原始錯誤訊息
        category: 錯誤類別
        strategy: 重試策略
        retry_count: 目前重試次數

    Returns:
        格式化的錯誤回應字典
    """
    return {
        "error": True,
        "category": category.value,
        "message": strategy.message_zh,
        "message_en": strategy.message,
        "original_error": error_message[:500],  # 截斷過長的錯誤訊息
        "retryable": strategy.should_retry and retry_count < strategy.max_retries,
        "retry_info": {
            "max_retries": strategy.max_retries,
            "current_retry": retry_count,
            "delay_seconds": strategy.delay_seconds,
            "will_change_proxy": strategy.change_proxy,
            "will_downgrade": strategy.downgrade_quality,
        } if strategy.should_retry else None
    }


class SmartRetryManager:
    """智能重試管理器"""

    def __init__(self):
        self.task_retries: Dict[str, Dict[str, Any]] = {}

    def start_task(self, task_id: str, initial_format: str):
        """開始追蹤任務"""
        self.task_retries[task_id] = {
            "retry_count": 0,
            "current_format": initial_format,
            "errors": [],
            "proxies_tried": set(),
        }

    def should_retry(self, task_id: str, error_message: str) -> Tuple[bool, Dict[str, Any]]:
        """
        判斷是否應該重試

        Args:
            task_id: 任務 ID
            error_message: 錯誤訊息

        Returns:
            (是否重試, 重試資訊)
        """
        if task_id not in self.task_retries:
            self.start_task(task_id, "best")

        task_info = self.task_retries[task_id]
        category, strategy = classify_error(error_message)

        # 記錄錯誤
        task_info["errors"].append({
            "category": category.value,
            "message": error_message[:200],
            "retry_count": task_info["retry_count"]
        })

        # 判斷是否應該重試
        if not strategy.should_retry:
            return False, format_error_response(
                error_message, category, strategy, task_info["retry_count"]
            )

        if task_info["retry_count"] >= strategy.max_retries:
            return False, format_error_response(
                error_message, category, strategy, task_info["retry_count"]
            )

        # 準備重試資訊
        retry_info = {
            "should_retry": True,
            "delay": strategy.delay_seconds,
            "change_proxy": strategy.change_proxy,
            "message": strategy.message_zh,
        }

        # 處理格式降級
        if strategy.downgrade_quality:
            new_format = get_downgraded_format(task_info["current_format"])
            if new_format:
                task_info["current_format"] = new_format
                retry_info["new_format"] = new_format
                retry_info["message"] = f"格式降級到 {new_format}"
            else:
                # 已經是最低畫質，不再重試
                return False, format_error_response(
                    error_message, category, strategy, task_info["retry_count"]
                )

        task_info["retry_count"] += 1
        return True, retry_info

    def get_current_format(self, task_id: str) -> str:
        """取得任務當前格式"""
        if task_id in self.task_retries:
            return self.task_retries[task_id]["current_format"]
        return "best"

    def record_proxy_used(self, task_id: str, proxy: str):
        """記錄使用過的代理"""
        if task_id in self.task_retries:
            self.task_retries[task_id]["proxies_tried"].add(proxy)

    def cleanup_task(self, task_id: str):
        """清理任務記錄"""
        self.task_retries.pop(task_id, None)

    def get_task_errors(self, task_id: str) -> list:
        """取得任務的錯誤歷史"""
        if task_id in self.task_retries:
            return self.task_retries[task_id]["errors"]
        return []


# 全域實例
retry_manager = SmartRetryManager()
