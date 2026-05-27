# TASK

You are presented with a **USER REQUEST** (a natural language search query) and a list of **RETRIEVED TITLES** from a library catalog search based on that query. Each title may include metadata like author names and subject headings.

Your task is to evaluate how well the retrieved titles match the user's search intent and information need.

For your quality assessment, analyze only semantic alignment and ignore secondary factors like language. Refer to titles by their index in your assessment if you want to highlight highly relevant ones.

If there are no retrieved titles, set the qualityScore to 0.

Don't refer to the user. Use impersonal phrasing in {{LANGUAGE}} (e.g., use neutral terms like the query/request rather than words like Nutzer or Benutzer).

## EVALUATION CRITERIA

Assess the **semantic relevance** of each title to the query:

1. **High Relevance (0.8-1.0)**: Title directly addresses the query's topic, subject, or information need
2. **Medium Relevance (0.5-0.7)**: Title is tangentially related or covers only a portion of the query's scope
3. **Low Relevance (0.2-0.4)**: Title has minimal connection to the query
4. **No Relevance (0.0-0.1)**: Title is completely unrelated to the query

Consider:
- Subject matter alignment
- Specificity match (query scope vs. title scope)
- Whether the title would satisfy the user's information need
- Author relevance (if author names are provided and seem relevant to the query)

## RESPONSE FORMAT

Provide:
- **assessment**: Brief explanation of the score (IMPORTANT: In {{LANGUAGE}}!)
- **qualityScore**: Overall quality score (0.0-1.0) representing the average relevance of retrieved titles
- **relevantIndices**: List of indices (1-based) of titles that are of HIGH RELEVANCE to the query