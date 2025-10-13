"""
MCP Monitor - 主入口文件
"""
import asyncio
import yaml
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from database import DatabaseManager
from models import OpenAIAdapter
from core.orchestrator import MCPOrchestrator
from api.routes import router


# 全局变量
db_manager = None
orchestrator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global db_manager, orchestrator

    logger.info("Starting MCP Monitor...")

    try:
        # 1. 加载配置
        with open("config/config.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # 2. 初始化数据库
        logger.info("Initializing database...")
        db_manager = DatabaseManager(config)
        await db_manager.init()

        # 3. 初始化模型
        logger.info("Initializing model...")
        model = OpenAIAdapter(config.get("model", {}))

        # 验证模型配置
        if not model.validate_config():
            raise ValueError("Invalid model configuration")

        # 4. 初始化编排器
        logger.info("Initializing orchestrator...")
        orchestrator = MCPOrchestrator(db_manager, model, config)
        await orchestrator.start()

        logger.info("MCP Monitor started successfully!")

        yield

    except Exception as e:
        logger.error(f"Failed to start MCP Monitor: {e}")
        raise
    finally:
        # 清理
        logger.info("Shutting down MCP Monitor...")

        if orchestrator:
            await orchestrator.stop()

        if db_manager:
            await db_manager.close()

        logger.info("MCP Monitor stopped")


# 创建FastAPI应用
app = FastAPI(
    title="MCP Monitor",
    description="智能MCP工具调用监控和管理系统",
    version="1.0.0",
    lifespan=lifespan
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(router)


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "MCP Monitor",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn

    # 配置日志
    logger.add(
        "logs/mcp_monitor.log",
        rotation="10 MB",
        retention="7 days",
        level="INFO"
    )

    # 启动服务
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
