# RefStore

[![PyPI version](https://img.shields.io/pypi/v/refstore)](https://pypi.org/project/refstore/)
[![Python versions](https://img.shields.io/pypi/pyversions/refstore)](https://pypi.org/project/refstore/)
[![License](https://img.shields.io/pypi/l/refstore)](LICENSE)
[![codecov](https://codecov.io/gh/yourusername/refstore/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/refstore)

简单易用的 MinIO 对象存储服务封装库

## 特性

- **同步/异步 API** - 提供完整的同步和异步接口
- **Web API (FastAPI)** - 基于 FastAPI 的 RESTful 接口
- **S3 URI 编码/解码** - 统一的文件标识：`s3://bucket/path/to/file`
- **逻辑桶名映射** - 支持逻辑桶名到物理桶名的映射
- **配置验证** - 内置配置格式验证和连接测试
- **重试机制** - 带指数退避的自动重试
- **完整的文档和示例** - 包含丰富的使用示例和测试用例

## 安装

### 基础安装

```bash
pip install refstore
```

### 完整安装（包含 Web API）

```bash
pip install refstore[web]
```

### 开发安装

```bash
pip install refstore[dev]
```

## 快速开始

### 同步 API

```python
from refstore import RefStore

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

# 初始化服务
store = RefStore(config)
store.init_buckets()

# 上传文件
uri = store.upload_file(
    file_data=b"Hello, RefStore!",
    original_filename="test.txt",
    content_type="text/plain",
    logic_bucket="user",
    path="documents"
)
print(f"文件已上传: {uri}")  # s3://user/documents/test.txt

# 生成预签名 URL
url = store.get_presigned_url(uri, expiry_seconds=3600)
print(f"下载 URL: {url}")

# 下载文件
data = store.download_file(uri)
print(f"文件内容: {data.decode('utf-8')}")

# 获取文件信息
info = store.get_file_info(uri)
print(f"文件大小: {info['size_human']}")

# 列出文件
files = store.list_files(logic_bucket="user")
print(f"找到 {len(files)} 个文件")
```

### 异步 API

```python
import asyncio
from refstore import AsyncRefStore

config = {
    "minio": {
        "endpoint": "localhost:9000",
        "access_key": "your_access_key",
        "secret_key": "your_secret_key",
        "secure": False,
    },
}

async def main():
    async with AsyncRefStore(config) as store:
        # 上传文件
        uri = await store.upload_file(
            file_data=b"Hello, Async RefStore!",
            original_filename="async_test.txt",
            logic_bucket="user"
        )

        # 下载文件
        data = await store.download_file(uri)
        print(data.decode('utf-8'))

        # 并发上传多个文件
        tasks = [
            store.upload_file(b"File 1", "file1.txt", "user")
            for _ in range(10)
        ]
        uris = await asyncio.gather(*tasks)

asyncio.run(main())
```

### Web API

启动 Web 服务：

```python
from refstore import web_app, init_web_service

config = {
    "minio": {
        "endpoint": "localhost:9000",
        "access_key": "your_access_key",
        "secret_key": "your_secret_key",
        "secure": False,
    },
}

# 初始化 Web 服务
init_web_service(config)

# 启动服务器
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(web_app, host="0.0.0.0", port=8000)
```

或使用命令行：

```bash
uvicorn refstore.web:web_app --host 0.0.0.0 --port 8000 --reload
```

访问 API 文档：http://localhost:8000/docs

### Web API 客户端

```python
import requests

# 上传文件
with open("test.txt", "rb") as f:
    files = {"file": f}
    data = {"logic_bucket": "user"}
    response = requests.post("http://localhost:8000/upload", files=files, data=data)
    result = response.json()
    uri = result["uri"]

# 下载文件
params = {"uri": uri}
response = requests.get("http://localhost:8000/download", params=params)
with open("downloaded.txt", "wb") as f:
    f.write(response.content)

# 获取文件信息
params = {"uri": uri}
response = requests.get("http://localhost:8000/info", params=params)
info = response.json()

# 生成预签名 URL
params = {"uri": uri, "expiry_seconds": 3600}
response = requests.get("http://localhost:8000/presigned-url", params=params)
presigned_url = response.json()["url"]
```

## 配置

### 完整配置示例

```python
config = {
    # MinIO 连接配置（必需）
    "minio": {
        "endpoint": "localhost:9000",      # MinIO 服务器地址
        "access_key": "your_access_key",    # 访问密钥
        "secret_key": "your_secret_key",    # 秘密密钥
        "secure": False,                    # 是否使用 HTTPS
    },

    # 逻辑桶名到物理桶名的映射（可选）
    "bucket_map": {
        "user": "physical-user-bucket",
        "public": "physical-public-bucket",
        "temp": "physical-temp-bucket",
    },

    # 默认逻辑桶名（可选，默认为 "user"）
    "default_bucket": "user",

    # 预签名 URL 过期时间（可选，默认为 3600 秒）
    "presigned_expiry": 3600,
}
```

### 配置验证

```python
from refstore import ConfigValidator

# 验证配置
try:
    config = ConfigValidator.normalize_config(your_config)
    print("配置有效")
except ConfigError as e:
    print(f"配置无效: {e}")

# 测试连接
try:
    ConfigValidator.test_connection(config)
    print("连接成功")
except ConnectionError as e:
    print(f"连接失败: {e}")
```

## URI 操作

RefStore 使用标准化的 S3 URI 格式：`s3://logic_bucket/path/to/file`

```python
from refstore import encode_uri, decode_uri, validate_uri, get_bucket_from_uri

# 编码 URI
uri = encode_uri("user", "documents/report.pdf")
# s3://user/documents/report.pdf

# 解码 URI
bucket, object_name = decode_uri(uri)
# bucket: user, object_name: documents/report.pdf

# 验证 URI
is_valid = validate_uri(uri)
# True

# 提取桶名
bucket = get_bucket_from_uri(uri)
# user

# 提取对象名称
object_name = get_object_name_from_uri(uri)
# documents/report.pdf

# 获取文件扩展名
ext = get_file_extension(uri)
# .pdf
```

## 高级功能

### 重试机制

```python
from refstore import retry_with_backoff

@retry_with_backoff(max_retries=3, base_delay=1.0)
def upload_with_retry(store, data, filename):
    return store.upload_file(data, filename)
```

### 桶管理

```python
from refstore import BucketManager

# 创建桶管理器
bucket_manager = BucketManager(minio_client)

# 创建桶
bucket_manager.create_bucket("my-bucket")

# 检查桶是否存在
exists = bucket_manager.bucket_exists("my-bucket")

# 列出所有桶
buckets = bucket_manager.list_buckets()

# 获取桶信息
info = bucket_manager.get_bucket_info("my-bucket")

# 删除桶
bucket_manager.delete_bucket("my-bucket", force=True)
```

### 批量操作

```python
# 批量删除文件
uris = [
    "s3://user/file1.txt",
    "s3://user/file2.txt",
    "s3://user/file3.txt",
]
result = store.delete_files(uris)
print(f"删除成功: {len(result['deleted'])}")
print(f"删除失败: {len(result['failed'])}")
```

## 示例

查看 `examples/` 目录获取更多使用示例：

- `basic_usage.py` - 同步 API 基础用法
- `async_usage.py` - 异步 API 用法
- `web_service.py` - Web API 服务启动
- `web_client.py` - Web API 客户端使用
- `config_validation.py` - 配置验证示例

运行示例：

```bash
# 基础示例
python examples/basic_usage.py

# 异步示例
python examples/async_usage.py

# Web 服务
python examples/web_service.py

# 配置验证
python examples/config_validation.py
```

## API 文档

### 同步 API

- `RefStore` - 同步文件服务类
  - `upload_file()` - 上传文件
  - `upload_from_local()` - 从本地路径上传
  - `upload_from_url()` - 从 URL 上传
  - `download_file()` - 下载文件到内存
  - `download_to_local()` - 下载文件到本地
  - `get_presigned_url()` - 生成预签名 URL
  - `get_file_info()` - 获取文件信息
  - `file_exists()` - 检查文件是否存在
  - `delete_file()` - 删除文件
  - `delete_files()` - 批量删除文件
  - `list_files()` - 列出文件

### 异步 API

- `AsyncRefStore` - 异步文件服务类（方法签名与同步 API 相同）

### Web API 端点

- `POST /upload` - 上传文件
- `GET /download` - 下载文件
- `GET /presigned-url` - 生成预签名 URL
- `GET /info` - 获取文件信息
- `DELETE /delete` - 删除文件
- `GET /list` - 列出文件
- `GET /health` - 健康检查

## 开发

### 运行测试

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=refstore --cov-report=html
```

### 代码格式化

```bash
# 使用 Black 格式化代码
black refstore tests examples

# 使用 isort 排序导入
isort refstore tests examples
```

### 代码检查

```bash
# 使用 flake8 检查代码
flake8 refstore tests examples

# 使用 mypy 进行类型检查
mypy refstore
```

## 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解如何参与贡献。

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 问题反馈

如果你遇到问题或有建议，请在 [GitHub Issues](https://github.com/yourusername/refstore/issues) 中提出。

## 致谢

- [MinIO](https://min.io/) - 高性能的对象存储
- [FastAPI](https://fastapi.tiangolo.com/) - 现代、快速的 Web 框架
