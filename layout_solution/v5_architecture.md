# V5 Architecture: AI Content Restructuring

## Philosophy Shift

**V4 (Translation Mode):**
- Original structure → Translate 1:1 → French output
- Preserves bullet count, slide count
- Problem: Dense slides stay dense

**V5 (Restructuring Mode):**
- Original content → AI analyzes meaning → Optimal presentation
- May split/merge slides
- May extract data into cards, condense narrative into bullets
- **Goal: Present content the way NotebookLLM would**

---

## AI Decision Framework

```
INPUT: Slide content (title + body text)
↓
STEP 1: Content Analysis
- What type of content is this? (data/process/findings/context)
- How dense is it? (word count, number of distinct ideas)
- Are there extractable statistics?
↓
STEP 2: Layout Decision
- Data-heavy (5+ numbers) → Clean Cards
- Relational data → Styled Table
- Dense methodology → Split into Context + Stats
- Narrative findings → Condense to Text Bullets
- Section divider → Section Header
↓
STEP 3: Content Transformation
- Extract key numbers for cards
- Condense paragraphs to bullets
- Split if content exceeds ~150 words
↓
OUTPUT: 1-3 optimized slides
```

---

## Example: Slide 2 Transformation

**ORIGINAL (1 slide, 9 paragraph bullets):**
```
Title: Objectifs et méthodologie
- **Objectif**
- En mai 2019, le Bureau... [paragraph]
- Cette présentation résume... [paragraph]
- **Méthodologie**
- Environics a conçu... [paragraph]
- Les employés et superviseurs... [paragraph]
- **Rapport**
- On a demandé aux employés... [paragraph]
```

**V5 RESTRUCTURED (3 slides):**

**Slide 2.1: Section Header**
```json
{
  "id": "2.1",
  "layout_type": "section_header",
  "french_title": "Méthodologie de recherche",
  "summary_one_liner": "Sondage ROP d'octobre 2019 sur les mesures d'adaptation en milieu de travail"
}
```

**Slide 2.2: Key Stats (Clean Cards)**
```json
{
  "id": "2.2",
  "layout_type": "clean_cards",
  "french_title": "Échantillon du sondage",
  "summary_one_liner": "980 réponses valides recueillies entre le 22 et 29 octobre 2019",
  "cards": [
    {"number": "980", "label": "Réponses totales", "sublabel": "Sondage de suivi ROP"},
    {"number": "802", "label": "Employés", "sublabel": "Participants au sondage"},
    {"number": "178", "label": "Superviseurs", "sublabel": "Participants au sondage"},
    {"number": "30 min", "label": "Durée moyenne", "sublabel": "Par questionnaire"}
  ]
}
```

**Slide 2.3: Context (Text Bullets)**
```json
{
  "id": "2.3",
  "layout_type": "text_bullets",
  "french_title": "Objectifs de la recherche",
  "summary_one_liner": "Comprendre les expériences d'adaptation en milieu de travail fédéral",
  "french_points": [
    "Premier sondage BAFP mené en mai 2019 sur les mesures d'adaptation",
    "Sondage de suivi ROP en automne 2019 pour approfondir les conclusions",
    "Échantillons non probabilistes d'employés et superviseurs du sondage initial",
    "Résultats focalisés sur les demandes liées à un handicap (93% des répondants)"
  ]
}
```

---

## Output JSON Structure

```json
[
  {
    "source_slide_id": 2,
    "original_title": "Objectifs et méthodologie",
    "output_slides": [
      {
        "id": "2.1",
        "layout_type": "section_header",
        "french_title": "...",
        "summary_one_liner": "..."
      },
      {
        "id": "2.2",
        "layout_type": "clean_cards",
        "french_title": "...",
        "cards": [...]
      },
      {
        "id": "2.3",
        "layout_type": "text_bullets",
        "french_title": "...",
        "french_points": [...]
      }
    ]
  }
]
```

---

## Restructuring Rules

1. **Single output (1→1)** when:
   - Content is already concise (≤5 bullets, ≤100 words)
   - Clear single topic
   - Examples: Most V4 slides

2. **Split output (1→2 or 1→3)** when:
   - Dense methodology (>200 words)
   - Multiple distinct topics (Objectives + Methodology + Report conventions)
   - Extractable statistics mixed with narrative

3. **Merge output (2→1)** when:
   - Consecutive slides cover same topic
   - Section header + single bullet slide
   - (Not implementing in V5.0, future feature)

---

## AI Prompt Strategy

**Phase 1: Content Analysis**
```python
prompt = f"""
Analyze this slide content and determine optimal presentation structure.

CONTENT:
Title: {slide['title']}
Body: {slide['content']}

ANALYSIS TASKS:
1. Content type: [data-heavy / process / findings / context / section-divider]
2. Density: [concise / moderate / dense]
3. Extractable statistics: [list key numbers with labels]
4. Distinct topics: [count and list]

DECISION:
- How many output slides? (1-3)
- Layout for each slide?
- What content goes where?

OUTPUT (JSON only):
{
  "analysis": {
    "content_type": "...",
    "density": "dense",
    "key_statistics": [{"number": "980", "context": "total responses"}],
    "topics": ["objectives", "methodology", "report conventions"]
  },
  "decision": {
    "output_count": 3,
    "slides": [
      {"layout": "section_header", "content_focus": "..."},
      {"layout": "clean_cards", "content_focus": "..."},
      {"layout": "text_bullets", "content_focus": "..."}
    ]
  }
}
"""
```

**Phase 2: Content Generation** (for each decided slide)
```python
prompt = f"""
Generate French content for this slide.

ORIGINAL CONTENT: {full_context}
TARGET LAYOUT: {decided_layout}
FOCUS: {content_focus}

Requirements:
- Extract/condense only the relevant parts for this slide's focus
- Natural French translation
- Fit layout constraints (cards need numbers, bullets need conciseness)

OUTPUT (JSON): {{layout-specific structure}}
"""
```

---

## Implementation Plan

1. **translate_ai_v5.py**:
   - `analyze_slide_structure()` → Decision on split/layout
   - `generate_slide_content()` → Create each output slide
   - Two-phase API calls per source slide

2. **render_html_v5.py**:
   - Flatten output_slides array
   - Handle "2.1", "2.2" slide IDs
   - Same template as V4

3. **Testing**:
   - Start with Slide 2 only (known problem case)
   - Compare V5 vs V4 output
   - Then run full 10-slide corpus

---

## Fallback to V4

V5 is experimental. If AI makes poor decisions:
- V4 guaranteed to work (1:1 translation)
- V5 requires validation (did split make sense?)
- Keep both systems available
