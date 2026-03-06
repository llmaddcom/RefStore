"""
GatewayClient - 同步网关 SDK 客户端

通过 HTTP 连接 RefStore 网关服务，多项目可共享同一网关，
无需各自配置 MinIO 连接信息。
"""

import os
from typing import Optional, BinaryIO, Union, List, Dict, Any

import requests


class GatewayClient:
    """
    RefStore 网关同步客户端

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
        self.gateway_url = gateway_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        if headers:
            self.session.headers.update(headers)

    def close(self):
        """关闭 HTTP 会话"""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _url(self, path: str) -> str:
        return f"{self.gateway_url}{path}"

    def _raise_for_status(self, resp: requests.Response) -> None:
        if resp.status_code >= 400:
            try:
                detail = resp.json().get("detail", resp.text)
            except Exception:
                detail = resp.text
            raise RuntimeError(f"Gateway 请求失败 [{resp.status_code}]: {detail}")

    # ==========================================
    # 网关管理操作
    # ==========================================

    def get_status(self) -> Dict[str, Any]:
        """获取网关服务状态"""
        resp = self.session.get(self._url("/gateway/status"), timeout=self.timeout)
        self._raise_for_status(resp)
        return resp.json()

    def get_config(self) -> Dict[str, Any]:
        """获取网关配置（脱敏）"""
        resp = self.session.get(self._url("/gateway/config"), timeout=self.timeout)
        self._raise_for_status(resp)
        return resp.json()

    def list_buckets(self) -> Dict[str, Any]:
        """列出所有桶"""
        resp = self.session.get(self._url("/gateway/buckets"), timeout=self.timeout)
        self._raise_for_status(resp)
        return resp.json()

    def create_bucket(self, name: str, location: Optional[str] = None) -> Dict[str, Any]:
        """创建桶"""
        payload: Dict[str, Any] = {"name": name}
        if location:
            payload["location"] = location
        resp = self.session.post(
            self._url("/gateway/buckets"), json=payload, timeout=self.timeout
        )
        self._raise_for_status(resp)
        return resp.json()

    def get_bucket_info(self, name: str) -> Dict[str, Any]:
        """获取桶详情"""
        resp = self.session.get(self._url(f"/gateway/buckets/{name}"), timeout=self.timeout)
        self._raise_for_status(resp)
        return resp.json()

    def delete_bucket(self, name: str, force: bool = False) -> Dict[str, Any]:
        """删除桶"""
        params = {"force": str(force).lower()} if force else {}
        resp = self.session.delete(
            self._url(f"/gateway/buckets/{name}"), params=params, timeout=self.timeout
        )
        self._raise_for_status(resp)
        return resp.json()

    def get_bucket_mapping(self) -> Dict[str, Any]:
        """查看桶映射配置"""
        resp = self.session.get(self._url("/gateway/bucket-mapping"), timeout=self.timeout)
        self._raise_for_status(resp)
        return resp.json()

    def update_bucket_mapping(
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
        resp = self.session.put(
            self._url("/gateway/bucket-mapping"), json=payload, timeout=self.timeout
        )
        self._raise_for_status(resp)
        return resp.json()

    # ==========================================
    # 文件操作（通过网关代理）
    # ==========================================

    def upload_file(
        self,
        file_data: Union[bytes, BinaryIO],
        filename: str = "file",
        logic_bucket: Optional[str] = None,
        path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        上传文件

        :param file_data: 文件内容（bytes 或文件对象）
        :param filename: 文件名
        :param logic_bucket: 逻辑桶名
        :param path: 存储路径
        :return: 上传结果字典（包含 uri, success, message）
        """
        if isinstance(file_data, bytes):
            files = {"file": (filename, file_data)}
        else:
            files = {"file": (filename, file_data)}

        data: Dict[str, str] = {}
        if logic_bucket:
            data["logic_bucket"] = logic_bucket
        if path:
            data["path"] = path

        resp = self.session.post(
            self._url("/upload"), files=files, data=data, timeout=self.timeout
        )
        self._raise_for_status(resp)
        return resp.json()

    def upload_from_local(
        self,
        local_path: str,
        logic_bucket: Optional[str] = None,
        path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """从本地路径上传文件"""
        filename = os.path.basename(local_path)
        with open(local_path, "rb") as f:
            return self.upload_file(f, filename=filename, logic_bucket=logic_bucket, path=path)

    def download_file(self, uri: str) -> bytes:
        """
        下载文件

        :param uri: S3 URI
        :return: 文件内容 bytes
        """
        resp = self.session.get(
            self._url("/download"), params={"uri": uri}, timeout=self.timeout
        )
        self._raise_for_status(resp)
        return resp.content

    def download_to_local(self, uri: str, local_path: str) -> bool:
        """下载文件到本地"""
        try:
            data = self.download_file(uri)
            dir_path = os.path.dirname(local_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            with open(local_path, "wb") as f:
                f.write(data)
            return True
        except Exception:
            return False

    def get_presigned_url(
        self, uri: str, expiry_seconds: Optional[int] = None, method: str = "GET"
    ) -> Dict[str, Any]:
        """生成预签名 URL"""
        params: Dict[str, Any] = {"uri": uri, "method": method}
        if expiry_seconds is not None:
            params["expiry_seconds"] = expiry_seconds
        resp = self.session.get(
            self._url("/presigned-url"), params=params, timeout=self.timeout
        )
        self._raise_for_status(resp)
        return resp.json()

    def get_file_info(self, uri: str) -> Dict[str, Any]:
        """获取文件信息"""
        resp = self.session.get(
            self._url("/info"), params={"uri": uri}, timeout=self.timeout
        )
        self._raise_for_status(resp)
        return resp.json()

    def delete_file(self, uri: str) -> Dict[str, Any]:
        """删除单个文件"""
        return self.delete_files([uri])

    def delete_files(self, uris: List[str]) -> Dict[str, Any]:
        """批量删除文件"""
        resp = self.session.delete(
            self._url("/delete"), json={"uris": uris}, timeout=self.timeout
        )
        self._raise_for_status(resp)
        return resp.json()

    def list_files(
        self,
        logic_bucket: Optional[str] = None,
        prefix: str = "",
        recursive: bool = True,
    ) -> Dict[str, Any]:
        """列出文件"""
        params: Dict[str, Any] = {"prefix": prefix, "recursive": recursive}
        if logic_bucket:
            params["logic_bucket"] = logic_bucket
        resp = self.session.get(
            self._url("/list"), params=params, timeout=self.timeout
        )
        self._raise_for_status(resp)
        return resp.json()

    def health(self) -> Dict[str, Any]:
        """健康检查"""
        resp = self.session.get(self._url("/health"), timeout=self.timeout)
        self._raise_for_status(resp)
        return resp.json()
