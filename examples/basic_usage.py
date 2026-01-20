"""
RefStore 基础使用示例

演示同步 API 的基本用法
"""

from refstore import RefStore, ConfigValidator, encode_uri, decode_uri


def main():
    # 配置 RefStore
    config = {
            "minio": {
                "endpoint": "10.31.31.41:9000",
                "access_key": "qichen",
                "secret_key": "qichen1997",
                "secure": False,
            },
            "bucket_map": {
                "user": "physical-user-bucket",
                "public": "physical-public-bucket",
            },
            "default_bucket": "user",
            "presigned_expiry": 3600,
            "public_url": "https://shclzczy.odb.sh.cn/cdip-file-system/",
    }

    # 验证配置
    try:
        ConfigValidator.validate_config(config)
        print("[OK] 配置验证通过")
    except Exception as e:
        print(f"[ERROR] 配置验证失败: {e}")
        return

    # 初始化 RefStore 服务
    store = RefStore(config)

    # 初始化所有桶（如果不存在则创建）
    store.init_buckets()

    # 上传文件（字节数据）
    print("\n=== 上传文件 ===")
    file_data = b"Hello, RefStore! This is a test file."
    uri = store.upload_file(
        file_data=file_data,
        original_filename="test.txt",
        content_type="text/plain",
        logic_bucket="user",
        path="documents"
    )
    print(f"文件已上传: {uri}")

    # 上传本地文件
    print("\n=== 上传本地文件 ===")
    # uri = store.upload_from_local(
    #     local_path="/path/to/local/file.txt",
    #     logic_bucket="user",
    #     path="documents"
    # )
    # print(f"本地文件已上传: {uri}")

    # 从 URL 上传
    print("\n=== 从 URL 上传 ===")
    # uri = store.upload_from_url(
    #     url="https://example.com/file.txt",
    #     logic_bucket="public"
    # )
    # print(f"URL 文件已上传: {uri}")

    # 获取文件信息
    print("\n=== 获取文件信息 ===")
    file_info = store.get_file_info(uri)
    if file_info:
        print(f"逻辑桶: {file_info['logic_bucket']}")
        print(f"物理桶: {file_info['physical_bucket']}")
        print(f"对象名称: {file_info['object_name']}")
        print(f"文件大小: {file_info['size_human']}")
        print(f"内容类型: {file_info['content_type']}")

    # 检查文件是否存在
    print("\n=== 检查文件是否存在 ===")
    exists = store.file_exists(uri)
    print(f"文件存在: {exists}")

    # 生成预签名 URL
    print("\n=== 生成预签名 URL ===")
    presigned_url = store.get_presigned_url(uri, expiry_seconds=3600)
    print(f"下载 URL: {presigned_url}")

    # # 下载文件
    # print("\n=== 下载文件 ===")
    # downloaded_data = store.download_file(uri)
    # if downloaded_data:
    #     print(f"下载内容: {downloaded_data.decode('utf-8')}")

    # # 列出文件
    # print("\n=== 列出文件 ===")
    # files = store.list_files(logic_bucket="user", recursive=True)
    # print(f"找到 {len(files)} 个文件:")
    # for f in files[:5]:  # 只显示前5个
    #     print(f"  - {f['object_name']} ({f['size_human']})")

    # # URI 编码/解码示例
    # print("\n=== URI 操作 ===")
    # # 编码 URI
    # encoded_uri = encode_uri("user", "path/to/file.txt")
    # print(f"编码 URI: {encoded_uri}")

    # # 解码 URI
    # bucket, object_name = decode_uri(encoded_uri)
    # print(f"解码 URI - 桶: {bucket}, 对象: {object_name}")

    # # 删除文件
    # print("\n=== 删除文件 ===")
    # result = store.delete_file(uri)
    # print(f"文件删除: {'成功' if result else '失败'}")

    # 批量删除
    # uris = ["s3://user/file1.txt", "s3://user/file2.txt"]
    # result = store.delete_files(uris)
    # print(f"删除成功: {len(result['deleted'])} 个")
    # print(f"删除失败: {len(result['failed'])} 个")

    print("\n=== 示例完成 ===")


if __name__ == "__main__":
    main()
