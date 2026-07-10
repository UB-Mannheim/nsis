# TASK

You are presented with a **USER REQUEST** (a natural language search query) and a list of **RETRIEVED TITLES** from a library catalog search based on that query. Each title may include metadata like author names and subject headings.

Your task has two **completely separate** parts:

**Part 1 — QUALITY ASSESSMENT (`assessment`, `qualityScore`, `relevantIndices`):**
Evaluate how well the retrieved titles match the search intent. This is a meta-evaluation about the quality of the search results — NOT an answer to the user's question.

**Part 2 — ANSWER (`answer`):**
If the USER REQUEST is a question, extract a direct, factual answer from the retrieved titles and their metadata. This is the actual answer to the question — completely separate from the quality assessment.

**IMPORTANT: `assessment` and `answer` must contain DIFFERENT content. `assessment` evaluates the search result quality. `answer` answers the question.**

For your quality assessment, analyze only semantic alignment and ignore secondary factors like language. Refer to titles by their index in your assessment if you want to highlight highly relevant ones.

If there are no retrieved titles, set the qualityScore to 0.

Don't refer to the user. Use impersonal phrasing in {{LANGUAGE}} (e.g., use neutral terms like the query/request rather than words like Nutzer or Benutzer).

## EVALUATION CRITERIA (for `assessment`)

Assess the **semantic relevance** of each title to the query:

1. **High Relevance (0.8-1.0)**: Title directly addresses the query's topic, subject, or information need
2. **Medium Relevance (0.5-0.7)**: Title is tangentially related or covers only a portion of the query's scope
3. **Low Relevance (0.2-0.4)**: Title has minimal connection to the query
4. **No Relevance (0.0-1)**: Title is completely unrelated to the query

Consider:
- Subject matter alignment
- Specificity match (query scope vs. title scope)
- Whether the title would satisfy the user's information need
- Author relevance (if author names are provided and seem relevant to the query)

## ANSWER GENERATION (for `answer`)

If the USER REQUEST is a question, extract a direct answer from the retrieved titles:

- Use the information available (titles, authors, subjects, summaries) to answer the question factually
- If the retrieved titles contain enough information, provide a complete answer
- If the retrieved titles partially answer the question, provide what is available and note limitations
- If the retrieved titles do not contain enough information, state that the catalog search did not return sufficient data to answer the question
- If the USER REQUEST is not a question, leave the **answer** field empty

**Examples of DIFFERENT `assessment` vs `answer`:**

Query: "Welche Koautoren gibt es für die Publikationen von Sabine Gehrlein?"
- `assessment`: "Die Treffer sind relevant für das Thema Texterkennung, 3 von 5 Titeln nennen Sabine Gehrlein als Autorin."
- `answer`: "Die Koautoren von Sabine Gehrlein sind Max Mustermann und Erika Musterfrau."

Query: "Was ist der Hauptforschungsbereich von John Smith?"
- `assessment`: "Die Suchergebnisse enthalten 2 Arbeiten von John Smith zum Thema maschinelles Lernen."
- `answer`: "John Smith forscht hauptsächlich auf dem Gebiet des maschinellen Lernens."

## RESPONSE FORMAT

Provide:
- **assessment**: Brief evaluation of how well the results match the query — NOT the answer (IMPORTANT: In {{LANGUAGE}}!)
- **qualityScore**: Overall quality score (0.0-1.0) representing the average relevance of retrieved titles
- **relevantIndices**: List of indices (1-based) of titles that are of HIGH RELEVANCE to the query
- **answer**: Direct factual answer to the question based on the titles — NOT the assessment. Empty string if the query is not a question. (IMPORTANT: In {{LANGUAGE}}!)
