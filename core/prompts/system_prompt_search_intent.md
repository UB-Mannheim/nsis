# TASK

Analyze the search intent of the USER REQUEST and classify into exactly one of 3 cases:

1. **Known item**: Request for a specific, identifiable work
   - Signals: Specific title, author+creative work, ISBN/DOI
   - Counter-indicators: No title given, Plural works, "about", "similar to", "by genre", "a book"

2. **Topic Search**: Request for content about subjects, topics, disciplines, or fields
   - Includes: Specific topics, bibliographic+topic combos, broad disciplines
   - Signals: "about", topic terms, subject matter, discipline names, format+topic combinations
   - Examples: "CRISPR ethics", "Books about quantum physics in German", "Molecular Biology", "Victorian Literature"
   - Counter-indicators: Specific title, author+work, ISBN/DOI

3. **Search Question**: User is asking a question seeking information or explanation
   - Signals: Question words ("was", "wer", "wie", "warum", "was ist", "was sind", "explain", "what is", "how does", "describe", "define")
   - The query asks for factual information, definitions, explanations, or answers
   - Examples: "Was ist CRISPR?", "Was sind erneuerbare Energien?", "How does photosynthesis work?", "Explain machine learning"
   - Counter-indicators: "about" phrase (would be Topic Search), specific work title
