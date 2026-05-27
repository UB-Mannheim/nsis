## User Workflows

### Main Search Workflow

```mermaid
flowchart TD
    A[User enters natural language query] --> B[UI: Show loading state]
    B --> C[Pipeline: SI + QE + QT in parallel]
    C --> D{SI Complete?}
    C --> E{QE Complete?}
    C --> F{QT Complete?}
    D -->|Yes| G[Store search intent metadata]
    E -->|Yes| H[Auto-toggle keywords active]
    F -->|Yes| I[Render options panel]
    G --> J[All steps done]
    H --> J
    I --> J
    J --> K[Snapshot initial options for reset]
    K --> L[Rebuild URL from active options]
    L --> M[Fetch VuFind]
    M --> N[Show result count + titles]
    N --> O[Fetch query quality assessment]
    O --> P[Display quality score + assessment]
    P --> Q[Highlight relevant titles]
    Q --> R[User toggles options]
    R --> S[URL regenerates]
    S --> T[User clicks Title / Open in VuFind]
```

### Options Toggle Workflow

```mermaid
flowchart LR
    A[User toggles option checkbox] --> B[Update option active state]
    B --> C[Rebuild URL from all active options]
    C --> D[Show loading state immediately]
    D --> E[Increment fetchId]
    E --> F[Start debounce timer]
    F --> G[After delay, fetch VuFind]
    G --> H[Show result count + titles]
    H --> I[Fetch query quality]
    I --> J[Update quality score display]
    J --> K[Highlight relevant results]
```

### Keyword Addition Workflow

```mermaid
flowchart LR
    A[User enters custom keyword] --> B[Check for duplicates]
    B -->|duplicate| C[Show temporary error tooltip]
    B -->|new| D[POST /add-keyword-to-concepts]
    D --> E{LLM Decision}
    E -->|sub_concept| F[Add to existing concept]
    E -->|super_concept| G[Create new superconcept, reassign others]
    E -->|new_concept| H[Create standalone concept]
    F --> I[Update qeConcepts.positive]
    G --> I
    H --> I
    I --> J[Insert option before placeholder]
    J --> K[POST /build-logical-tree]
    K --> L[Update qeMeta.logicalTree]
    L --> M[Render options panel]
    M --> N[Rebuild URL and fetch VuFind immediately]
```

### Custom Topic Heading Workflow

```mermaid
flowchart LR
    A[User enters topic term] --> B[POST /lookup-vocabulary gnd-saz]
    A --> C[POST /lookup-vocabulary gnd-geo]
    B --> D{Results?}
    C --> D
    D -->|empty| E[Show empty message in popup]
    D -->|results| F[Show selection popup]
    F --> G[User selects GND headings]
    G --> H[POST /add-keyword-to-concepts]
    H --> I[Update qtConcepts.positive]
    I --> J[Insert options before placeholder]
    J --> K[POST /build-logical-tree]
    K --> L[Update qtMeta.logicalTree]
    L --> M[Render options panel]
    M --> N[Rebuild URL and fetch VuFind immediately]
```

### Custom BK Number Workflow

```mermaid
flowchart LR
    A[User enters BK notation] --> B[POST /lookup-vocabulary bk]
    B --> C{Results?}
    C -->|empty| D[Show empty message in popup]
    C -->|results| E[Show selection popup]
    E --> F[User selects BK notations]
    F --> G[Insert options before placeholder]
    G --> H[Render options panel]
    H --> I[Rebuild URL and fetch VuFind immediately]
```

### Option Removal Workflow

```mermaid
flowchart TD
    A[User clicks remove button] --> B{Option active?}
    B -->|Yes| C[Toggle option off]
    B -->|No| D[Continue]
    C --> D
    D --> E[Remove from STATE.options]
    E --> F{category keyword?}
    E --> G{category topic_facet?}
    F -->|Yes| H[Rebuild logical tree]
    G -->|Yes| H
    F -->|No| I
    G -->|No| I
    H --> I[Render options panel]
    I --> J[Rebuild URL and fetch VuFind immediately]
```

### Reset Options Workflow

```mermaid
flowchart LR
    A[User clicks Reset button] --> B[Restore STATE.options from initialOptions]
    B --> C[Render options panel]
    C --> D[Rebuild URL and fetch VuFind immediately]
```

### History Restoration Workflow

```mermaid
flowchart TD
    A[User clicks history item] --> B[Abort any in-flight requests]
    B --> C[Clear pending debounce timer]
    C --> D[Restore STATE from snapshot]
    D --> E[Restore search input value]
    E --> F[Render options panel]
    F --> G[Restore URL display]
    G --> H[Restore VuFind results]
    H --> I[Restore quality score]
    I --> J[Show results subtitle]
```

### Quality Assessment Workflow

```mermaid
flowchart LR
    A[VuFind results returned] --> B[POST /query-judge-quality]
    B --> C[LLM analyzes query-result match]
    C --> D[Return quality score 0-1]
    D --> E[Return relevant indices]
    E --> F[Update quality score display]
    F --> G[Highlight relevant title badges]
```

### Vocabulary Selection Popup Workflow

```mermaid
flowchart TD
    A[Popup opens with vocabulary results] --> B[User can toggle items]
    B --> C[Select Some / Select All / Deselect All]
    C --> D[User clicks Apply]
    D --> E[Close popup]
    E --> F[Return selected items to handler]
    F --> G{topic_facet or bk?}
    G -->|topic_facet| H[POST /add-keyword-to-concepts]
    G -->|bk| I[Insert options before placeholder]
    H --> J[Update qtConcepts.positive]
    J --> K[POST /build-logical-tree]
    K --> L[Update qtMeta.logicalTree]
    L --> M[Render options panel]
    I --> M
    M --> N[Rebuild URL and fetch VuFind immediately]
    C --> O[User clicks overlay/Escape]
    O --> P[Close popup]
    P --> Q[Return to options state]