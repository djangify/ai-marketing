# utils/token_helper.py
def getPromptTokenCount(prompt_text: str) -> int:
    """
    Simple function to estimate the number of tokens in a prompt.
    A more accurate implementation would use tiktoken or a similar library.
    """
    if not prompt_text:
        return 0
    
    # Simple estimation: approximately 4 characters per token
    return max(1, len(prompt_text) // 4)

def formatTokens(tokenCount: int) -> str:
    """Format token count for display."""
    if tokenCount < 1000:
        return str(tokenCount)
    else:
        kCount = tokenCount / 1000
        roundedKCount = round(kCount * 10) / 10
        return f"{roundedKCount}k"
    