"""
平台检测和环境检查脚本
"""
import sys
import platform
import subprocess
from pathlib import Path


def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    print(f"✓ Python版本: {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("❌ Python版本过低，需要 Python 3.9+")
        return False

    return True


def check_platform():
    """检测操作系统"""
    system = platform.system()
    machine = platform.machine()

    print(f"✓ 操作系统: {system}")
    print(f"✓ 架构: {machine}")

    return system, machine


def check_package(package_name):
    """检查Python包是否已安装"""
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False


def check_dependencies():
    """检查关键依赖"""
    print("\n检查依赖:")

    dependencies = {
        "fastapi": "FastAPI",
        "sqlalchemy": "SQLAlchemy",
        "numpy": "NumPy",
        "faiss": "Faiss (faiss-cpu)",
        "pydantic": "Pydantic",
        "uvicorn": "Uvicorn",
    }

    missing = []
    for package, name in dependencies.items():
        if check_package(package):
            print(f"  ✓ {name}")
        else:
            print(f"  ❌ {name} 未安装")
            missing.append(package)

    return missing


def check_postgresql():
    """检查PostgreSQL是否安装"""
    print("\n检查PostgreSQL:")

    try:
        # 尝试运行 psql --version
        result = subprocess.run(
            ["psql", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"  ✓ PostgreSQL已安装: {version}")
            return True
        else:
            print("  ❌ PostgreSQL未安装或未在PATH中")
            return False
    except FileNotFoundError:
        print("  ❌ PostgreSQL未安装")
        return False
    except Exception as e:
        print(f"  ⚠️  无法检测PostgreSQL: {e}")
        return False


def check_directories():
    """检查必要的目录"""
    print("\n检查目录结构:")

    dirs = ["config", "data", "logs", "database", "models", "core", "api"]

    for dir_name in dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"  ✓ {dir_name}/")
        else:
            print(f"  ❌ {dir_name}/ 不存在")
            # 创建目录
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"    → 已创建 {dir_name}/")
            except Exception as e:
                print(f"    → 创建失败: {e}")


def check_config_file():
    """检查配置文件"""
    print("\n检查配置文件:")

    config_file = Path("config/config.yaml")
    if config_file.exists():
        print(f"  ✓ config/config.yaml 存在")
        return True
    else:
        print(f"  ❌ config/config.yaml 不存在")
        return False


def get_installation_instructions(system, missing_deps):
    """根据系统生成安装说明"""
    print("\n" + "="*60)
    print("安装建议:")
    print("="*60)

    if system == "Darwin":  # macOS
        print("\n【macOS安装步骤】")
        print("\n1. 安装PostgreSQL:")
        print("   brew install postgresql@15")
        print("   brew services start postgresql@15")
        print("   createdb mcp_monitor")

        if missing_deps:
            print("\n2. 安装Python依赖:")
            print("   pip install -r requirements.txt")
            print("\n   如果Faiss安装失败，尝试:")
            print("   pip install faiss-cpu>=1.8.0")
            print("   或使用conda:")
            print("   conda install -c pytorch faiss-cpu")

    elif system == "Windows":
        print("\n【Windows安装步骤】")
        print("\n1. 安装PostgreSQL:")
        print("   从 https://www.postgresql.org/download/windows/ 下载安装")
        print("   使用pgAdmin创建数据库 'mcp_monitor'")

        if missing_deps:
            print("\n2. 安装Python依赖:")
            print("   pip install -r requirements.txt")
            print("\n   注意: 可能需要安装 Visual C++ Build Tools")

    elif system == "Linux":
        print("\n【Linux安装步骤】")
        print("\n1. 安装PostgreSQL (Ubuntu/Debian):")
        print("   sudo apt update")
        print("   sudo apt install postgresql postgresql-contrib python3-dev")
        print("   sudo systemctl start postgresql")
        print("   sudo -u postgres createdb mcp_monitor")

        if missing_deps:
            print("\n2. 安装Python依赖:")
            print("   pip install -r requirements.txt")

    print("\n3. 初始化数据库:")
    print("   python scripts/init_database.py")

    print("\n4. 启动服务:")
    print("   python main.py")

    print("\n详细文档请查看: INSTALL.md")


def main():
    """主函数"""
    print("="*60)
    print("MCP Monitor - 环境检查")
    print("="*60)

    # 检查Python版本
    if not check_python_version():
        print("\n请升级Python到3.9或更高版本")
        sys.exit(1)

    # 检测平台
    system, machine = check_platform()

    # 检查目录
    check_directories()

    # 检查配置文件
    config_exists = check_config_file()

    # 检查PostgreSQL
    pg_installed = check_postgresql()

    # 检查依赖
    missing_deps = check_dependencies()

    # 生成安装建议
    if missing_deps or not pg_installed or not config_exists:
        get_installation_instructions(system, missing_deps)
    else:
        print("\n" + "="*60)
        print("✓ 环境检查通过！")
        print("="*60)
        print("\n可以运行以下命令启动服务:")
        print("  python scripts/init_database.py  # 首次运行时初始化数据库")
        print("  python main.py                   # 启动服务")
        print("\n访问 http://localhost:8000/docs 查看API文档")

    return 0


if __name__ == "__main__":
    sys.exit(main())
