# TASK

Rerank library classification topics by relevance to the search request.

# RELEVANCE RULES

A topic is RELEVANT if it:
- Directly matches the search subject
- Is a broader category encompassing the topic
- Is a narrower concept within the topic
- Is a closely related refining concept

A topic is NOT RELEVANT if it:
- Only shares superficial keywords
- Describes an unrelated field
- Would mislead the search intent

# SELECTION GUIDELINES

- Include topics you are CONFIDENT are relevant
- Select at most 6 topics — more dilutes relevance — choose the most relevant ones
- Include at least 2-3 topics when possible
- When uncertain, prefer INCLUSION over EXCLUSION

# EXAMPLE

USER REQUEST: "Klimawandel Auswirkungen auf Landwirtschaft"
TOPICS:
1. Klimawandel
2. Landwirtschaft
3. Globale Erwärmung
4. Wetterextreme
5. Musikgeschichte
6. CO2-Emissionen
7. Trockenheit
8. Stadtplanung

EXPECTED: {"indicesOfRelevantTopics": [1, 2, 3, 6]}

# OUTPUT

Respond with ONLY valid JSON:
{"indicesOfRelevantTopics": [list of integers, sorted by relevance]}
