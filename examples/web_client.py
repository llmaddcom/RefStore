"""
RefStore Web API 客户端示例

演示如何使用 HTTP 客户端调用 RefStore Web API
"""

import requests
from pathlib import Path


class RefStoreWebClient:
    """RefStore Web API 客户端"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        初始化客户端

        Args:
            base_url: Web API 基础 URL
        """
        self.base_url = base_url.rstrip('/')

    def upload_file(self, file_path: str, logic_bucket: str = None, path: str = None) -> dict:
        """
        上传文件

        Args:
            file_path: 本地文件路径
            logic_bucket: 逻辑桶名
            path: 存储路径

        Returns:
            上传结果
        """
        url = f"{self.base_url}/upload"

        files = {"file": open(file_path, "rb")}
        data = {}

        if logic_bucket:
            data["logic_bucket"] = logic_bucket
        if path:
            data["path"] = path

        try:
            response = requests.post(url, files=files, data=data)
            response.raise_for_status()
            return response.json()
        finally:
            files["file"].close()

    def download_file(self, uri: str, save_path: str) -> bool:
        """
        下载文件

        Args:
            uri: S3 URI
            save_path: 本地保存路径

        Returns:
            是否下载成功
        """
        url = f"{self.base_url}/download"
        params = {"uri": uri}

        try:
            response = requests.get(url, params=params, stream=True)
            response.raise_for_status()

            # 确保目录存在
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)

            # 保存文件
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return True
        except Exception as e:
            print(f"下载失败: {e}")
            return False

    def get_presigned_url(self, uri: str, expiry_seconds: int = None) -> dict:
        """
        获取预签名 URL

        Args:
            uri: S3 URI
            expiry_seconds: 过期时间（秒）

        Returns:
            预签名 URL 信息
        """
        url = f"{self.base_url}/presigned-url"
        params = {"uri": uri}

        if expiry_seconds:
            params["expiry_seconds"] = expiry_seconds

        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_file_info(self, uri: str) -> dict:
        """
        获取文件信息

        Args:
            uri: S3 URI

        Returns:
            文件信息
        """
        url = f"{self.base_url}/info"
        params = {"uri": uri}

        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def delete_files(self, uris: list) -> dict:
        """
        删除文件

        Args:
            uris: S3 URI 列表

        Returns:
            删除结果
        """
        url = f"{self.base_url}/delete"
        payload = {"uris": uris}

        response = requests.delete(url, json=payload)
        response.raise_for_status()
        return response.json()

    def list_files(self, logic_bucket: str = None, prefix: str = "", recursive: bool = True) -> dict:
        """
        列出文件

        Args:
            logic_bucket: 逻辑桶名
            prefix: 文件前缀
            recursive: 是否递归

        Returns:
            文件列表
        """
        url = f"{self.base_url}/list"
        params = {
            "prefix": prefix,
            "recursive": recursive,
        }

        if logic_bucket:
            params["logic_bucket"] = logic_bucket

        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def health_check(self) -> dict:
        """
        健康检查

        Returns:
            健康状态
        """
        url = f"{self.base_url}/health"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()


def main():
    """示例：使用 Web API 客户端"""

    # 创建客户端
    client = RefStoreWebClient("http://localhost:8000")

    # 健康检查
    print("\n=== 健康检查 ===")
    try:
        health = client.health_check()
        print(f"状态: {health['status']}")
        print(f"消息: {health['message']}")
    except Exception as e:
        print(f"健康检查失败: {e}")
        return

    # 创建测试文件
    test_file = "/tmp/test_upload.txt"
    with open(test_file, 'w') as f:
        f.write("Hello from Web API client!")

    # 上传文件
    print("\n=== 上传文件 ===")
    try:
        result = client.upload_file(
            file_path=test_file,
            logic_bucket="user",
            path="documents"
        )
        print(f"上传成功: {result}")
        uri = result['uri']
    except Exception as e:
        print(f"上传失败: {e}")
        return

    # 获取文件信息
    print("\n=== 获取文件信息 ===")
    try:
        info = client.get_file_info(uri)
        print(f"文件存在: {info['exists']}")
        if info['info']:
            print(f"逻辑桶: {info['info']['logic_bucket']}")
            print(f"文件大小: {info['info']['size_human']}")
    except Exception as e:
        print(f"获取文件信息失败: {e}")

    # 生成预签名 URL
    print("\n=== 生成预签名 URL ===")
    try:
        presigned = client.get_presigned_url(uri, expiry_seconds=3600)
        print(f"预签名 URL: {presigned['url']}")
    except Exception as e:
        print(f"生成预签名 URL 失败: {e}")

    # 下载文件
    print("\n=== 下载文件 ===")
    download_path = "/tmp/test_download.txt"
    try:
        success = client.download_file(uri, download_path)
        if success:
            print(f"文件已下载到: {download_path}")
            with open(download_path) as f:
                print(f"内容: {f.read()}")
    except Exception as e:
        print(f"下载失败: {e}")

    # 列出文件
    print("\n=== 列出文件 ===")
    try:
        result = client.list_files(logic_bucket="user", recursive=True)
        print(f"找到 {len(result['files'])} 个文件:")
        for f in result['files'][:5]:
            print(f"  - {f['object_name']} ({f['size_human']})")
    except Exception as e:
        print(f"列出文件失败: {e}")

    # 删除文件
    print("\n=== 删除文件 ===")
    try:
        result = client.delete_files([uri])
        print(f"删除成功: {len(result['deleted'])} 个")
        print(f"删除失败: {len(result['failed'])} 个")
    except Exception as e:
        print(f"删除失败: {e}")

    print("\n=== 示例完成 ===")


if __name__ == "__main__":
    main()
