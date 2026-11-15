import urllib.request
import urllib.parse
import logging
from html.parser import HTMLParser

logger = logging.getLogger(__name__)

class DuckDuckGoHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.results = []
        self.current_snippet = ""
        self.current_url = ""
        self.in_result_snippet = False
        self.in_result_url = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == 'a' and 'result__url' in attrs_dict.get('class', ''):
            self.current_url = attrs_dict.get('href', '')
            self.in_result_url = True
        if tag == 'a' and 'result__snippet' in attrs_dict.get('class', ''):
            self.in_result_snippet = True

    def handle_data(self, data):
        if self.in_result_snippet:
            self.current_snippet += data.strip()
        if self.in_result_url:
            if not self.current_url:
                self.current_url = data.strip()

    def handle_endtag(self, tag):
        if tag == 'a':
            if self.in_result_snippet:
                self.in_result_snippet = False
            if self.in_result_url:
                self.in_result_url = False
                if self.current_snippet:
                    self.results.append({
                        "snippet": self.current_snippet,
                        "url": self.current_url or "https://duckduckgo.com"
                    })
                    self.current_snippet = ""
                    self.current_url = ""

def search_bing_or_web(query: str) -> str:
    """
    Hàm cào dữ liệu thực tế từ DuckDuckGo, tự động ép site nếu Sếp hỏi báo chí cụ thể.
    """
    try:
        # Nếu Sếp nhắc đến báo Tuổi Trẻ, tự động tối ưu query tìm kiếm chính thống
        target_query = query
        if 'tuổi trẻ' in query.lower() or 'tuoi tre' in query.lower():
            target_query = f"site:tuoitre.vn {query.replace('báo tuổi trẻ', '').replace('tuổi trẻ', '')}"

        encoded_query = urllib.parse.quote(target_query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            html_content = response.read().decode('utf-8')
            
        parser = DuckDuckGoHTMLParser()
        parser.feed(html_content)
        
        if parser.results:
            formatted_res = ""
            for idx, item in enumerate(parser.results[:5]):
                target_url = item['url']
                if 'uddg=' in target_url:
                    parsed_qs = urllib.parse.parse_qs(urllib.parse.urlparse(target_url).query)
                    if 'uddg' in parsed_qs:
                        target_url = parsed_qs['uddg'][0]

                formatted_res += f"- [Nguồn {idx+1}]: {item['snippet']}\n  Link tham khảo: {target_url}\n\n"
            return formatted_res
            
        return f"Đã tìm kiếm với từ khóa '{query}' nhưng không trích xuất được kết quả chi tiết."
    except Exception as e:
        logger.error(f"[-] Lỗi trong search_bing_or_web: {e}")
        return f"Không thể kết nối đến công cụ tìm kiếm trực tuyến: {str(e)}"