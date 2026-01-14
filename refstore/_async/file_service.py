"""
异步文件服务类

注意：由于 MinIO 官方客户端本身是同步的，这里使用 asyncio 在线程池中运行同步操作
"""

import asyncio
import os
import io
from typing import Optional, BinaryIO, Union, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

from minio import Minio

from ..sync.file_service import MinioFileService as SyncMinioFileService
from ..core.config import ConfigValidator
from ..utils.uri import URIUtils


class AsyncMinioFileService:
    """
    异步 MinIO 文件服务类

    提供与同步 API 相同的方法签名，但在后台使用线程池执行同步操作
    """

    def __init__(self, config: Dict[str, Any], executor: ThreadPoolExecutor = None):
        """
        初始化异步文件服务

        Args:
            config: 配置字典
            executor: 线程池执行器，如果为 None 则创建默认执行器
        """
        self.config = ConfigValidator.normalize_config(config)
        self.executor = executor
        self._owned_executor = executor is None

        # 创建同步文件服务实例
        self._sync_service = SyncMinioFileService(self.config)

        # 线程池（如果没有提供）
        if self._owned_executor:
            self.executor = ThreadPoolExecutor(max_workers=10)

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

    # 属性访问
    @property
    def endpoint(self) -> str:
        return self._sync_service.endpoint

    @property
    def secure(self) -> bool:
        return self._sync_service.secure

    @property
    def bucket_map(self) -> Dict[str, str]:
        return self._sync_service.bucket_map

    @property
    def default_bucket(self) -> str:
        return self._sync_service.default_bucket

    @property
    def presigned_expiry(self) -> int:
        return self._sync_service.presigned_expiry

    # 桶初始化
    async def init_buckets(self) -> None:
        """初始化所有配置的物理桶"""
        await self._run_in_executor(self._sync_service.init_buckets)

    def get_physical_bucket(self, logic_bucket: str) -> str:
        """逻辑桶名 -> 物理桶名（同步方法）"""
        return self._sync_service.get_physical_bucket(logic_bucket)

    # ==========================================
    # 上传方法
    # ==========================================

    async def upload_file(
        self,
        file_data: Union[bytes, BinaryIO],
        original_filename: str = "file",
        content_type: str = "application/octet-stream",
        logic_bucket: Optional[str] = None,
        path: Optional[str] = None
    ) -> Optional[str]:
        """
        上传文件

        :param file_data: 文件数据（bytes 或 BinaryIO）
        :param original_filename: 原始文件名
        :param content_type: 内容类型
        :param logic_bucket: 逻辑桶名（会映射到物理桶）
        :param path: 指定的相对路径（可选）
        :return: S3 URI (如 s3://user/path/file.ext) 或 None
        """
        return await self._run_in_executor(
            self._sync_service.upload_file,
            file_data, original_filename, content_type, logic_bucket, path
        )

    async def upload_from_local(
        self,
        local_path: str,
        logic_bucket: Optional[str] = None,
        path: Optional[str] = None,
        content_type: Optional[str] = None
    ) -> Optional[str]:
        """从本地路径上传文件"""
        return await self._run_in_executor(
            self._sync_service.upload_from_local,
            local_path, logic_bucket, path, content_type
        )

    async def upload_from_url(
        self,
        url: str,
        logic_bucket: Optional[str] = None,
        path: Optional[str] = None,
        timeout: int = 30
    ) -> Optional[str]:
        """从 URL 下载并上传文件"""
        return await self._run_in_executor(
            self._sync_service.upload_from_url,
            url, logic_bucket, path, timeout
        )

    # ==========================================
    # 下载方法
    # ==========================================

    async def download_file(self, s3_uri: str) -> Optional[bytes]:
        """下载文件到内存"""
        return await self._run_in_executor(
            self._sync_service.download_file, s3_uri
        )

    async def download_to_local(
        self,
        s3_uri: str,
        local_path: str,
        create_dirs: bool = True
    ) -> bool:
        """下载文件到本地路径"""
        return await self._run_in_executor(
            self._sync_service.download_to_local,
            s3_uri, local_path, create_dirs
        )

    # ==========================================
    # URL 生成方法
    # ==========================================

    async def get_presigned_url(
        self,
        s3_uri: str,
        expiry_seconds: int = None,
        method: str = "GET"
    ) -> Optional[str]:
        """生成预签名 URL"""
        return await self._run_in_executor(
            self._sync_service.get_presigned_url,
            s3_uri, expiry_seconds, method
        )

    async def get_download_url(self, s3_uri: str, expiry_seconds: int = None) -> Optional[str]:
        """生成下载 URL"""
        return await self._run_in_executor(
            self._sync_service.get_download_url,
            s3_uri, expiry_seconds
        )

    # ==========================================
    # 文件信息方法
    # ==========================================

    async def get_file_info(self, s3_uri: str) -> Optional[Dict[str, Any]]:
        """根据 URI 获取文件信息"""
        return await self._run_in_executor(
            self._sync_service.get_file_info, s3_uri
        )

    async def file_exists(self, s3_uri: str) -> bool:
        """检查文件是否存在"""
        return await self._run_in_executor(
            self._sync_service.file_exists, s3_uri
        )

    # ==========================================
    # 删除方法
    # ==========================================

    async def delete_file(self, s3_uri: str) -> bool:
        """删除文件"""
        return await self._run_in_executor(
            self._sync_service.delete_file, s3_uri
        )

    async def delete_files(self, s3_uris: List[str]) -> Dict[str, Any]:
        """批量删除文件"""
        return await self._run_in_executor(
            self._sync_service.delete_files, s3_uris
        )

    # ==========================================
    # 列表方法
    # ==========================================

    async def list_files(
        self,
        logic_bucket: Optional[str] = None,
        prefix: str = "",
        recursive: bool = True
    ) -> List[Dict[str, Any]]:
        """列出桶中的文件"""
        return await self._run_in_executor(
            self._sync_service.list_files,
            logic_bucket, prefix, recursive
        )
