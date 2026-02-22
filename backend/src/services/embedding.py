import asyncio
from typing import List
from sentence_transformers import SentenceTransformer

class EmbeddingService:
    def __init__(self):
        self.model = SentenceTransformer(
            'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
            cache_folder='/app/model_cache'
        )
        
    def _clean_description(
        self,
        description: str,
    ) -> str:
        return " ".join(description.split())

    def _generate_sync(
        self,
        description: str,
    ) -> List[float]:
        text = self._clean_description(description)
        print(text)
        embedding = self.model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        return embedding.tolist()
    
    async def generate_embedding(
        self,
        description: str,
    ) -> List[float]:
        return await asyncio.to_thread(
            self._generate_sync,
            description
        )

embedding_service = EmbeddingService()