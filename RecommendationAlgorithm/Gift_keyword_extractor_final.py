"""
Gift Keyword Extractor for Recommendation System
Author: CS Student
Date: November 18, 2025

This module extracts structured information from natural language gift search queries
and formats the data for eBay and Amazon API calls.

Dependencies:
    - spacy (optional, falls back to regex if not available)
    - re (standard library)

Installation:
    pip install spacy
    python -m spacy download en_core_web_sm
"""

import re
from typing import Dict, List, Optional, Any


class GiftKeywordExtractor:
    """
    Extract structured information from gift search queries to populate
    eBay and Amazon API parameters.

    Usage:
        extractor = GiftKeywordExtractor()
        result = extractor.extract("gift for 10 year old niece under $15")

        # Access eBay parameters
        ebay_query = result['ebay_params']['query']
        ebay_max_price = result['ebay_params']['max_price']

        # Access Amazon parameters
        amazon_query = result['amazon_params']['query']
        amazon_sort = result['amazon_params']['sort_by']

        # Access metadata
        age = result['metadata']['age']
        relationship = result['metadata']['relationship']
    """

    def __init__(self):
        """Initialize the extractor with relationship mappings and category keywords."""
        # Try to load spaCy for advanced NLP, but provide fallback
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
            self.use_spacy = True
            print("✓ spaCy loaded successfully")
        except (ImportError, OSError):
            print("⚠ spaCy not available. Using regex-only mode.")
            print("  For better results, install spaCy:")
            print("  pip install spacy && python -m spacy download en_core_web_sm")
            self.use_spacy = False

        # Relationship mappings with gender and generation inference
        self.relationships = {
            'son': {'gender': 'male', 'generation': 'child'},
            'daughter': {'gender': 'female', 'generation': 'child'},
            'niece': {'gender': 'female', 'generation': 'child'},
            'nephew': {'gender': 'male', 'generation': 'child'},
            'brother': {'gender': 'male', 'generation': 'sibling'},
            'sister': {'gender': 'female', 'generation': 'sibling'},
            'mother': {'gender': 'female', 'generation': 'parent'},
            'father': {'gender': 'male', 'generation': 'parent'},
            'mom': {'gender': 'female', 'generation': 'parent'},
            'dad': {'gender': 'male', 'generation': 'parent'},
            'friend': {'gender': 'neutral', 'generation': 'peer'},
            'wife': {'gender': 'female', 'generation': 'spouse'},
            'husband': {'gender': 'male', 'generation': 'spouse'},
            'girlfriend': {'gender': 'female', 'generation': 'partner'},
            'boyfriend': {'gender': 'male', 'generation': 'partner'},
            'cousin': {'gender': 'neutral', 'generation': 'family'},
            'grandma': {'gender': 'female', 'generation': 'grandparent'},
            'grandmother': {'gender': 'female', 'generation': 'grandparent'},
            'grandpa': {'gender': 'male', 'generation': 'grandparent'},
            'grandfather': {'gender': 'male', 'generation': 'grandparent'},
            'uncle': {'gender': 'male', 'generation': 'family'},
            'aunt': {'gender': 'female', 'generation': 'family'},
        }

        # Age group classifications
        self.age_groups = {
            (0, 2): 'baby',
            (3, 5): 'toddler',
            (6, 9): 'young_child',
            (10, 12): 'preteen',
            (13, 17): 'teen',
            (18, 25): 'young_adult',
            (26, 40): 'adult',
            (41, 60): 'middle_age',
            (61, 120): 'senior'
        }

        # Gift category keywords for categorization
        self.category_keywords = {
            'toys': ['toy', 'toys', 'doll', 'action figure', 'lego', 'blocks', 'game', 'puzzle'],
            'electronics': ['phone', 'tablet', 'laptop', 'headphones', 'speaker', 'gadget', 'tech', 'console'],
            'clothing': ['shirt', 'dress', 'shoes', 'jacket', 'pants', 'clothing', 'apparel', 'outfit'],
            'books': ['book', 'novel', 'reading', 'literature', 'magazine'],
            'sports': ['sports', 'athletic', 'fitness', 'outdoor', 'ball', 'bike', 'exercise'],
            'jewelry': ['jewelry', 'necklace', 'bracelet', 'ring', 'watch', 'earrings'],
            'home': ['home', 'decor', 'kitchen', 'furniture', 'appliance'],
            'beauty': ['makeup', 'perfume', 'skincare', 'cosmetics', 'beauty'],
            'art': ['art', 'craft', 'drawing', 'painting', 'creative'],
        }

    def extract(self, query: str) -> Dict[str, Any]:
        """
        Main extraction method that returns structured data for both APIs.

        Args:
            query (str): The natural language gift search query

        Returns:
            Dict containing:
                - ebay_params: Dict with eBay API parameters
                    - query (str): Search keyword
                    - min_price (float/None): Minimum price
                    - max_price (float/None): Maximum price
                    - condition (str/None): Comma-separated conditions
                    - output_file (str): Output filename
                - amazon_params: Dict with Amazon API parameters
                    - query (str): Search keyword
                    - sort_by (str): Sort preference
                    - max_price (float/None): Maximum price
                - metadata: Dict with extracted context
                    - age (int/None): Extracted age
                    - age_group (str/None): Age category
                    - relationship (str/None): Relationship type
                    - relationship_details (dict/None): Gender and generation
                    - budget (dict/None): Budget constraints
                    - categories (list): Identified product categories
                    - extracted_keywords (list): Relevant keywords
                    - original_query (str): Original input
        """
        query_lower = query.lower()

        # Extract all components
        age = self._extract_age(query)
        budget = self._extract_budget(query)
        relationship = self._extract_relationship(query)
        condition_pref = self._extract_condition_preference(query)
        sort_preference = self._infer_sort_preference(query, budget)
        keywords = self._extract_keywords(query)
        categories = self._identify_categories(query)

        # Build optimized search query for APIs
        search_query = self._build_search_query(query, age, relationship, categories, keywords)

        # Construct eBay API parameters
        ebay_params = {
            'query': search_query,
            'min_price': budget.get('min') if budget else None,
            'max_price': budget.get('max') if budget else None,
            'condition': condition_pref,
            'output_file': 'ebay_results.json'
        }

        # Construct Amazon API parameters
        amazon_params = {
            'query': search_query,
            'sort_by': sort_preference,
            'max_price': budget.get('max') if budget else None,
        }

        # Metadata for recommendation logic
        metadata = {
            'age': age,
            'age_group': self._get_age_group(age) if age else None,
            'relationship': relationship,
            'relationship_details': self.relationships.get(relationship) if relationship else None,
            'budget': budget,
            'categories': categories,
            'extracted_keywords': keywords,
            'original_query': query
        }

        return {
            'ebay_params': ebay_params,
            'amazon_params': amazon_params,
            'metadata': metadata
        }

    def _extract_age(self, query: str) -> Optional[int]:
        """
        Extract age from query using multiple regex patterns.

        Patterns matched:
            - "10 year old", "10 years old"
            - "10 yo", "10y.o."
            - "age 10"
        """
        age_patterns = [
            r'(\d{1,2})\s*year\s*old',
            r'(\d{1,2})\s*yo\b',
            r'age\s*(\d{1,2})',
            r'(\d{1,2})\s*years?\s*old',
            r'\b(\d{1,2})\s*y\.?o\.?\b'
        ]

        for pattern in age_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                age = int(match.group(1))
                if 0 <= age <= 120:  # Sanity check
                    return age

        return None

    def _extract_budget(self, query: str) -> Optional[Dict[str, float]]:
        """
        Extract budget constraints (minimum and maximum prices).

        Patterns matched:
            - Maximum: "under $50", "less than $50", "budget of $50", "$50 or less"
            - Minimum: "at least $20", "minimum of $20", "more than $20"
            - Range: "$20-$50", "$20 to $50"
        """
        budget = {}

        # Max budget patterns
        max_patterns = [
            r'under\s*\$?(\d+(?:\.\d{2})?)',
            r'less\s*than\s*\$?(\d+(?:\.\d{2})?)',
            r'budget\s*of\s*\$?(\d+(?:\.\d{2})?)',
            r'\$(\d+(?:\.\d{2})?)\s*(?:or\s*less|max|maximum)',
            r'no\s*more\s*than\s*\$?(\d+(?:\.\d{2})?)',
            r'up\s*to\s*\$?(\d+(?:\.\d{2})?)'
        ]

        for pattern in max_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                budget['max'] = float(match.group(1))
                break

        # Min budget patterns
        min_patterns = [
            r'at\s*least\s*\$?(\d+(?:\.\d{2})?)',
            r'minimum\s*of\s*\$?(\d+(?:\.\d{2})?)',
            r'more\s*than\s*\$?(\d+(?:\.\d{2})?)',
            r'over\s*\$?(\d+(?:\.\d{2})?)'
        ]

        for pattern in min_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                budget['min'] = float(match.group(1))
                break

        # Range pattern: "$20-$50" or "$20 to $50"
        range_pattern = r'\$?(\d+(?:\.\d{2})?)\s*(?:-|to)\s*\$?(\d+(?:\.\d{2})?)'
        range_match = re.search(range_pattern, query, re.IGNORECASE)
        if range_match:
            budget['min'] = float(range_match.group(1))
            budget['max'] = float(range_match.group(2))

        return budget if budget else None

    def _extract_relationship(self, query: str) -> Optional[str]:
        """Extract relationship type (son, daughter, niece, etc.)."""
        for rel in self.relationships.keys():
            if re.search(rf'\b{rel}\b', query, re.IGNORECASE):
                return rel
        return None

    def _extract_condition_preference(self, query: str) -> Optional[str]:
        """
        Determine if user wants new, used, or any condition.
        Returns comma-separated string for eBay API.
        """
        query_lower = query.lower()

        conditions = []
        if re.search(r'\bnew\b', query_lower):
            conditions.append('NEW')
        if re.search(r'\bused\b|\bsecond\s*hand\b|\bpre\s*owned\b', query_lower):
            conditions.append('USED')

        if conditions:
            return ', '.join(conditions)
        return None  # Default: any condition

    def _infer_sort_preference(self, query: str, budget: Optional[Dict]) -> str:
        """
        Infer Amazon sort preference from query context.

        Returns one of:
            - RELEVANCE (default)
            - PRICE_LOW_TO_HIGH
            - PRICE_HIGH_TO_LOW
            - BEST_SELLING
            - NEWEST
            - AVG_CUSTOMER_REVIEW
        """
        query_lower = query.lower()

        # Explicit sort preferences
        if re.search(r'cheap|cheapest|lowest\s*price|budget|affordable', query_lower):
            return 'PRICE_LOW_TO_HIGH'
        if re.search(r'best\s*quality|premium|expensive|high\s*end', query_lower):
            return 'AVG_CUSTOMER_REVIEW'
        if re.search(r'popular|best\s*seller|trending', query_lower):
            return 'BEST_SELLING'
        if re.search(r'new|newest|latest', query_lower):
            return 'NEWEST'

        # Budget-based inference
        if budget and budget.get('max'):
            if budget['max'] < 25:
                return 'PRICE_LOW_TO_HIGH'

        return 'RELEVANCE'  # Default

    def _extract_keywords(self, query: str) -> List[str]:
        """
        Extract meaningful keywords using spaCy if available, otherwise regex.

        Uses:
            - spaCy: Extracts nouns, proper nouns, adjectives, and noun chunks
            - Regex fallback: Simple tokenization with stopword filtering
        """
        keywords = []

        if self.use_spacy:
            doc = self.nlp(query)

            # Extract nouns, proper nouns, and adjectives
            for token in doc:
                if token.pos_ in ['NOUN', 'PROPN', 'ADJ'] and not token.is_stop:
                    keywords.append(token.lemma_.lower())

            # Extract noun chunks (multi-word phrases)
            for chunk in doc.noun_chunks:
                if len(chunk.text.split()) > 1:
                    keywords.append(chunk.text.lower())
        else:
            # Fallback: simple tokenization excluding common words
            stop_words = {'for', 'my', 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on',
                         'at', 'to', 'i', 'need', 'want', 'find', 'looking', 'gift', 'under'}
            words = re.findall(r'\b[a-z]+\b', query.lower())
            keywords = [w for w in words if w not in stop_words and len(w) > 2]

        return list(set(keywords))  # Remove duplicates

    def _identify_categories(self, query: str) -> List[str]:
        """Identify product categories from the query."""
        query_lower = query.lower()
        found_categories = []

        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                if re.search(rf'\b{keyword}\b', query_lower):
                    found_categories.append(category)
                    break

        return found_categories

    def _get_age_group(self, age: int) -> str:
        """Map numeric age to age group category."""
        for (min_age, max_age), group in self.age_groups.items():
            if min_age <= age <= max_age:
                return group
        return 'unknown'

    def _build_search_query(self, original_query: str, age: Optional[int],
                           relationship: Optional[str], categories: List[str],
                           keywords: List[str]) -> str:
        """
        Build an optimized search query for APIs based on extracted information.

        Strategy:
            1. Start with "gift" as base term
            2. Add age-appropriate terms (kids, teen, etc.)
            3. Add gender if determinable from relationship
            4. Add primary category if identified
            5. Add top relevant keywords
            6. Fallback to cleaned original query if insufficient keywords
        """
        query_parts = ['gift']

        # Add age group if available
        if age:
            age_group = self._get_age_group(age)
            if age_group in ['baby', 'toddler', 'young_child']:
                query_parts.append('kids')
            elif age_group == 'teen':
                query_parts.append('teen')

        # Add gender if determinable from relationship
        if relationship and relationship in self.relationships:
            gender = self.relationships[relationship]['gender']
            if gender != 'neutral':
                query_parts.append(gender)

        # Add primary category
        if categories:
            query_parts.append(categories[0])

        # Add specific keywords (limit to most relevant)
        relevant_keywords = [k for k in keywords
                           if k not in ['gift', 'year', 'old', 'dollar', 'dollars']]
        if relevant_keywords:
            query_parts.extend(relevant_keywords[:3])  # Top 3 keywords

        # If no good keywords extracted, use cleaned version of original
        if len(query_parts) == 1:
            # Remove common phrases and numbers
            cleaned = re.sub(r'\b(for|my|under|dollar|year|old)\b', '',
                           original_query, flags=re.IGNORECASE)
            cleaned = re.sub(r'\d+', '', cleaned)  # Remove numbers
            cleaned = ' '.join(cleaned.split())  # Clean whitespace
            if cleaned:
                return cleaned.strip()

        return ' '.join(query_parts)


# Example usage
if __name__ == "__main__":
    print("=== Gift Keyword Extractor Test Suite ===\n")

    # Initialize extractor
    extractor = GiftKeywordExtractor()

    # Test query
    query = "i need a gift for my 21 year old girlfriend under 50 dollars tomorrow"
    print(f"Query: {query}\n")

    result = extractor.extract(query)

    print("eBay API Parameters:")
    for key, value in result['ebay_params'].items():
        print(f"  {key}: {value}")

    print("\nAmazon API Parameters:")
    for key, value in result['amazon_params'].items():
        print(f"  {key}: {value}")

    print("\nExtracted Metadata:")
    for key, value in result['metadata'].items():
        if value:
            print(f"  {key}: {value}")
