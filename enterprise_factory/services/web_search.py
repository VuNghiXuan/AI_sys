# File: enterprise_factory/services/web_search.py
import logging
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

def search_web(query: str, max_results: int = 3) -> str:
    """
    Thực hiện tìm kiếm thông tin trên Web qua DuckDuckGo hoàn toàn miễn phí.
    Dùng để tra cứu luật pháp, định nghĩa, hoặc tin tức nóng theo yêu cầu của Sếp.
    """
    try:
        print(f"🌐 [WEB SEARCH] Đang tra cứu trên mạng từ khóa: '{query}'...")
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                title = r.get('title', '')
                body = r.get('body', '')
                href = r.get('href', '')
                results.append(f"- **{title}**: {body} (Nguồn: {href})")
        
        if not results:
            return "Không tìm thấy kết quả phù hợp trên web."
        
        return "\n".join(results)
    except Exception as e:
        logger.error(f"[-] [WEB SEARCH ERROR]: {str(e)}")
        return f"Lỗi khi tra cứu web: {str(e)}"