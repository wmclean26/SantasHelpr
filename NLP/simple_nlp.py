"""
Enhanced NLP extractor for chat mode - uses spaCy + regex for best extraction
Combines entity recognition, POS tagging, noun chunks, and pattern matching
"""

import re
from typing import Dict, Any, Optional, List

# Try to load spaCy
try:
    import spacy
    try:
        nlp = spacy.load('en_core_web_sm')
        SPACY_AVAILABLE = True
        print("✓ spaCy loaded successfully for enhanced NLP")
    except OSError:
        SPACY_AVAILABLE = False
        print("⚠ spaCy model not found. Run: python -m spacy download en_core_web_sm")
except ImportError:
    SPACY_AVAILABLE = False
    print("⚠ spaCy not installed. Run: pip install spacy")


class SimpleNLPExtractor:
    """
    Enhanced keyword and topic extractor for gift search queries.
    Uses spaCy NLP + regex patterns for comprehensive extraction.
    """

    def __init__(self):
        self.use_spacy = SPACY_AVAILABLE
        
        # Common words to filter out
        self.stop_words = {
            'i', 'me', 'my', 'a', 'an', 'the', 'for', 'to', 'of', 'and', 'or',
            'need', 'want', 'looking', 'find', 'get', 'buy', 'search', 'show',
            'please', 'can', 'you', 'help', 'something', 'anything', 'gift',
            'present', 'idea', 'ideas', 'good', 'best', 'nice', 'cool', 'great',
            'really', 'very', 'some', 'any', 'that', 'this', 'what', 'which',
            'would', 'like', 'think', 'maybe', 'could', 'should', 'be', 'is',
            'are', 'was', 'were', 'been', 'being', 'have', 'has', 'had', 'do',
            'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
            'must', 'shall', 'it', 'its', 'they', 'them', 'their', 'he', 'she',
            'him', 'her', 'his', 'hers', 'who', 'whom', 'whose', 'there', 'here'
        }

        # Relationship to gender/demographic mapping
        self.relationships = {
            'son': {'gender': 'boy', 'demographic': 'kids'},
            'daughter': {'gender': 'girl', 'demographic': 'kids'},
            'niece': {'gender': 'girl', 'demographic': 'kids'},
            'nephew': {'gender': 'boy', 'demographic': 'kids'},
            'brother': {'gender': 'men', 'demographic': 'adult'},
            'sister': {'gender': 'women', 'demographic': 'adult'},
            'mother': {'gender': 'women', 'demographic': 'adult'},
            'father': {'gender': 'men', 'demographic': 'adult'},
            'mom': {'gender': 'women', 'demographic': 'adult'},
            'dad': {'gender': 'men', 'demographic': 'adult'},
            'wife': {'gender': 'women', 'demographic': 'adult'},
            'husband': {'gender': 'men', 'demographic': 'adult'},
            'girlfriend': {'gender': 'women', 'demographic': 'adult'},
            'boyfriend': {'gender': 'men', 'demographic': 'adult'},
            'grandma': {'gender': 'women', 'demographic': 'senior'},
            'grandmother': {'gender': 'women', 'demographic': 'senior'},
            'grandpa': {'gender': 'men', 'demographic': 'senior'},
            'grandfather': {'gender': 'men', 'demographic': 'senior'},
            'aunt': {'gender': 'women', 'demographic': 'adult'},
            'uncle': {'gender': 'men', 'demographic': 'adult'},
            'friend': {'gender': None, 'demographic': 'adult'},
            'cousin': {'gender': None, 'demographic': None},
            'baby': {'gender': None, 'demographic': 'baby'},
            'toddler': {'gender': None, 'demographic': 'toddler'},
            'kid': {'gender': None, 'demographic': 'kids'},
            'child': {'gender': None, 'demographic': 'kids'},
            'teen': {'gender': None, 'demographic': 'teen'},
            'teenager': {'gender': None, 'demographic': 'teen'},
        }
        
        # Category keywords for product classification
        self.category_keywords = {
            'toys': ['toy', 'toys', 'doll', 'action figure', 'lego', 'blocks', 'game', 'puzzle', 'playset'],
            'electronics': ['phone', 'tablet', 'laptop', 'headphones', 'speaker', 'gadget', 'tech', 'console', 'gaming', 'computer', 'earbuds', 'airpods'],
            'clothing': ['shirt', 'dress', 'shoes', 'jacket', 'pants', 'clothing', 'apparel', 'outfit', 'sweater', 'hoodie'],
            'books': ['book', 'novel', 'reading', 'literature', 'magazine', 'kindle'],
            'sports': ['sports', 'athletic', 'fitness', 'outdoor', 'ball', 'bike', 'exercise', 'gym', 'yoga'],
            'jewelry': ['jewelry', 'necklace', 'bracelet', 'ring', 'watch', 'earrings'],
            'home': ['home', 'decor', 'kitchen', 'furniture', 'appliance', 'cookware'],
            'beauty': ['makeup', 'perfume', 'skincare', 'cosmetics', 'beauty', 'fragrance'],
            'art': ['art', 'craft', 'drawing', 'painting', 'creative', 'supplies'],
            'music': ['music', 'guitar', 'piano', 'instrument', 'vinyl', 'record'],
        }

    def extract(self, query: str) -> Dict[str, Any]:
        """
        Extract main topic and filters from a natural language query.
        Uses spaCy for NLP when available, with regex fallback.
        
        Returns:
            Dict with 'query', 'min_price', 'max_price', 'metadata'
        """
        query_lower = query.lower()
        
        # Extract price constraints (regex is reliable for this)
        min_price, max_price = self._extract_price(query_lower)
        
        # Extract age (regex + spaCy entity recognition)
        age = self._extract_age(query, query_lower)
        
        # Extract relationship and infer gender/demographic context
        relationship = self._extract_relationship(query_lower)
        rel_info = self.relationships.get(relationship, {}) if relationship else {}
        gender_context = rel_info.get('gender')
        demographic = rel_info.get('demographic')
        
        # Override demographic based on age if available
        if age:
            demographic = self._get_demographic_from_age(age)
        
        # Extract categories mentioned
        categories = self._identify_categories(query_lower)
        
        # Extract the main topic/product using spaCy or regex
        if self.use_spacy:
            main_topic, keywords = self._extract_main_topic_spacy(query, age, gender_context, demographic, categories)
        else:
            main_topic, keywords = self._extract_main_topic_regex(query_lower, age, gender_context, demographic, categories)
        
        return {
            'query': main_topic,
            'min_price': min_price,
            'max_price': max_price,
            'metadata': {
                'age': age,
                'demographic': demographic,
                'relationship': relationship,
                'gender_context': gender_context,
                'categories': categories,
                'keywords': keywords,
                'original_query': query
            }
        }

    def _extract_price(self, query: str) -> tuple:
        """Extract min and max price from query using regex patterns."""
        min_price = None
        max_price = None
        
        # Max price patterns (order matters - more specific first)
        max_patterns = [
            r'under\s*\$?(\d+(?:\.\d{2})?)',
            r'less\s*than\s*\$?(\d+(?:\.\d{2})?)',
            r'up\s*to\s*\$?(\d+(?:\.\d{2})?)',
            r'no\s*more\s*than\s*\$?(\d+(?:\.\d{2})?)',
            r'max(?:imum)?\s*\$?(\d+(?:\.\d{2})?)',
            r'\$?(\d+(?:\.\d{2})?)\s*(?:or\s*less|max|budget)',
            r'budget\s*(?:of\s*)?\$?(\d+(?:\.\d{2})?)',
            r'around\s*\$?(\d+(?:\.\d{2})?)',
            r'about\s*\$?(\d+(?:\.\d{2})?)',
            r'roughly\s*\$?(\d+(?:\.\d{2})?)',
        ]
        
        for pattern in max_patterns:
            match = re.search(pattern, query)
            if match:
                max_price = int(float(match.group(1)))
                break
        
        # Min price patterns
        min_patterns = [
            r'at\s*least\s*\$?(\d+(?:\.\d{2})?)',
            r'minimum\s*(?:of\s*)?\$?(\d+(?:\.\d{2})?)',
            r'over\s*\$?(\d+(?:\.\d{2})?)',
            r'more\s*than\s*\$?(\d+(?:\.\d{2})?)',
            r'above\s*\$?(\d+(?:\.\d{2})?)',
        ]
        
        for pattern in min_patterns:
            match = re.search(pattern, query)
            if match:
                min_price = int(float(match.group(1)))
                break
        
        # Price range pattern: $20-$50 or $20 to $50
        range_match = re.search(r'\$?(\d+(?:\.\d{2})?)\s*(?:-|to)\s*\$?(\d+(?:\.\d{2})?)', query)
        if range_match:
            min_price = int(float(range_match.group(1)))
            max_price = int(float(range_match.group(2)))
        
        return min_price, max_price

    def _extract_age(self, query: str, query_lower: str) -> Optional[int]:
        """Extract age from query using spaCy entities + regex patterns."""
        age = None
        
        # First try spaCy for entity recognition
        if self.use_spacy:
            doc = nlp(query)
            for ent in doc.ents:
                if ent.label_ == 'CARDINAL':
                    # Check if this cardinal is near "year old" or similar
                    context = query_lower[max(0, ent.start_char-5):min(len(query_lower), ent.end_char+15)]
                    if re.search(r'\d+\s*(?:year|yr|yo)', context):
                        try:
                            age = int(ent.text)
                            if 0 <= age <= 100:
                                return age
                        except ValueError:
                            pass
        
        # Regex fallback/supplement
        patterns = [
            r'(\d{1,2})\s*year\s*old',
            r'(\d{1,2})\s*-?\s*year\s*-?\s*old',
            r'(\d{1,2})\s*yo\b',
            r'(\d{1,2})\s*y\.?o\.?\b',
            r'age\s*(\d{1,2})\b',
            r'(\d{1,2})\s*years?\s*old',
            r'aged?\s*(\d{1,2})\b',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                try:
                    age = int(match.group(1))
                    if 0 <= age <= 100:
                        return age
                except ValueError:
                    pass
        
        return age

    def _extract_relationship(self, query: str) -> Optional[str]:
        """Extract relationship from query."""
        for rel in self.relationships.keys():
            if re.search(rf'\b{rel}\b', query):
                return rel
        return None

    def _get_demographic_from_age(self, age: int) -> str:
        """Map age to demographic category."""
        if age <= 2:
            return 'baby'
        elif age <= 4:
            return 'toddler'
        elif age <= 12:
            return 'kids'
        elif age <= 17:
            return 'teen'
        elif age <= 25:
            return 'young adult'
        elif age <= 60:
            return 'adult'
        else:
            return 'senior'

    def _identify_categories(self, query: str) -> List[str]:
        """Identify product categories from the query."""
        found_categories = []
        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                if re.search(rf'\b{keyword}s?\b', query):
                    if category not in found_categories:
                        found_categories.append(category)
                    break
        return found_categories

    def _extract_main_topic_spacy(self, query: str, age: Optional[int], 
                                   gender_context: Optional[str],
                                   demographic: Optional[str],
                                   categories: List[str]) -> tuple:
        """
        Extract the main topic using spaCy NLP.
        Returns (search_query, keywords_list)
        """
        doc = nlp(query)
        
        # Extract noun chunks (multi-word phrases like "lego star wars")
        noun_chunks = []
        for chunk in doc.noun_chunks:
            chunk_text = chunk.text.lower()
            # Filter out chunks that are just stop words or relationships
            chunk_words = chunk_text.split()
            meaningful_words = [w for w in chunk_words if w not in self.stop_words and w not in self.relationships]
            if meaningful_words:
                noun_chunks.append(' '.join(meaningful_words))
        
        # Extract individual nouns, proper nouns, and adjectives
        keywords = []
        for token in doc:
            if token.pos_ in ['NOUN', 'PROPN'] and not token.is_stop:
                lemma = token.lemma_.lower()
                if lemma not in self.stop_words and lemma not in self.relationships and len(lemma) > 2:
                    keywords.append(lemma)
            elif token.pos_ == 'ADJ' and not token.is_stop:
                # Include descriptive adjectives (colors, materials, etc.)
                lemma = token.lemma_.lower()
                if lemma not in self.stop_words and len(lemma) > 2:
                    keywords.append(lemma)
        
        # Remove duplicates while preserving order
        keywords = list(dict.fromkeys(keywords))
        
        # Filter out price/age/relationship related words
        filter_words = {'dollar', 'dollars', 'year', 'years', 'old', 'age', 'gift', 'present', 'idea'}
        keywords = [k for k in keywords if k not in filter_words]
        noun_chunks = [nc for nc in noun_chunks if not any(fw in nc for fw in filter_words)]
        
        # Build the search query
        search_parts = []
        
        # Prioritize noun chunks (they capture multi-word product names)
        if noun_chunks:
            # Use the longest/most specific noun chunk first
            best_chunk = max(noun_chunks, key=len)
            search_parts.append(best_chunk)
            # Add other unique keywords not in the chunk
            for kw in keywords[:3]:
                if kw not in best_chunk:
                    search_parts.append(kw)
        elif keywords:
            search_parts.extend(keywords[:4])
        
        # Add demographic/gender context if helpful and no specific product found
        if len(search_parts) == 0 or (len(search_parts) == 1 and search_parts[0] in ['stuff', 'thing', 'things']):
            if demographic:
                search_parts.insert(0, demographic)
            if gender_context:
                search_parts.insert(0, gender_context)
            if categories:
                search_parts.append(categories[0])
            if not search_parts:
                search_parts.append('gift')
        
        main_topic = ' '.join(search_parts).strip()
        
        # Clean up
        main_topic = re.sub(r'\s+', ' ', main_topic).strip()
        
        return main_topic, keywords

    def _extract_main_topic_regex(self, query: str, age: Optional[int], 
                                   gender_context: Optional[str],
                                   demographic: Optional[str],
                                   categories: List[str]) -> tuple:
        """
        Fallback: Extract the main topic using regex (when spaCy unavailable).
        Returns (search_query, keywords_list)
        """
        # Remove price mentions
        cleaned = re.sub(r'\$\d+(?:\.\d{2})?', '', query)
        cleaned = re.sub(r'under\s*\d+', '', cleaned)
        cleaned = re.sub(r'less\s*than\s*\d+', '', cleaned)
        cleaned = re.sub(r'up\s*to\s*\d+', '', cleaned)
        cleaned = re.sub(r'budget\s*(?:of\s*)?\d+', '', cleaned)
        cleaned = re.sub(r'around\s*\d+', '', cleaned)
        cleaned = re.sub(r'about\s*\d+', '', cleaned)
        cleaned = re.sub(r'\d+\s*dollars?', '', cleaned)
        
        # Remove age mentions
        cleaned = re.sub(r'\d+\s*-?\s*year\s*-?\s*old', '', cleaned)
        cleaned = re.sub(r'\d+\s*yo\b', '', cleaned)
        cleaned = re.sub(r'age\s*\d+', '', cleaned)
        
        # Remove relationship words
        for rel in self.relationships.keys():
            cleaned = re.sub(rf'\b{rel}\b', '', cleaned)
        
        # Tokenize and filter
        words = re.findall(r'\b[a-z]+\b', cleaned)
        keywords = [w for w in words if w not in self.stop_words and len(w) > 2]
        
        # Build the search query
        search_parts = []
        
        if keywords:
            search_parts.extend(keywords[:4])
        
        # Add context if no good keywords
        if not search_parts:
            if demographic:
                search_parts.append(demographic)
            if gender_context:
                search_parts.append(gender_context)
            if categories:
                search_parts.append(categories[0])
            if not search_parts:
                search_parts.append('gift')
        
        main_topic = ' '.join(search_parts).strip()
        
        return main_topic, keywords


# Quick test
if __name__ == "__main__":
    extractor = SimpleNLPExtractor()
    
    test_queries = [
        "I need a gift for my 10 year old niece under $50",
        "Looking for headphones for my boyfriend around $100",
        "Get me a lego star wars set under 30 dollars",
        "something for my mom, maybe kitchen stuff under $75",
        "toy for 5 year old nephew",
        "gaming keyboard for teen",
        "nice watch for my husband's birthday around $200",
        "art supplies for creative daughter age 8",
    ]
    
    print(f"\nUsing spaCy: {extractor.use_spacy}\n")
    print("=" * 60)
    
    for q in test_queries:
        result = extractor.extract(q)
        print(f"\nQuery: {q}")
        print(f"  → Search: '{result['query']}'")
        print(f"  → Price: ${result['min_price'] or 0} - ${result['max_price'] or 'any'}")
        print(f"  → Keywords: {result['metadata']['keywords']}")
        print(f"  → Categories: {result['metadata']['categories']}")
        if result['metadata']['relationship']:
            print(f"  → Recipient: {result['metadata']['relationship']} ({result['metadata']['demographic']})")

