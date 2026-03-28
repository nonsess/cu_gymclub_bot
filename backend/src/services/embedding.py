import numpy as np
from onnxruntime import InferenceSession
from tokenizers import Tokenizer
from pathlib import Path

class EmbeddingService:
    def __init__(self):
        cache_dir = Path('/app/model_cache')
        
        self.tokenizer = Tokenizer.from_file(str(cache_dir / "tokenizer.json"))
        
        self.tokenizer.enable_padding(length=256)
        self.tokenizer.enable_truncation(max_length=256)
        
        self.session = InferenceSession(
            str(cache_dir / "model.onnx"),
            providers=['CPUExecutionProvider']
        )
    
    def _mean_pooling(self, last_hidden_state, attention_mask):
        mask = np.expand_dims(attention_mask, -1).astype(float)
        return np.sum(last_hidden_state * mask, 1) / np.maximum(mask.sum(1), 1e-9)

    async def generate_embedding(self, text: str) -> list[float]:
        encoding = self.tokenizer.encode(text)
        
        inputs = {
            'input_ids': np.array([encoding.ids], dtype=np.int64),
            'attention_mask': np.array([encoding.attention_mask], dtype=np.int64),
            'token_type_ids': np.array([encoding.type_ids], dtype=np.int64)
        }
        
        outputs = self.session.run(['last_hidden_state'], inputs)
        
        embeddings = self._mean_pooling(outputs[0], inputs['attention_mask'])
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        
        return embeddings[0].tolist()

embedding_service = EmbeddingService()
