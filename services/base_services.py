# services/base_services.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class LLMService(ABC):
    """
    大型語言模型 (LLM) 服務的抽象基礎類別。
    定義了所有 LLM 服務都必須實現的標準介面。
    """

    @abstractmethod
    def generate_content(self, prompt_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        根據結構化的提示詳情生成內容。
        
        Args:
            prompt_details: 一個包含 'contents', 'generation_config' 等鍵的字典。
        
        Returns:
            一個包含 'internal_thought', 'spoken_response', 'error' 等鍵的標準化字典。
        """
        pass

    @abstractmethod
    def analyze_text_for_emotions(self, text: str) -> Dict[str, float]:
        """
        分析給定文本，返回一個包含情緒及其分數的字典。
        
        Args:
            text: 要分析的文本。
            
        Returns:
            一個情緒字典，例如：{'joy': 0.8, 'sadness': 0.1}。
        """
        pass
        
    @abstractmethod
    def appraise_event(self, event_text: str) -> Dict[str, float]:
        """
        根據評價理論分析事件文本，返回評價維度分數。

        Args:
            event_text: 要評價的事件文本。

        Returns:
            一個包含評價維度的字典，例如：{'pleasantness': 0.7, 'novelty': 0.9}。
        """
        pass


class SearchService(ABC):
    """
    網路搜尋服務的抽象基礎類別。
    定義了所有搜尋服務都必須實現的標準介面。
    """

    @abstractmethod
    def search(self, query: str, num_results: int = 3) -> Dict[str, Any]:
        """
        執行網路搜尋。
        
        Args:
            query: 搜尋的關鍵字。
            num_results: 期望的結果數量。
            
        Returns:
            一個包含 'results' (列表) 或 'error' (字串) 的字典。
        """
        pass

    @property
    @abstractmethod
    def is_enabled(self) -> bool:
        """
        檢查服務是否已啟用 (例如，是否已設定 API 金鑰)。
        """
        pass