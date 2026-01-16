"""
异步桶管理类

注意：由于 MinIO 官方客户端本身是同步的，这里使用 asyncio 在线程池中运行同步操作
"""

import asyncio
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

from minio import Minio
from minio.error import S3Error

from ..sync.buckets import BucketManager as SyncBucketManager


class AsyncBucketManager:
    """
    异步 MinIO 桶管理类

    使用线程池在后台执行同步操作，提供异步接口
    """

    def __init__(self, client: Minio, executor: ThreadPoolExecutor = None):
        """
        初始化异步桶管理器

        Args:
            client: MinIO 客户端
            executor: 线程池执行器，如果为 None 则创建默认执行器
        """
        self.client = client
        self.executor = executor
        self._owned_executor = executor is None

        # 创建同步包装器
        self._sync_manager = SyncBucketManager(client)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        """关闭资源"""
        if self._owned_executor and self.executor:
            self.executor.shutdown(wait=True)

    def _run_in_executor(self, func, *args, **kwargs):
        """在线程池中执行同步函数"""
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(self.executor, lambda: func(*args, **kwargs))

    async def create_bucket(self, bucket_name: str, location: str = None) -> bool:
        """创建桶"""
        return await self._run_in_executor(
            self._sync_manager.create_bucket, bucket_name, location
        )

    async def delete_bucket(self, bucket_name: str, force: bool = False) -> bool:
        """删除桶"""
        return await self._run_in_executor(
            self._sync_manager.delete_bucket, bucket_name, force
        )

    async def bucket_exists(self, bucket_name: str) -> bool:
        """检查桶是否存在"""
        return await self._run_in_executor(
            self._sync_manager.bucket_exists, bucket_name
        )

    async def list_buckets(self) -> List[Dict[str, Any]]:
        """列出所有桶"""
        return await self._run_in_executor(self._sync_manager.list_buckets)

    async def get_bucket_info(self, bucket_name: str) -> Optional[Dict[str, Any]]:
        """获取桶信息"""
        return await self._run_in_executor(self._sync_manager.get_bucket_info, bucket_name)
