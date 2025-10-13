"""
数据库初始化脚本
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import DatabaseManager
from utils.config_loader import load_config
from loguru import logger


async def init_database():
    """初始化数据库"""
    try:
        # 加载配置
        config = load_config()

        # 初始化数据库管理器
        db_manager = DatabaseManager(config)

        # 创建表
        logger.info("Creating database tables...")
        await db_manager.init()

        logger.info("Database initialized successfully!")

        # 关闭连接
        await db_manager.close()

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(init_database())
