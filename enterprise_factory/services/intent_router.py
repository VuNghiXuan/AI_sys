# File: enterprise_factory/services/intent_router.py

def classify_user_intent(directive_text):
    text_lower = directive_text.lower()
    
    # 1. Nhóm SMALL_TALK: Chào hỏi, giao tiếp thông thường
    greeting_keywords = ['chào', 'hi', 'hello', 'hallo', 'buổi sáng', 'buổi chiều', 'cảm ơn', 'thanks']
    if any(kw in text_lower for kw in greeting_keywords) and len(text_lower.split()) <= 4:
        return {
            'intent': 'SMALL_TALK',
            'assigned_agent': 'BOD_CEO_01'
        }

    # 2. Nhóm CODE_DEV: Yêu cầu viết code, lập trình, tạo file, sửa code, hàm xử lý
    code_keywords = ['viết code', 'lập trình', 'tạo hàm', 'tạo file', 'sửa code', 'code cho', 'python', 'django', 'script']
    if any(kw in text_lower for kw in code_keywords):
        return {
            'intent': 'CODE_DEV',
            'assigned_agent': 'DEV_BE_01'
        }

    # 3. Mặc định: GENERAL_DEBATE (Tranh luận, hỏi đáp kiến thức, nghiệp vụ tổng hợp)
    return {
        'intent': 'GENERAL_DEBATE',
        'assigned_agent': 'BOD_CEO_01'
    }