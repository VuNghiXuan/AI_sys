"""
scan_project_map.py
Script tự động quét toàn bộ cấu trúc thư mục, tệp tin, Class và Hàm Python trong dự án AI_sys,
sau đó tự động cập nhật vào tệp PROJECT_MAP.md chuẩn cốt lõi vnxBox Enterprise.
"""

import os
import ast
import datetime

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_MAP_FILE = os.path.join(ROOT_DIR, "PROJECT_MAP.md")

EXCLUDE_DIRS = {'env', '.git', '__pycache__', 'staticfiles', 'logs', 'media', 'node_modules'}

def parse_python_file(filepath):
    """Đọc file Python và trích xuất danh sách Class và Function bằng AST."""
    classes = []
    functions = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=filepath)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)
            elif isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                functions.append(node.name)
    except Exception as e:
        pass
    return classes, functions

def scan_codebase():
    """Duyệt toàn bộ thư mục dự án và gom cấu trúc."""
    project_structure = {}
    
    for root, dirs, files in os.walk(ROOT_DIR):
        # Lọc bỏ các thư mục hệ thống / môi trường ảo
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        rel_path = os.path.relpath(root, ROOT_DIR)
        if rel_path == '.':
            current_level = project_structure
        else:
            parts = rel_path.split(os.sep)
            curr = project_structure
            for p in parts:
                curr = curr.setdefault(p, {})
                
        for file in files:
            if file.endswith('.py') or file.endswith('.html') or file.endswith('.js'):
                file_path = os.path.join(root, file)
                classes, funcs = [], []
                if file.endswith('.py'):
                    classes, funcs = parse_python_file(file_path)
                
                current_level[file] = {
                    "type": "file",
                    "classes": classes,
                    "funcs": funcs
                }
    return project_structure

def generate_markdown_map(structure):
    """Chuyển cấu trúc đã quét thành định dạng Markdown chuẩn PROJECT_MAP.md."""
    now_str = datetime.datetime.now().strftime("%H:%M:%S ngày %d/%m/%Y")
    lines = [
        "# PROJECT MAP & CODE KNOWLEDGE GRAPH - VNXBOX ENTERPRISE",
        f"# Tự động quét và cập nhật lần cuối: {now_str}",
        "# Quản lý bởi: Ký ức Sâu Mã nguồn (Code Graph & Incremental Memory)",
        "",
        "## 📁 1. Sơ đồ Cấu trúc Thư mục & Chi tiết Mã nguồn",
        ""
    ]

    def build_tree(d, indent=0):
        for name, data in sorted(d.items()):
            prefix = "  " * indent
            if isinstance(data, dict) and "type" not in data:
                lines.append(f"{prefix}- **`{name}/`**")
                build_tree(data, indent + 1)
            elif isinstance(data, dict) and data.get("type") == "file":
                details = []
                if data["classes"]:
                    details.append(f"Classes: {', '.join(data['classes'])}")
                if data["funcs"]:
                    details.append(f"Funcs: {', '.join(data['funcs'][:5])}{'...' if len(data['funcs'])>5 else ''}")
                
                detail_str = f" *({', '.join(details)})*" if details else ""
                lines.append(f"{prefix}  - `{name}`{detail_str}")

    build_tree(structure)
    
    lines.extend([
        "",
        "## 🧠 2. Các Thành Phần Trọng Tâm Đã Định Hình",
        "- **HybridSemanticRouter** (`enterprise_factory/services/semantic_router.py`): Định tuyến 3 tầng + Cosine Similarity.",
        "- **ChatHandlerConsumer** (`enterprise_factory/consumers/chat_handler.py`): Xử lý WebSocket & Map-Reduce spec dài.",
        "- **LongPromptHandler** (`enterprise_factory/services/long_prompt_handler.py`): Hierarchical Chunker cho đặc tả 10k ký tự.",
        "",
        "## 🔒 3. Trạng thái Môi trường & Phần cứng",
        "- **Model LLM:** `qwen2.5-coder:7b-instruct` (Ollama local, port 11434).",
        "- **Core Pinning:** `OLLAMA_NUM_THREAD=10`, `OLLAMA_KEEP_ALIVE=-1`.",
        "- **Database:** SQLite (`db.sqlite3`)."
    ])
    
    return "\n".join(lines)

if __name__ == "__main__":
    print("[*] Đang quét toàn bộ codebase dự án AI_sys...")
    tree_data = scan_codebase()
    md_content = generate_markdown_map(tree_data)
    with open(OUTPUT_MAP_FILE, 'w', encoding='utf-8') as f:
        f.write(md_content)
    print(f"[+] Thành công! Đã cập nhật bản đồ mới nhất vào: {OUTPUT_MAP_FILE}")