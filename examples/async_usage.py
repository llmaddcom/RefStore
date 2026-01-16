"""
RefStore 异步 API 使用示例

演示异步 API 的基本用法
"""

import asyncio
from refstore import AsyncRefStore


async def main():
    # 配置 RefStore
    config = {
        "minio": {
            "endpoint": "localhost:9000",
            "access_key": "your_access_key",
            "secret_key": "your_secret_key",
            "secure": False,
        },
        "bucket_map": {
            "user": "physical-user-bucket",
            "public": "physical-public-bucket",
        },
        "default_bucket": "user",
        "presigned_expiry": 3600,
    }

    # 使用上下文管理器自动初始化和清理资源
    async with AsyncRefStore(config) as store:
        # 初始化所有桶
        await store.init_buckets()

        # 上传文件（字节数据）
        print("\n=== 异步上传文件 ===")
        file_data = b"Hello, Async RefStore! This is a test file."
        uri = await store.upload_file(
            file_data=file_data,
            original_filename="async_test.txt",
            content_type="text/plain",
            logic_bucket="user",
            path="documents"
        )
        print(f"文件已上传: {uri}")

        # 上传本地文件
        print("\n=== 异步上传本地文件 ===")
        # uri = await store.upload_from_local(
        #     local_path="/path/to/local/file.txt",
        #     logic_bucket="user",
        #     path="documents"
        # )
        # print(f"本地文件已上传: {uri}")

        # 从 URL 上传
        print("\n=== 异步从 URL 上传 ===")
        # uri = await store.upload_from_url(
        #     url="https://example.com/file.txt",
        #     logic_bucket="public"
        # )
        # print(f"URL 文件已上传: {uri}")

        # 获取文件信息
        print("\n=== 获取文件信息 ===")
        file_info = await store.get_file_info(uri)
        if file_info:
            print(f"逻辑桶: {file_info['logic_bucket']}")
            print(f"物理桶: {file_info['physical_bucket']}")
            print(f"对象名称: {file_info['object_name']}")
            print(f"文件大小: {file_info['size_human']}")
            print(f"内容类型: {file_info['content_type']}")

        # 检查文件是否存在
        print("\n=== 检查文件是否存在 ===")
        exists = await store.file_exists(uri)
        print(f"文件存在: {exists}")

        # 生成预签名 URL
        print("\n=== 生成预签名 URL ===")
        presigned_url = await store.get_presigned_url(uri, expiry_seconds=3600)
        print(f"下载 URL: {presigned_url}")

        # 下载文件
        print("\n=== 下载文件 ===")
        downloaded_data = await store.download_file(uri)
        if downloaded_data:
            print(f"下载内容: {downloaded_data.decode('utf-8')}")

        # 列出文件
        print("\n=== 列出文件 ===")
        files = await store.list_files(logic_bucket="user", recursive=True)
        print(f"找到 {len(files)} 个文件:")
        for f in files[:5]:  # 只显示前5个
            print(f"  - {f['object_name']} ({f['size_human']})")

        # 删除文件
        print("\n=== 删除文件 ===")
        # result = await store.delete_file(uri)
        # print(f"文件删除: {'成功' if result else '失败'}")

        # 批量删除
        # uris = ["s3://user/file1.txt", "s3://user/file2.txt"]
        # result = await store.delete_files(uris)
        # print(f"删除成功: {len(result['deleted'])} 个")
        # print(f"删除失败: {len(result['failed'])} 个")

        print("\n=== 异步示例完成 ===")


async def upload_multiple_files():
    """演示并发上传多个文件"""
    config = {
        "minio": {
            "endpoint": "localhost:9000",
            "access_key": "your_access_key",
            "secret_key": "your_secret_key",
            "secure": False,
        },
        "default_bucket": "user",
    }

    async with AsyncRefStore(config) as store:
        # 并发上传多个文件
        files_to_upload = [
            (b"File 1 content", "file1.txt"),
            (b"File 2 content", "file2.txt"),
            (b"File 3 content", "file3.txt"),
        ]

        tasks = [
            store.upload_file(data, filename, "text/plain", "user", "batch")
            for data, filename in files_to_upload
        ]

        uris = await asyncio.gather(*tasks)
        print(f"\n并发上传完成，上传了 {len(uris)} 个文件:")
        for uri in uris:
            print(f"  - {uri}")


if __name__ == "__main__":
    # 运行基础示例
    asyncio.run(main())

    # 运行并发上传示例
    # asyncio.run(upload_multiple_files())
