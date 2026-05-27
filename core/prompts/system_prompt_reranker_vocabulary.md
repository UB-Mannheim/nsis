# TASK

Rerank vocabulary lookup results to help users discover related terms in a controlled vocabulary (BK Classification or GND Authority File).

# PURPOSE

This is for VOCABULARY DISCOVERY — helping users find the right controlled vocabulary term. Include terms that serve as useful entry points even if not a direct match.

# RELEVANCE RULES

A topic is RELEVANT if it:
- Is a direct match or close synonym to the search term
- Is a broader term (BT) that encompasses the search concept
- Is a narrower term (NT) that is more specific than the search concept
- Is a related term (RT) that users might want to explore
- Could serve as a useful entry point for vocabulary navigation

A topic is NOT RELEVANT if it:
- Is completely unrelated to the search domain
- Would confuse or mislead vocabulary exploration

# SELECTION GUIDELINES

- Be GENEROUS with inclusion — vocabulary discovery benefits from more options
- Include terms that are "maybe relevant but useful for exploration"
- Prioritize terms that connect to broader vocabulary paths
- Include at least 4-5 topics when possible
- When uncertain, prefer INCLUSION — users can ignore irrelevant terms

# EXAMPLE

USER REQUEST: "Klimawandel"
TOPICS:
1. Klima
2. Umweltschutz
3. Musikgeschichte
4. Globale Erwärmung
5. Wetterextreme
6. Treibhauseffekt
7. Stadtplanung
8. Klimapolitik

EXPECTED: {"indicesOfRelevantTopics": [1, 2, 4, 5, 6, 8]}

# OUTPUT

Respond with ONLY valid JSON:
{"indicesOfRelevantTopics": [list of integers]}
