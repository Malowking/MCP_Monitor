"""
Faiss向量数据库管理
"""
import os
import pickle
from typing import List, Tuple, Optional
import numpy as np
import faiss
from loguru import logger


class FaissManager:
    """Faiss向量数据库管理器"""

    def __init__(self, config: dict):
        """
        初始化Faiss管理器

        Args:
            config: Faiss配置字典
        """
        self.config = config
        faiss_config = config.get("faiss", {})

        self.index_path = faiss_config.get("index_path", "./data/faiss_index")
        self.dimension = faiss_config.get("dimension", 1536)
        self.index_type = faiss_config.get("index_type", "IVFFlat")
        self.nlist = faiss_config.get("nlist", 100)

        # 确保存储目录存在
        os.makedirs(self.index_path, exist_ok=True)

        # 索引文件路径
        self.index_file = os.path.join(self.index_path, "index.faiss")
        self.id_map_file = os.path.join(self.index_path, "id_map.pkl")

        # 初始化索引
        self.index = None
        self.id_map = {}  # vector_id -> database_id 映射
        self.next_vector_id = 0

        self._load_or_create_index()

        logger.info(f"Faiss manager initialized: {self.index_path}, dimension={self.dimension}")

    def _create_index(self) -> faiss.Index:
        """创建Faiss索引"""
        if self.index_type == "Flat":
            # 暴力搜索，精确但慢
            index = faiss.IndexFlatL2(self.dimension)
        elif self.index_type == "IVFFlat":
            # 倒排文件索引，平衡精度和速度
            quantizer = faiss.IndexFlatL2(self.dimension)
            index = faiss.IndexIVFFlat(quantizer, self.dimension, self.nlist)
            # 需要训练
            index.is_trained = False
        elif self.index_type == "HNSW":
            # HNSW图索引，快速但占用内存
            index = faiss.IndexHNSWFlat(self.dimension, 32)
        else:
            logger.warning(f"Unknown index type {self.index_type}, using Flat")
            index = faiss.IndexFlatL2(self.dimension)

        logger.info(f"Created new Faiss index: {self.index_type}")
        return index

    def _load_or_create_index(self):
        """加载或创建索引"""
        if os.path.exists(self.index_file) and os.path.exists(self.id_map_file):
            # 加载现有索引
            try:
                self.index = faiss.read_index(self.index_file)
                with open(self.id_map_file, 'rb') as f:
                    data = pickle.load(f)
                    self.id_map = data['id_map']
                    self.next_vector_id = data['next_vector_id']
                logger.info(f"Loaded existing Faiss index with {self.index.ntotal} vectors")
            except Exception as e:
                logger.error(f"Failed to load index: {e}, creating new one")
                self.index = self._create_index()
        else:
            # 创建新索引
            self.index = self._create_index()

    def _save_index(self):
        """保存索引到磁盘"""
        try:
            faiss.write_index(self.index, self.index_file)
            with open(self.id_map_file, 'wb') as f:
                pickle.dump({
                    'id_map': self.id_map,
                    'next_vector_id': self.next_vector_id
                }, f)
            logger.debug(f"Saved Faiss index with {self.index.ntotal} vectors")
        except Exception as e:
            logger.error(f"Failed to save index: {e}")

    def add_vector(self, embedding: List[float], database_id: int) -> int:
        """
        添加向量到索引

        Args:
            embedding: 向量嵌入
            database_id: 对应的数据库记录ID

        Returns:
            vector_id: Faiss中的向量ID
        """
        # 转换为numpy数组
        vector = np.array([embedding], dtype=np.float32)

        # 如果是IVFFlat且未训练，需要先训练
        if isinstance(self.index, faiss.IndexIVFFlat) and not self.index.is_trained:
            if self.index.ntotal >= self.nlist:
                # 有足够的数据进行训练
                logger.info("Training IVFFlat index...")
                self.index.train(vector)
            else:
                # 数据不够，暂时不训练，等数据足够再说
                pass

        # 添加向量
        if self.index.is_trained or not isinstance(self.index, faiss.IndexIVFFlat):
            self.index.add(vector)

            # 记录映射
            vector_id = self.next_vector_id
            self.id_map[vector_id] = database_id
            self.next_vector_id += 1

            # 定期保存（每10个向量保存一次）
            if self.next_vector_id % 10 == 0:
                self._save_index()

            logger.debug(f"Added vector {vector_id} -> database_id {database_id}")
            return vector_id
        else:
            logger.warning("Index not trained yet, skipping add")
            return -1

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        搜索最相似的向量

        Args:
            query_embedding: 查询向量
            top_k: 返回top k结果

        Returns:
            [(database_id, distance), ...] 列表
        """
        if self.index.ntotal == 0:
            logger.warning("Index is empty")
            return []

        # 转换为numpy数组
        query_vector = np.array([query_embedding], dtype=np.float32)

        # 搜索
        try:
            distances, indices = self.index.search(query_vector, top_k)

            # 转换为数据库ID
            results = []
            for idx, dist in zip(indices[0], distances[0]):
                if idx != -1 and idx in self.id_map:
                    database_id = self.id_map[idx]
                    results.append((database_id, float(dist)))

            logger.debug(f"Found {len(results)} similar vectors")
            return results
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def delete_vector(self, vector_id: int):
        """
        删除向量（注意：Faiss不直接支持删除，这里只从映射中移除）

        Args:
            vector_id: 向量ID
        """
        if vector_id in self.id_map:
            del self.id_map[vector_id]
            self._save_index()
            logger.debug(f"Removed vector {vector_id} from mapping")

    def get_total_vectors(self) -> int:
        """获取索引中的向量总数"""
        return self.index.ntotal

    def save(self):
        """手动保存索引"""
        self._save_index()

    def rebuild_index(self, embeddings: List[Tuple[List[float], int]]):
        """
        重建索引（用于维护）

        Args:
            embeddings: [(embedding, database_id), ...] 列表
        """
        logger.info("Rebuilding Faiss index...")

        # 创建新索引
        self.index = self._create_index()
        self.id_map = {}
        self.next_vector_id = 0

        # 批量添加
        if embeddings:
            vectors = np.array([emb for emb, _ in embeddings], dtype=np.float32)

            # 训练（如果需要）
            if isinstance(self.index, faiss.IndexIVFFlat) and not self.index.is_trained:
                if len(vectors) >= self.nlist:
                    logger.info("Training index...")
                    self.index.train(vectors)

            # 添加向量
            if self.index.is_trained or not isinstance(self.index, faiss.IndexIVFFlat):
                self.index.add(vectors)

                # 重建映射
                for i, (_, db_id) in enumerate(embeddings):
                    self.id_map[i] = db_id
                self.next_vector_id = len(embeddings)

        # 保存
        self._save_index()
        logger.info(f"Index rebuilt with {self.index.ntotal} vectors")
