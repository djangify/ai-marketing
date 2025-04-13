# utils/token_helper.py
import tiktoken

def getPromptTokenCount(prompt_text: str) -> int:
    """
    Get an accurate token count using tiktoken.
    """
    if not prompt_text:
        return 0
    
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        tokens = encoding.encode(prompt_text)
        return len(tokens)
    except Exception as e:
        print(f"Error counting tokens: {e}")
        # Fallback to a simple word count estimation if tiktoken fails
        return max(1, len(prompt_text) // 4)

def formatTokens(tokenCount: int) -> str:
    """Format token count for display."""
    if tokenCount < 1000:
        return str(tokenCount)
    else:
        kCount = tokenCount / 1000
        roundedKCount = round(kCount * 10) / 10
        return f"{roundedKCount}k"
    