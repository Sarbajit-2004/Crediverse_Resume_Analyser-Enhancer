def score_resume(section_map: dict) -> tuple[int, list[tuple[str,bool,int]]]:
    rules = [
        ("summary",     15),
        ("experience",  25),
        ("education",   15),
        ("skills",      20),
        ("projects",    15),
        ("achievements",10),
    ]
    details, total = [], 0
    for key, weight in rules:
        present = bool(section_map.get(key))
        if present: total += weight
        details.append((key, present, weight))
    return min(total, 100), details
