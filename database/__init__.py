"""
数据库管理器统一接口
"""
from typing import Dict, Any
from database.postgresql import PostgreSQLManager
from database.faiss_db import FaissManager
from loguru import logger


class DatabaseManager:
    """统一的数据库管理器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化数据库管理器

        Args:
            config: 配置字典
        """
        self.config = config

        # 初始化PostgreSQL
        self.pg = PostgreSQLManager(config.get("database", {}))

        # 初始化Faiss
        self.faiss = FaissManager(config.get("database", {}))

        logger.info("Database manager initialized")

    async def init(self):
        """初始化数据库"""
        await self.pg.init_database()

    async def close(self):
        """关闭所有数据库连接"""
        await self.pg.close()
        self.faiss.save()
        logger.info("All database connections closed")

    def __getattr__(self, name):
        """代理访问PostgreSQL方法"""
        if hasattr(self.pg, name):
            return getattr(self.pg, name)
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
