import torch
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import List, Tuple, Dict
from app.core.config import get_settings

settings = get_settings()


class CodeBERTService:
    def __init__(self):
        self.model_name = settings.CODEBERT_MODEL
        self.similarity_threshold = settings.SIMILARITY_THRESHOLD
        self.tokenizer = None
        self.model = None
        self._initialized = False
    
    def initialize(self):
        """
        Initialize CodeBERT model and tokenizer
        """
        if not self._initialized:
            print(f"Loading CodeBERT model: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name)
            self.model.eval()
            self._initialized = True
            print("CodeBERT model loaded successfully")
    
    def get_code_embedding(self, code: str) -> np.ndarray:
        """
        Generate embedding for code snippet using CodeBERT
        """
        if not self._initialized:
            self.initialize()
        
        # Tokenize code
        inputs = self.tokenizer(
            code,
            return_tensors="pt",
            max_length=512,
            truncation=True,
            padding=True
        )
        
        # Get embeddings
        with torch.no_grad():
            outputs = self.model(**inputs)
            # Use CLS token embedding
            embedding = outputs.last_hidden_state[:, 0, :].numpy()
        
        return embedding[0]
    
    def calculate_similarity(self, code1: str, code2: str) -> float:
        """
        Calculate similarity between two code snippets
        """
        embedding1 = self.get_code_embedding(code1)
        embedding2 = self.get_code_embedding(code2)
        
        # Reshape for cosine_similarity
        embedding1 = embedding1.reshape(1, -1)
        embedding2 = embedding2.reshape(1, -1)
        
        similarity = cosine_similarity(embedding1, embedding2)[0][0]
        return float(similarity)
    
    def detect_plagiarism(self, submissions: List[Dict[str, str]]) -> List[Dict]:
        """
        Detect potential plagiarism among multiple submissions
        
        Args:
            submissions: List of dicts with 'id' and 'code' keys
        
        Returns:
            List of plagiarism detections with similarity scores
        """
        if not self._initialized:
            self.initialize()
        
        detections = []
        n = len(submissions)
        
        # Compare each pair of submissions
        for i in range(n):
            for j in range(i + 1, n):
                similarity = self.calculate_similarity(
                    submissions[i]['code'],
                    submissions[j]['code']
                )
                
                if similarity >= self.similarity_threshold:
                    detections.append({
                        'submission_id_1': submissions[i]['id'],
                        'submission_id_2': submissions[j]['id'],
                        'semantic_similarity': round(similarity * 100, 2),
                        'status': 'suspicious' if similarity > 0.95 else 'review_needed'
                    })
        
        return detections
    
    def calculate_structural_similarity(self, code1: str, code2: str) -> float:
        """
        Calculate structural similarity (simple token-based approach)
        This complements semantic similarity
        """
        # Tokenize both codes
        tokens1 = set(code1.split())
        tokens2 = set(code2.split())
        
        # Jaccard similarity
        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def analyze_code_quality(self, code: str) -> Dict[str, any]:
        """
        Analyze code quality metrics using embeddings
        """
        if not self._initialized:
            self.initialize()
        
        embedding = self.get_code_embedding(code)
        
        # Basic metrics (can be extended)
        code_length = len(code)
        num_lines = len(code.split('\n'))
        avg_line_length = code_length / num_lines if num_lines > 0 else 0
        
        return {
            'embedding_norm': float(np.linalg.norm(embedding)),
            'code_length': code_length,
            'num_lines': num_lines,
            'avg_line_length': round(avg_line_length, 2)
        }
    
    def batch_get_embeddings(self, codes: List[str]) -> np.ndarray:
        """
        Get embeddings for multiple code snippets efficiently
        """
        if not self._initialized:
            self.initialize()
        
        embeddings = []
        for code in codes:
            embedding = self.get_code_embedding(code)
            embeddings.append(embedding)
        
        return np.array(embeddings)


# Singleton instance
codebert_service = CodeBERTService()
