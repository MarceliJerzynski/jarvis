---
project_name: 'laps'
user_name: 'Marceli'
status: 'complete'
optimized_for_llm: true
---

# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in this project._

---
## Critical Rules

- **Human-Mediated UI/UX (No Sally agent needed):** Aplikacja posiada warstwę frontendową (Angular), ale nie istnieją żadne formalne dokumenty makiety ani pliki UI/UX. Wszystkie decyzje dotyczące wyglądu i zachowania interfejsu podejmuje Marceli na podstawie bezpośrednich ustaleń z człowiekiem od UI/UX. Agenci nie mogą szukać zewnętrznych plików UX, żądać ich tworzenia ani zgłaszać ich braku jako błędu. Wszelkie wymagania dotyczące interfejsu są opisywane bezpośrednio w PRD lub doprecyzowywane w rozmowie z Marcelim.
- **BMAD Artifact Paths:** NEVER save absolute file paths in the output artifacts; ALWAYS prefer relative paths to the project root.
- **User Task:** NEVER modify the original user task description and supporting files in the `.bmad/tasks/**`.
- **Framework Documentation:** When asked to read framework documentation or get an overview about the framework then use documents in the `.bmad/docs/framework` folder as the first choice.
- **SP means Framework, Framework means SP:** 'Service Platform Framework', 'SP Framework', 'Framework', 'SP' are all synonyms.
