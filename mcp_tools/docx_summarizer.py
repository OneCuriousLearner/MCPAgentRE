"""
docx_summarizer.py

功能：
- 输入 .docx 文档路径，自动提取正文内容。
- 生成简要摘要（如截取前N段）。
- 作为 MCP 工具注册，便于 AI 自动调用。
- 输出文件默认保存至 docx_sum 文件夹，便于统一管理。

依赖：python-docx
"""
from typing import Optional
from docx import Document
import os
from mcp.server.fastmcp import FastMCP
import json

mcp = FastMCP("docx")

@mcp.tool()
def summarize_docx(docx_path: str, max_paragraphs: int = 5) -> str:
    """
    读取 docx 文档并生成摘要和完整内容的 JSON 数据
    
    参数：
        docx_path (str): .docx 文件路径
        max_paragraphs (int): 摘要最多包含的段落数，默认5
    返回：
        str: JSON 字符串，包含所有段落和摘要
    """
    if not os.path.exists(docx_path):
        return json.dumps({"status": "error", "message": f"文件不存在: {docx_path}"}, ensure_ascii=False)
    try:
        doc = Document(docx_path)
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        para_list = [
            {"index": i+1, "text": text}
            for i, text in enumerate(paragraphs)
        ]
        summary = "\n".join(paragraphs[:max_paragraphs]) if paragraphs else "文档无有效正文内容。"
        result = {
            "status": "success",
            "summary": summary,
            "paragraphs": para_list,
            "total_paragraphs": len(para_list)
        }
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": f"解析文档失败: {str(e)}"}, ensure_ascii=False)

if __name__ == "__main__":
    # 示例用法
    import os
    # 获取项目根目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    test_path = os.path.join(project_root, "docx_sum", "1.docx")
    result_json = summarize_docx(test_path)
    print(result_json)
    # 输出到 docx_sum 文件夹
    output_path = os.path.join(project_root, "docx_sum", "docx_summary.json")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result_json)
    print(f"已将摘要和全部内容输出到 {output_path} 文件。") 