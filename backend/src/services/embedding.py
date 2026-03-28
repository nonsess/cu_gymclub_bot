import numpy as np
from transformers import AutoTokenizer
from optimum.onnxruntime import ORTModelForFeatureExtraction

from src.core.logger import get_service_logger

class EmbeddingService:
    def __init__(self):
        self.logger = get_service_logger()

        model_id = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
        cache_dir = '/app/model_cache'

        self.logger.info("Initializing Optimum embedding service", extra={"model": model_id})
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_id, cache_dir=cache_dir)
            self.model = ORTModelForFeatureExtraction.from_pretrained(
                model_id,
                export=True, 
                provider="CPUExecutionProvider",
                cache_dir=cache_dir
            )
            self.logger.debug("Optimum model loaded successfully")
        except Exception as e:
            self.logger.error("Failed to load Optimum model", exc_info=True)
            raise
    
    def _mean_pooling(self, last_hidden_state, attention_mask):
        mask = np.expand_dims(attention_mask, axis=-1).astype(float)
        sum_embeddings = np.sum(last_hidden_state * mask, axis=1)
        sum_mask = np.clip(mask.sum(axis=1), a_min=1e-9, a_max=None)
        return sum_embeddings / sum_mask
        
    async def generate_embedding(self, text: str) -> list[float]:
        clean_text = " ".join(text.split())
        
        inputs = self.tokenizer(
            clean_text, 
            return_tensors="np", 
            padding=True, 
            truncation=True, 
            max_length=256
        )
        
        outputs = self.model(**inputs)
        
        embeddings = self._mean_pooling(outputs.last_hidden_state, inputs['attention_mask'])
        
        norm = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / norm
        
        return embeddings[0].tolist()

embedding_service = EmbeddingService()