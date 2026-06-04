def looks_like_isin(symbol: str) -> bool:
    upper = symbol.upper().strip()
    return len(upper) == 12 and upper[:2].isalpha() and upper[2:].isalnum()
