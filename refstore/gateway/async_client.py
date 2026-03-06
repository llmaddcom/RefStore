"""
AsyncGatewayClient - 异步网关 SDK 客户端

基于 aiohttp 通过 HTTP 连接 RefStore 网关服务。
"""

import os
import asyncio
from typing import Optional, BinaryIO, Union, List, Dict, Any

try:
    import aiohttp
except ImportError:
    aiohttp = None  # type: ignore[assignment]


def _require_aiohttp():
    if aiohttp is None:
        raise ImportError(
            "AsyncGatewayClient 需要 aiohttp 库。请安装: pip install refstore[gateway]"
        )


class AsyncGatewayClient:
    """
    RefStore 网关异步客户端

    通过 HTTP API 与 RefStore 网关服务交互，提供文件操作和桶管理功能。

    Args:
        gateway_url: 网关服务基础 URL，如 "http://localhost:8000"
        timeout: 请求超时时间（秒），默认 30
        headers: 额外的请求头（如认证 token）
    """

    def __init__(
        self,
        gateway_url: str,
        timeout: int = 30,
        headers: Optional[Dict[str, str]] = None,
    ):
        _require_aiohttp()
        self.gateway_url = gateway_url.rstrip("/")
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._headers = headers
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> "aiohttp.ClientSession":
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=self.timeout, headers=self._headers
            )
        return self._session

    async def close(self):
        """关闭 HTTP 会话"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    def _url(self, path: str) -> str:
        return f"{self.gateway_url}{path}"

    @staticmethod
    async def _raise_for_status(resp: "aiohttp.ClientResponse") -> None:
        if resp.status >= 400:
            try:
                body = await resp.json()
                detail = body.get("detail", await resp.text())
            except Exception:
                detail = await resp.text()
            raise RuntimeError(f"Gateway 请求失败 [{resp.status}]: {detail}")

    # ==========================================
    # 网关管理操作
    # ==========================================

    async def get_status(self) -> Dict[str, Any]:
        """获取网关服务状态"""
        session = await self._get_session()
        async with session.get(self._url("/gateway/status")) as resp:
            await self._raise_for_status(resp)
            return await resp.json()

    async def get_config(self) -> Dict[str, Any]:
        """获取网关配置（脱敏）"""
        session = await self._get_session()
        async with session.get(self._url("/gateway/config")) as resp:
            await self._raise_for_status(resp)
            return await resp.json()

    async def list_buckets(self) -> Dict[str, Any]:
        """列出所有桶"""
        session = await self._get_session()
        async with session.get(self._url("/gateway/buckets")) as resp:
            await self._raise_for_status(resp)
            return await resp.json()

    async def create_bucket(
        self, name: str, location: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建桶"""
        payload: Dict[str, Any] = {"name": name}
        if location:
            payload["location"] = location
        session = await self._get_session()
        async with session.post(self._url("/gateway/buckets"), json=payload) as resp:
            await self._raise_for_status(resp)
            return await resp.json()

    async def get_bucket_info(self, name: str) -> Dict[str, Any]:
        """获取桶详情"""
        session = await self._get_session()
        async with session.get(self._url(f"/gateway/buckets/{name}")) as resp:
            await self._raise_for_status(resp)
            return await resp.json()

    async def delete_bucket(self, name: str, force: bool = False) -> Dict[str, Any]:
        """删除桶"""
        params = {"force": str(force).lower()} if force else {}
        session = await self._get_session()
        async with session.delete(
            self._url(f"/gateway/buckets/{name}"), params=params
        ) as resp:
            await self._raise_for_status(resp)
            return await resp.json()

    async def get_bucket_mapping(self) -> Dict[str, Any]:
        """查看桶映射配置"""
        session = await self._get_session()
        async with session.get(self._url("/gateway/bucket-mapping")) as resp:
            await self._raise_for_status(resp)
            return await resp.json()

    async def update_bucket_mapping(
        self,
        enable_bucket_mapping: Optional[bool] = None,
        bucket_map: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """更新桶映射配置"""
        payload: Dict[str, Any] = {}
        if enable_bucket_mapping is not None:
            payload["enable_bucket_mapping"] = enable_bucket_mapping
        if bucket_map is not None:
            payload["bucket_map"] = bucket_map
        session = await self._get_session()
        async with session.put(
            self._url("/gateway/bucket-mapping"), json=payload
        ) as resp:
            await self._raise_for_status(resp)
            return await resp.json()

    # ==========================================
    # 文件操作（通过网关代理）
    # ==========================================

    async def upload_file(
        self,
        file_data: Union[bytes, BinaryIO],
        filename: str = "file",
        logic_bucket: Optional[str] = None,
        path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """上传文件"""
        form = aiohttp.FormData()
        if isinstance(file_data, bytes):
            form.add_field("file", file_data, filename=filename)
        else:
            content = file_data.read()
            form.add_field("file", content, filename=filename)
        if logic_bucket:
            form.add_field("logic_bucket", logic_bucket)
        if path:
            form.add_field("path", path)

        session = await self._get_session()
        async with session.post(self._url("/upload"), data=form) as resp:
            await self._raise_for_status(resp)
            return await resp.json()

    async def upload_from_local(
        self,
        local_path: str,
        logic_bucket: Optional[str] = None,
        path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """从本地路径上传文件"""
        filename = os.path.basename(local_path)
        with open(local_path, "rb") as f:
            data = f.read()
        return await self.upload_file(data, filename=filename, logic_bucket=logic_bucket, path=path)

    async def download_file(self, uri: str) -> bytes:
        """下载文件"""
        session = await self._get_session()
        async with session.get(self._url("/download"), params={"uri": uri}) as resp:
            await self._raise_for_status(resp)
            return await resp.read()

    async def download_to_local(self, uri: str, local_path: str) -> bool:
        """下载文件到本地"""
        try:
            data = await self.download_file(uri)
            dir_path = os.path.dirname(local_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            with open(local_path, "wb") as f:
                f.write(data)
            return True
        except Exception:
            return False

    async def get_presigned_url(
        self, uri: str, expiry_seconds: Optional[int] = None, method: str = "GET"
    ) -> Dict[str, Any]:
        """生成预签名 URL"""
        params: Dict[str, Any] = {"uri": uri, "method": method}
        if expiry_seconds is not None:
            params["expiry_seconds"] = expiry_seconds
        session = await self._get_session()
        async with session.get(self._url("/presigned-url"), params=params) as resp:
            await self._raise_for_status(resp)
            return await resp.json()

    async def get_file_info(self, uri: str) -> Dict[str, Any]:
        """获取文件信息"""
        session = await self._get_session()
        async with session.get(self._url("/info"), params={"uri": uri}) as resp:
            await self._raise_for_status(resp)
            return await resp.json()

    async def delete_file(self, uri: str) -> Dict[str, Any]:
        """删除单个文件"""
        return await self.delete_files([uri])

    async def delete_files(self, uris: List[str]) -> Dict[str, Any]:
        """批量删除文件"""
        session = await self._get_session()
        async with session.delete(self._url("/delete"), json={"uris": uris}) as resp:
            await self._raise_for_status(resp)
            return await resp.json()

    async def list_files(
        self,
        logic_bucket: Optional[str] = None,
        prefix: str = "",
        recursive: bool = True,
    ) -> Dict[str, Any]:
        """列出文件"""
        params: Dict[str, Any] = {"prefix": prefix, "recursive": recursive}
        if logic_bucket:
            params["logic_bucket"] = logic_bucket
        session = await self._get_session()
        async with session.get(self._url("/list"), params=params) as resp:
            await self._raise_for_status(resp)
            return await resp.json()

    async def health(self) -> Dict[str, Any]:
        """健康检查"""
        session = await self._get_session()
        async with session.get(self._url("/health")) as resp:
            await self._raise_for_status(resp)
            return await resp.json()
