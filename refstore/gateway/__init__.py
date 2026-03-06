"""
Gateway SDK 模块

提供 GatewayClient（同步）和 AsyncGatewayClient（异步）客户端，
用于通过 HTTP 连接 RefStore 网关服务，实现集中式文件管理。
各项目只需配置 gateway_url，无需知道 MinIO 的连接细节。
"""

from .client import GatewayClient
from .async_client import AsyncGatewayClient

__all__ = [
    "GatewayClient",
    "AsyncGatewayClient",
]
