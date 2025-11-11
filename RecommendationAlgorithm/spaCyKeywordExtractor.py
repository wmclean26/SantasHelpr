import spacy
import re


nlp = spacy.load('en_core_web_sm')


def extract_entities(query):
    doc = nlp(query)
    entities = {}

    for ent in doc.ents:
        if ent.label_ == 'MONEY':
            # Extract numeric value from money entity
            amount = re.search(r'(\d+(?:\.\d{2})?)', ent.text)
            if amount:
                entities['budget'] = float(amount.group(1))
        elif ent.label_ == 'DATE':
            entities['occasion_date'] = ent.text
        elif ent.label_ == 'CARDINAL':
            # Might be age
            entities['age_candidate'] = int(ent.text)

    return entities


query = "I need to find a gift for my 10 year old niece under 15 dollars"
entities = extract_entities(query)
print(entities)
