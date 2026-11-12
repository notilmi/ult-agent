from typing import Any

def extract_text_content(content: Any) -> str:
    """
    Extracts a clean, plain text string from message content.
    Seamlessly handles both simple string content and list-of-dict content blocks
    (e.g., [{'type': 'text', 'text': '...', 'extras': ...}]) returned by Gemini/LangChain.
    """
    if isinstance(content, str):
        return content.strip()
    elif isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                parts.append(str(item["text"]))
            elif hasattr(item, "text"):
                parts.append(str(item.text))
        return "".join(parts).strip()
    return str(content).strip()
