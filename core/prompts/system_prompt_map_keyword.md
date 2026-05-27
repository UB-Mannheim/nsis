# TASK
Determine if a KEYWORD should map to an existing concept, become a new supercategory, or create a new concept.

## KEYWORD
`{keyword}`

## EXISTING CONCEPTS
`{existing_concepts}`

## DECISION RULES
Apply these rules in order:

1. **SUPER_CONCEPT** if keyword is a broader term that contains/explains existing concepts:
   - "Europa" with "Osteuropa" → super_concept (Europa is the continent, Osteuropa is a region)
   - "Science" with "Physics", "Chemistry" → super_concept
   - "Music" with "Rock", "Jazz" → super_concept

2. **SUB_CONCEPT** if keyword is a specific instance or narrower topic of existing concepts:
   - "EU" with "European Union" → sub_concept (abbreviation maps to full name)
   - "Dogs" with "Mammals" → sub_concept (subcategory)
   - "Renaissance Art" with "Art" → sub_concept

   SUB_CONCEPT means the keyword is a *type of* the existing concept (definitional hierarchy). If the keyword is merely a specific subject or event that *belongs to* the concept's domain, this is NOT sub_concept — use new_concept instead.

3. **NEW_CONCEPT** if keyword is unrelated to all existing concepts:
   - "Cooking" with "Physics" → new_concept
   - "Sports" with "Computer Science" → new_concept

## ABSORBED CONCEPTS FOR SUPER_CONCEPT
When decision is "super_concept", list the concept keys to absorb (not the individual terms):
- Only provide the concept keys that should be absorbed into the new supercategory

## OUTPUT (JSON)
```json
{
  "decision": "sub_concept" | "super_concept" | "new_concept",
  "concept_key": "existing key OR keyword",
  "absorbed_concepts": ["SubConcept", "AnotherConcept"]
}
```
