"""
使用示例
"""
import asyncio
import httpx
from loguru import logger


API_BASE = "http://localhost:8000/api/v1"


async def example_workflow():
    """完整的工作流示例"""

    async with httpx.AsyncClient(timeout=30.0) as client:

        # 1. 健康检查
        logger.info("1. Health check...")
        response = await client.get(f"{API_BASE}/health")
        logger.info(f"Health: {response.json()}")

        # 2. 注册MCP服务
        logger.info("\n2. Registering MCP service...")
        service_data = {
            "service_name": "file_operations",
            "service_url": "http://localhost:9000",
            "description": "文件操作服务",
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "delete_file",
                        "description": "删除指定的文件",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "path": {
                                    "type": "string",
                                    "description": "文件路径"
                                }
                            },
                            "required": ["path"]
                        }
                    }
                }
            ],
            "layer": "L2",
            "domain": "file"
        }

        response = await client.post(
            f"{API_BASE}/services/register",
            json=service_data
        )
        logger.info(f"Register result: {response.json()}")

        # 3. 列出所有服务
        logger.info("\n3. Listing all services...")
        response = await client.get(f"{API_BASE}/services/list")
        logger.info(f"Services: {response.json()}")

        # 4. 发送查询（高风险操作）
        logger.info("\n4. Sending query (high-risk operation)...")
        query_data = {
            "user_id": "user123",
            "question": "帮我删除/tmp目录下的所有文件"
        }

        response = await client.post(
            f"{API_BASE}/query",
            json=query_data
        )
        query_result = response.json()
        logger.info(f"Query result: {query_result}")

        # 检查是否需要确认
        if query_result.get("requires_confirmation"):
            request_id = query_result["request_id"]
            logger.info(f"\n5. Tool call requires confirmation!")

            # 显示确认信息
            for tool_call in query_result.get("tool_calls", []):
                logger.info(f"\nConfirmation message:\n{tool_call.get('confirmation_message')}")

            # 模拟用户确认
            logger.info("\n6. User confirming...")
            confirm_data = {
                "request_id": request_id,
                "user_id": "user123",
                "confirmed": True,
                "feedback": "我确认这个操作是安全的"
            }

            response = await client.post(
                f"{API_BASE}/confirm",
                json=confirm_data
            )
            confirm_result = response.json()
            logger.info(f"Confirm result: {confirm_result}")

            # 模拟执行并记录结果
            logger.info("\n7. Recording execution result...")
            execution_data = {
                "request_id": request_id,
                "execution_success": True,
                "execution_result": {
                    "deleted_files": 5,
                    "message": "Files deleted successfully"
                }
            }

            response = await client.post(
                f"{API_BASE}/execution",
                json=execution_data
            )
            logger.info(f"Execution recorded: {response.json()}")

        # 8. 查看用户历史
        logger.info("\n8. Getting user history...")
        response = await client.get(f"{API_BASE}/history/user123?limit=10")
        history = response.json()
        logger.info(f"User history: {history}")


async def example_low_risk_query():
    """低风险查询示例（无需确认）"""

    async with httpx.AsyncClient(timeout=30.0) as client:

        logger.info("Sending low-risk query...")
        query_data = {
            "user_id": "user456",
            "question": "查询今天的天气"
        }

        response = await client.post(
            f"{API_BASE}/query",
            json=query_data
        )
        query_result = response.json()

        logger.info(f"Query result: {query_result}")

        if not query_result.get("requires_confirmation"):
            logger.info("Low risk operation - no confirmation required!")


if __name__ == "__main__":
    # 运行完整工作流示例
    logger.info("=== Running complete workflow example ===")
    asyncio.run(example_workflow())

    logger.info("\n\n=== Running low-risk query example ===")
    asyncio.run(example_low_risk_query())
