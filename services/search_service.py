# services/search_service.py
import logging
from typing import Dict, Any, Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from services.base_services import SearchService

class GoogleSearchService(SearchService):
    """使用 Google Custom Search API 的搜尋服務"""

    def __init__(self, api_key: Optional[str], cx_id: Optional[str]):
        self.api_key = api_key
        self.cx_id = cx_id
        self._service = None

        if self.is_enabled:
            try:
                self._service = build("customsearch", "v1", developerKey=self.api_key, static_discovery=False)
                logging.info("GoogleSearchService initialized successfully.")
            except Exception as e:
                logging.error(f"Failed to build Google Search service: {e}", exc_info=True)
                self._service = None

    @property
    def is_enabled(self) -> bool:
        """檢查服務是否已啟用 (金鑰和ID都存在)"""
        return bool(self.api_key and self.cx_id)

    def search(self, query: str, num_results: int = 3) -> Dict[str, Any]:
        """執行網路搜尋"""
        if not self._service:
            logging.warning("Search skipped: GoogleSearchService is not enabled or failed to initialize.")
            return {"error": "Service not configured. Check API key and CX ID."}

        try:
            logging.info(f"Performing Google search for: '{query}'")
            response = self._service.cse().list(
                q=query,
                cx=self.cx_id,
                num=num_results,
                lr='lang_zh-TW' # 優先顯示繁體中文結果
            ).execute()

            results_list: list[str] = []
            if 'items' in response:
                for item in response['items']:
                    title = item.get('title', 'N/A')
                    snippet = item.get('snippet', 'No snippet available.').replace("\n", " ").strip()
                    link = item.get('link', '#')
                    results_list.append(f"標題: {title}\n摘要: {snippet}\n連結: {link}")
                logging.info(f"Search successful for '{query}', found {len(results_list)} results.")
                return {"results": results_list}
            else:
                logging.info(f"No search results found for '{query}'.")
                return {"results": []}

        except HttpError as e:
            error_content = str(e.content)
            if e.resp.status in [403, 429]:
                logging.error(f"Search API Quota Exceeded or Key/CX ID issue: {e.resp.status} - {error_content}")
                return {"error": f"API 配額已滿或金鑰錯誤: {e.resp.reason}"}
            else:
                logging.error(f"Search API HttpError: {e.resp.status} - {error_content}")
                return {"error": f"API HTTP 錯誤: {e.resp.reason}"}
        except Exception as e:
            logging.error(f"An unexpected error occurred during search for '{query}': {e}", exc_info=True)
            return {"error": f"未知的搜尋錯誤: {e}"}