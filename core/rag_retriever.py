"""
RAG检索引擎 - 基于历史数据检索相似案例
"""
from typing import List, Dict, Any, Optional, Tuple
from loguru import logger

from database import DatabaseManager
from models.base_model import BaseModel


class RAGRetriever:
    """RAG检索器"""

    def __init__(
        self,
        db_manager: DatabaseManager,
        model: BaseModel,
        config: Dict[str, Any]
    ):
        """
        初始化RAG检索器

        Args:
            db_manager: 数据库管理器
            model: 模型实例（用于生成embedding）
            config: RAG配置
        """
        self.db = db_manager
        self.model = model
        self.config = config.get("rag", {})

        self.top_k = self.config.get("top_k", 5)
        self.similarity_threshold = self.config.get("similarity_threshold", 0.75)

        logger.info(f"RAG retriever initialized: top_k={self.top_k}, threshold={self.similarity_threshold}")

    async def retrieve_similar_cases(
        self,
        user_question: str,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        检索相似的历史案例

        Args:
            user_question: 用户问题
            user_id: 用户ID（可选，用于过滤该用户的历史）

        Returns:
            相似案例列表，每个案例包含历史记录和相似度分数
        """
        try:
            # 1. 生成问题的embedding
            logger.debug(f"Generating embedding for question: {user_question[:50]}...")
            embedding = await self.model.get_embedding(user_question)

            # 2. 在Faiss中搜索相似向量
            logger.debug(f"Searching similar vectors in Faiss...")
            similar_vectors = self.db.faiss.search(embedding, self.top_k * 2)  # 多检索一些，后续过滤

            if not similar_vectors:
                logger.info("No similar cases found in Faiss")
                return []

            # 3. 从PostgreSQL获取完整记录
            database_ids = [db_id for db_id, _ in similar_vectors]
            logger.debug(f"Fetching {len(database_ids)} records from PostgreSQL...")
            histories = await self.db.get_history_by_ids(database_ids)

            # 4. 构建结果，计算相似度并过滤
            results = []
            for history in histories:
                # 找到对应的距离（L2距离）
                distance = next(
                    (dist for db_id, dist in similar_vectors if db_id == history.id),
                    float('inf')
                )

                # 将L2距离转换为相似度分数 (0-1，越高越相似)
                # 使用公式: similarity = 1 / (1 + distance)
                similarity_score = 1.0 / (1.0 + distance)

                # 应用相似度阈值
                if similarity_score < self.similarity_threshold:
                    continue

                # 可选：只返回该用户的历史
                if user_id and history.user_id != user_id:
                    continue

                results.append({
                    "history": history,
                    "similarity_score": similarity_score,
                    "distance": distance
                })

            # 5. 按相似度排序并限制数量
            results.sort(key=lambda x: x["similarity_score"], reverse=True)
            results = results[:self.top_k]

            logger.info(f"Retrieved {len(results)} similar cases (threshold={self.similarity_threshold})")

            return results

        except Exception as e:
            logger.error(f"Error retrieving similar cases: {e}")
            return []

    async def store_question_embedding(
        self,
        user_question: str,
        database_id: int
    ) -> int:
        """
        存储问题的embedding到Faiss

        Args:
            user_question: 用户问题
            database_id: 对应的数据库记录ID

        Returns:
            vector_id: Faiss中的向量ID
        """
        try:
            # 生成embedding
            embedding = await self.model.get_embedding(user_question)

            # 存入Faiss
            vector_id = self.db.faiss.add_vector(embedding, database_id)

            logger.debug(f"Stored embedding: vector_id={vector_id}, db_id={database_id}")

            return vector_id

        except Exception as e:
            logger.error(f"Error storing embedding: {e}")
            return -1

    def analyze_historical_feedback(
        self,
        similar_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        分析历史反馈，提取关键信息

        Args:
            similar_cases: 相似案例列表

        Returns:
            分析结果字典
        """
        if not similar_cases:
            return {
                "has_history": False,
                "risk_indication": "unknown",
                "common_patterns": [],
                "user_preferences": []
            }

        analysis = {
            "has_history": True,
            "total_cases": len(similar_cases),
            "risk_indication": "low",
            "common_patterns": [],
            "user_preferences": []
        }

        # 统计高风险案例
        high_risk_count = 0
        confirmed_count = 0
        rejected_count = 0
        failed_count = 0

        for case in similar_cases:
            history = case["history"]

            # 风险统计
            if history.risk_score and history.risk_score > 0.7:
                high_risk_count += 1

            # 用户反馈统计
            if history.user_confirmed is not None:
                if history.user_confirmed:
                    confirmed_count += 1
                else:
                    rejected_count += 1

            # 执行结果统计
            if history.execution_success is False:
                failed_count += 1

        # 判断风险指示
        if high_risk_count > len(similar_cases) / 2:
            analysis["risk_indication"] = "high"
        elif rejected_count > confirmed_count:
            analysis["risk_indication"] = "medium"
        elif failed_count > 0:
            analysis["risk_indication"] = "medium"

        # 提取常见模式
        if high_risk_count > 0:
            analysis["common_patterns"].append(
                f"历史中有 {high_risk_count}/{len(similar_cases)} 个类似操作被标记为高风险"
            )

        if rejected_count > 0:
            analysis["common_patterns"].append(
                f"历史中有 {rejected_count} 次类似操作被用户拒绝"
            )

        if failed_count > 0:
            analysis["common_patterns"].append(
                f"历史中有 {failed_count} 次类似操作执行失败"
            )

        # 用户偏好
        if confirmed_count > rejected_count:
            analysis["user_preferences"].append("用户通常会确认此类操作")
        elif rejected_count > confirmed_count:
            analysis["user_preferences"].append("用户通常会拒绝此类操作")

        logger.info(
            f"Historical analysis: risk={analysis['risk_indication']}, "
            f"patterns={len(analysis['common_patterns'])}"
        )

        return analysis
