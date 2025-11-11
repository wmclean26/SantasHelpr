import re


def extract_basic_info(query):
    info = {}

    # Age extraction
    age_patterns = [
        r'(\d{1,2})\s*year\s*old',
        r'(\d{1,2})\s*yo',
        r'age\s*(\d{1,2})'
    ]
    for pattern in age_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            info['age'] = int(match.group(1))
            break

    # Budget extraction
    budget_patterns = [
        r'under\s*\$?(\d+(?:\.\d{2})?)',
        r'less\s*than\s*\$?(\d+(?:\.\d{2})?)',
        r'budget\s*of\s*\$?(\d+(?:\.\d{2})?)',
        r'\$(\d+(?:\.\d{2})?)\s*(?:or\s*less|max|maximum)'
    ]
    for pattern in budget_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            info['max_budget'] = float(match.group(1))
            break

    # Relationship extraction
    relationships = ['son', 'daughter', 'niece', 'nephew', 'brother', 'sister',
                     'mother', 'father', 'mom', 'dad', 'friend', 'wife', 'husband',
                     'girlfriend', 'boyfriend', 'cousin', 'grandma', 'grandpa']
    for rel in relationships:
        if re.search(rf'\b{rel}\b', query, re.IGNORECASE):
            info['relationship'] = rel
            break

    return info


# Test
query = "I need to find a gift for my 10 year old niece under 15 dollars"
extracted = extract_basic_info(query)
print(extracted)
# Output: {'age': 10, 'max_budget': 15.0, 'relationship': 'niece'}
