# 发布指南

## 更新版本号

### 方法1: 使用脚本（推荐）

```bash
# 自动递增修订号（0.1.0 -> 0.1.1）
python update_version.py --patch

# 自动递增次版本号（0.1.0 -> 0.2.0）
python update_version.py --minor

# 自动递增主版本号（0.1.0 -> 1.0.0）
python update_version.py --major

# 或直接指定版本号
python update_version.py 0.2.0
```

### 方法2: 手动更新

需要同时更新两个文件：

1. **pyproject.toml**
```toml
[project]
version = "0.2.0"  # 更新这里
```

2. **refstore/__init__.py**
```python
__version__ = "0.2.0"  # 更新这里
```

## 构建和发布到 PyPI

### 1. 安装构建工具

```bash
pip install build twine
```

### 2. 清理旧的构建文件

```bash
rm -rf dist/ build/ *.egg-info/
```

### 3. 构建分发包

```bash
python -m build
```

这会生成：
- `dist/refstore-X.X.X.tar.gz` (源码包)
- `dist/refstore-X.X.X-py3-none-any.whl` (wheel包)

### 4. 检查构建的包

```bash
# 检查包内容
twine check dist/*

# 测试安装（可选）
pip install dist/refstore-X.X.X-py3-none-any.whl
```

### 5. 上传到 PyPI

#### 测试环境（TestPyPI）- 推荐先测试

```bash
# 上传到 TestPyPI
twine upload --repository testpypi dist/*

# 从 TestPyPI 测试安装
pip install --index-url https://test.pypi.org/simple/ refstore
```

#### 正式环境（PyPI）

```bash
# 上传到 PyPI
twine upload dist/*
```

**注意**: 
- 需要 PyPI 账号和 API token
- 可以在 https://pypi.org/manage/account/token/ 创建 token
- 使用 `__token__` 作为用户名，token 作为密码

### 6. 验证发布

```bash
# 等待几分钟后，尝试安装
pip install refstore --upgrade

# 检查版本
python -c "import refstore; print(refstore.__version__)"
```

## 版本号规范

遵循 [语义化版本](https://semver.org/lang/zh-CN/)：

- **主版本号** (MAJOR): 不兼容的 API 修改
- **次版本号** (MINOR): 向下兼容的功能性新增
- **修订号** (PATCH): 向下兼容的问题修正

示例：
- `0.1.0` → `0.1.1` - 修复bug（patch）
- `0.1.0` → `0.2.0` - 新增功能（minor）
- `0.1.0` → `1.0.0` - 重大变更（major）

## 发布检查清单

- [ ] 更新版本号（pyproject.toml 和 __init__.py）
- [ ] 更新 CHANGELOG.md（如果有）
- [ ] 运行测试确保通过
- [ ] 更新 README.md（如果需要）
- [ ] 构建包并检查
- [ ] 先上传到 TestPyPI 测试
- [ ] 上传到正式 PyPI
- [ ] 创建 Git tag: `git tag v0.2.0 && git push --tags`
- [ ] 创建 GitHub Release（如果有）

## 常见问题

### 1. 版本已存在错误

如果版本号已存在于 PyPI，需要：
- 使用新的版本号
- 或者删除旧版本（需要 PyPI 管理员权限）

### 2. 认证失败

确保：
- 使用正确的 API token
- token 有上传权限
- 用户名使用 `__token__`（注意前后各两个下划线）

### 3. 上传后无法立即安装

PyPI 的 CDN 可能需要几分钟同步，请稍候再试。
