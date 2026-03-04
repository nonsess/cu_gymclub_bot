import asyncio
from typing import List
from sentence_transformers import SentenceTransformer
from src.core.logger import get_service_logger

class EmbeddingService:
    def __init__(self):
        self.logger = get_service_logger()
        self.logger.info(
            "Initializing embedding service",
            extra={
                "operation": "init",
                "model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                "cache_folder": "/app/model_cache"
            }
        )
        
        try:
            self.__model = SentenceTransformer(
                'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
                cache_folder='/app/model_cache'
            )
            self.logger.debug(
                "Model loaded successfully",
                extra={"operation": "init"}
            )
        except Exception as e:
            self.logger.error(
                "Failed to load embedding model",
                extra={
                    "operation": "init",
                    "error_type": type(e).__name__,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
        
    def _clean_description(
        self,
        description: str,
    ) -> str:
        original_length = len(description)
        cleaned = " ".join(description.split())
        cleaned_length = len(cleaned)
        
        if original_length != cleaned_length:
            self.logger.debug(
                "Description cleaned",
                extra={
                    "operation": "_clean_description",
                    "original_length": original_length,
                    "cleaned_length": cleaned_length,
                    "spaces_removed": original_length - cleaned_length
                }
            )
        
        return cleaned

    def _generate_sync(
        self,
        description: str,
    ) -> List[float]:
        try:
            text = self._clean_description(description)
            
            self.logger.debug(
                "Generating embedding",
                extra={
                    "operation": "_generate_sync",
                    "text_length": len(text),
                    "text_preview": text[:100] + "..." if len(text) > 100 else text
                }
            )
            
            embedding = self.__model.encode(
                text,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            
            embedding_list = embedding.tolist()
            
            self.logger.debug(
                "Embedding generated",
                extra={
                    "operation": "_generate_sync",
                    "embedding_length": len(embedding_list),
                    "embedding_preview": embedding_list[:5] if embedding_list else []
                }
            )
            
            return embedding_list
            
        except Exception as e:
            self.logger.error(
                "Failed to generate embedding synchronously",
                extra={
                    "operation": "_generate_sync",
                    "description_length": len(description) if description else 0,
                    "error_type": type(e).__name__,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    async def generate_embedding(
        self,
        description: str,
    ) -> List[float]:
        self.logger.debug(
            "Generating embedding asynchronously",
            extra={
                "operation": "generate_embedding",
                "description_length": len(description) if description else 0,
                "description_preview": description[:100] + "..." if description and len(description) > 100 else description
            }
        )
        
        try:
            embedding = await asyncio.to_thread(
                self._generate_sync,
                description
            )
            
            self.logger.debug(
                "Embedding generated successfully",
                extra={
                    "operation": "generate_embedding",
                    "embedding_length": len(embedding),
                    "description_length": len(description) if description else 0
                }
            )
            
            return embedding
            
        except Exception as e:
            self.logger.error(
                "Failed to generate embedding",
                extra={
                    "operation": "generate_embedding",
                    "description_length": len(description) if description else 0,
                    "error_type": type(e).__name__,
                    "error": str(e)
                },
                exc_info=True
            )
            raise

embedding_service = EmbeddingService()