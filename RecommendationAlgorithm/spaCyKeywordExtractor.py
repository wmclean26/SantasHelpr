import spacy

# Load pre-trained model
nlp = spacy.load('en_core_web_sm')

# Process user query
text = "I need to find a gift for my 10 year old niece under 15 dollars"
doc = nlp(text)

# Extract named entities
for ent in doc.ents:
    print(f"{ent.text}: {ent.label_}")
    # Output: "10": CARDINAL, "15 dollars": MONEY
