#!/usr/bin/env python3
"""
版本更新脚本

用法:
    python update_version.py 0.1.1
    python update_version.py --patch   # 自动递增修订号
    python update_version.py --minor   # 自动递增次版本号
    python update_version.py --major   # 自动递增主版本号
"""

import re
import sys
from pathlib import Path


def get_current_version():
    """获取当前版本号"""
    # 从 pyproject.toml 读取
    pyproject_path = Path(__file__).parent / "pyproject.toml"
    with open(pyproject_path, "r", encoding="utf-8") as f:
        content = f.read()
        match = re.search(r'version\s*=\s*"([^"]+)"', content)
        if match:
            return match.group(1)
    raise ValueError("无法找到当前版本号")


def update_version(new_version: str):
    """更新版本号到指定位置"""
    project_root = Path(__file__).parent
    
    # 1. 更新 pyproject.toml
    pyproject_path = project_root / "pyproject.toml"
    with open(pyproject_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    content = re.sub(
        r'version\s*=\s*"[^"]+"',
        f'version = "{new_version}"',
        content
    )
    
    with open(pyproject_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✓ 已更新 pyproject.toml: version = {new_version}")
    
    # 2. 更新 refstore/__init__.py
    init_path = project_root / "refstore" / "__init__.py"
    with open(init_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    content = re.sub(
        r'__version__\s*=\s*"[^"]+"',
        f'__version__ = "{new_version}"',
        content
    )
    
    with open(init_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✓ 已更新 refstore/__init__.py: __version__ = {new_version}")


def increment_version(current_version: str, part: str) -> str:
    """递增版本号"""
    parts = current_version.split(".")
    if len(parts) != 3:
        raise ValueError(f"无效的版本号格式: {current_version}")
    
    major, minor, patch = map(int, parts)
    
    if part == "major":
        major += 1
        minor = 0
        patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    elif part == "patch":
        patch += 1
    else:
        raise ValueError(f"无效的版本部分: {part}")
    
    return f"{major}.{minor}.{patch}"


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python update_version.py <新版本号>")
        print("  python update_version.py --patch   # 自动递增修订号")
        print("  python update_version.py --minor   # 自动递增次版本号")
        print("  python update_version.py --major   # 自动递增主版本号")
        sys.exit(1)
    
    arg = sys.argv[1]
    
    if arg.startswith("--"):
        # 自动递增模式
        current_version = get_current_version()
        part = arg[2:]  # 移除 "--"
        new_version = increment_version(current_version, part)
        print(f"当前版本: {current_version}")
        print(f"新版本: {new_version}")
    else:
        # 直接指定版本号
        new_version = arg
        # 验证版本号格式
        if not re.match(r'^\d+\.\d+\.\d+$', new_version):
            print(f"错误: 无效的版本号格式 '{new_version}'，应为 '主版本号.次版本号.修订号'")
            sys.exit(1)
    
    update_version(new_version)
    print(f"\n✓ 版本已更新为: {new_version}")


if __name__ == "__main__":
    main()
