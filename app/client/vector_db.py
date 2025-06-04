from qdrant_client import QdrantClient
from typing import List, Any, Dict, Optional
from qdrant_client import models
from qdrant_client.http.models import (
    ScoredPoint
)
from qdrant_client.conversions.common_types import (
    UpdateResult,
)


class QdrantDBClient:
    """
    Singleton class for managing interactions with a Qdrant vector database.
    """
    _instance = None

    def __new__(cls,
                **_kwargs: Any):
        """
        Ensures only one instance of QdrantDatabaseClientServer is created (Singleton pattern).
        """
        if cls._instance is None:
            cls._instance = super(QdrantDBClient, cls).__new__(cls)
        return cls._instance

    def __init__(self,
                 host: str,
                 port: int):
        if not hasattr(self, 'initialized') or not self.initialized:
            try:
                self.client = QdrantClient(url=host,
                                           port=port)
                self.initialized = True
            except Exception as e:
                raise e


    def insert_point(self,
                     collection_name: str,
                     uuid: str,
                     vector: List[float],
                     payload: Dict
                     ) -> UpdateResult:
        result = self.client.upsert(
            collection_name=collection_name,
            points=[models.PointStruct(
                id=str(uuid),
                payload=payload,
                vector=vector)
            ]
        )
        return result


    def query(
            self,
            collection_name: str,
            vector: List[float],
            limit: int,
            query_filter: Optional[models.Filter] = None,

    ) -> List[ScoredPoint]:
        try:
            result = self.client.search(
                collection_name=collection_name,
                query_vector=vector,
                limit=limit,
                query_filter=query_filter
            )
            return result
        except Exception as e:
            raise e

    def create_collection(self,
                          collection_name: str,
                          collection_size: int ) -> None:

        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=collection_size,
                distance=models.Distance.COSINE),
        )
