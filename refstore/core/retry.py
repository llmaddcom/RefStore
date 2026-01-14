"""重试机制模块"""

import time
import logging
from functools import wraps
from typing import Callable, Optional, List, Type, Tuple

from minio.error import S3Error

from .exceptions import ConnectionError

logger = logging.getLogger(__name__)


# 默认可重试的异常类型
DEFAULT_RETRY_EXCEPTIONS = (
    ConnectionError,
    S3Error,
    ConnectionResetError,
    TimeoutError,
    OSError,
)


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[int, Exception], None]] = None,
):
    """
    带指数退避的重试装饰器

    Args:
        max_retries: 最大重试次数（不包括首次调用）
        base_delay: 基础延迟时间（秒）
        max_delay: 最大延迟时间（秒）
        exponential_base: 指数退避的基数
        jitter: 是否添加随机抖动以避免惊群效应
        exceptions: 需要重试的异常类型，如果为 None 则使用默认异常
        on_retry: 重试时的回调函数，参数为 (retry_count, exception)

    Returns:
        装饰器函数

    Example:
        @retry_with_backoff(max_retries=3, base_delay=1)
        def upload_file():
            # 可能失败的操作
            pass
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retry_exceptions = exceptions or DEFAULT_RETRY_EXCEPTIONS
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retry_exceptions as e:
                    last_exception = e

                    # 如果是最后一次尝试，不再重试
                    if attempt == max_retries:
                        logger.error(
                            f"函数 {func.__name__} 在 {max_retries} 次重试后仍然失败: {e}"
                        )
                        raise

                    # 计算延迟时间
                    delay = min(base_delay * (exponential_base**attempt), max_delay)

                    # 添加随机抖动
                    if jitter:
                        import random

                        delay = delay * (0.5 + random.random())

                    logger.warning(
                        f"函数 {func.__name__} 第 {attempt + 1} 次尝试失败: {e}, "
                        f"{delay:.2f} 秒后重试..."
                    )

                    # 调用重试回调
                    if on_retry:
                        try:
                            on_retry(attempt + 1, e)
                        except Exception as callback_error:
                            logger.error(
                                f"重试回调函数执行失败: {callback_error}"
                            )

                    # 等待后重试
                    time.sleep(delay)

            # 理论上不会到达这里，但为了类型检查
            raise last_exception

        return wrapper

    return decorator


class RetryHandler:
    """重试处理器类"""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
    ):
        """
        初始化重试处理器

        Args:
            max_retries: 最大重试次数
            base_delay: 基础延迟时间
            max_delay: 最大延迟时间
            exponential_base: 指数退避基数
            jitter: 是否添加随机抖动
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

    def execute(
        self,
        func: Callable,
        *args,
        exceptions: Optional[Tuple[Type[Exception], ...]] = None,
        **kwargs,
    ):
        """
        执行带重试的函数

        Args:
            func: 要执行的函数
            *args: 函数的位置参数
            exceptions: 需要重试的异常类型
            **kwargs: 函数的关键字参数

        Returns:
            函数的返回值
        """
        retry_exceptions = exceptions or DEFAULT_RETRY_EXCEPTIONS
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except retry_exceptions as e:
                last_exception = e

                if attempt == self.max_retries:
                    logger.error(
                        f"函数 {func.__name__} 在 {self.max_retries} 次重试后仍然失败: {e}"
                    )
                    raise

                delay = min(
                    self.base_delay * (self.exponential_base**attempt), self.max_delay
                )

                if self.jitter:
                    import random

                    delay = delay * (0.5 + random.random())

                logger.warning(
                    f"函数 {func.__name__} 第 {attempt + 1} 次尝试失败: {e}, "
                    f"{delay:.2f} 秒后重试..."
                )

                time.sleep(delay)

        raise last_exception

    def execute_with_callback(
        self,
        func: Callable,
        *args,
        exceptions: Optional[Tuple[Type[Exception], ...]] = None,
        on_retry: Optional[Callable[[int, Exception], None]] = None,
        **kwargs,
    ):
        """
        执行带重试和回调的函数

        Args:
            func: 要执行的函数
            *args: 函数的位置参数
            exceptions: 需要重试的异常类型
            on_retry: 重试回调函数
            **kwargs: 函数的关键字参数

        Returns:
            函数的返回值
        """
        retry_exceptions = exceptions or DEFAULT_RETRY_EXCEPTIONS
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except retry_exceptions as e:
                last_exception = e

                if attempt == self.max_retries:
                    logger.error(
                        f"函数 {func.__name__} 在 {self.max_retries} 次重试后仍然失败: {e}"
                    )
                    raise

                delay = min(
                    self.base_delay * (self.exponential_base**attempt), self.max_delay
                )

                if self.jitter:
                    import random

                    delay = delay * (0.5 + random.random())

                logger.warning(
                    f"函数 {func.__name__} 第 {attempt + 1} 次尝试失败: {e}, "
                    f"{delay:.2f} 秒后重试..."
                )

                if on_retry:
                    try:
                        on_retry(attempt + 1, e)
                    except Exception as callback_error:
                        logger.error(
                            f"重试回调函数执行失败: {callback_error}"
                        )

                time.sleep(delay)

        raise last_exception
