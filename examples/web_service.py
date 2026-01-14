"""
RefStore Web API 服务示例

演示如何使用 FastAPI 启动 RefStore Web 服务
"""

import uvicorn
from refstore import web_app, init_web_service


def main():
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

    # 初始化 Web 服务
    init_web_service(config)

    # 启动 FastAPI 服务器
    # 访问 http://localhost:8000 查看 API 文档
    uvicorn.run(
        web_app,
        host="0.0.0.0",
        port=8000,
        reload=True,  # 开发模式下启用热重载
    )


if __name__ == "__main__":
    main()
