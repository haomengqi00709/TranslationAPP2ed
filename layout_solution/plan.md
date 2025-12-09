# PPT Translation Layout Solution: English → French

## Core Problem
When translating PowerPoint presentations from English to French, text overflow causes layout issues because:
- French text is typically 15-30% longer than English
- PPT text boxes have fixed dimensions
- Overflow results in clipped text, overlapping elements, or inconsistent font sizing

## Solution Approach
Instead of fighting PPT's fixed-layout constraints, we'll use a web-based pipeline:
**PPT → Extract Data → AI Reformat → HTML Render → PDF Export**

This approach leverages HTML/CSS's content-driven layout to automatically handle variable-length text.

## High-Level Pipeline
### Why HTML?
Don't try to calculate pixel positions manually. Instead:
1. **Extract**: Convert PPT to structured data
2. **Reformat**: Use AI to translate and restructure content to fit layout constraints (Markdown/JSON)
3. **Render**: Use HTML/CSS for automatic layout (Flexbox handles alignment)
4. **Export**: Convert HTML to PDF
## Stage 1: Data Extraction (Estimated: 2 hours)

**Goal**: Convert messy PPT into clean JSON data

### Step 1: Build Slide Model
- Use `python-pptx` to read PPT file
- Iterate through each slide and extract:
  - **Title**: The main slide title
  - **Body**: Merge all text box content (ignore positioning - just combine into one text block)
  - **Screenshot** (optional but recommended): Save each slide as an image for reference in the PDF

### Expected Output
A JSON list like:
```json
[
  { "id": 1, "title": "Company Introduction", "content": "We were founded in 2020...", "original_img": "slide1.png" },
  { "id": 2, "title": "Core Technology", "content": "Our deep learning model...", "original_img": "slide2.png" }
]
```
## Stage 2: AI-Powered Restructuring (Estimated: 3 hours)

**Goal**: Solve overflow at the source - don't just translate, but restructure for slide format

### Step 2: Design the Prompt
Don't translate sentence-by-sentence. Feed entire slide content to AI at once.

**Core Prompt Logic**:
```
You are a professional PPT designer. Read the following English content and restructure it as French slide content.

Requirements:
- Translate and condense: Maintain meaning but use concise French (bullet point style)
- Structured output: Return JSON format with french_title and french_points (array)
- Layout constraints: Maximum 4 bullet points, each point maximum 20 words (to prevent overflow)
```

### Step 3: Batch Processing
- Write Python script to loop through Stage 1 JSON
- Call OpenAI/Gemini API for each slide
- Store the AI-returned "condensed French version"

### Why This Solves Overflow
By enforcing hard limits on bullet count and word count, the AI will automatically condense verbose content. This solves the layout problem at the source.
## Stage 3: HTML Template Rendering (Estimated: 4 hours)

**Goal**: Use web layout engines to handle variable-length content automatically

### Step 4: Design HTML Template
Create `template.html` mimicking NotebookLM's "deck" style:

**Layout Design**:
- Use CSS Grid or Flexbox
- Each slide = one card/page (A4 Landscape format)
- **Top**: French title
- **Middle**: Beautiful bullet point list
- **Bottom/Citation**: Original language reference or "Source: Slide X"
- **Styling**: Professional fonts (Roboto, Inter), proper line-height

### Step 5: Data Injection (Jinja2)
- Use Python's Jinja2 library
- Inject Stage 2 AI JSON into HTML template
- Generate complete `output.html` file

**Self-test**: Open HTML in browser - text will auto-reflow without overflow. This is the power of web layout.
## Stage 4: PDF Export (Estimated: 1 hour)

**Goal**: Convert beautiful HTML to distributable PDF

### Step 6: HTML to PDF Conversion

**Option 1 - Manual (Quick Start)**:
- Open `output.html` in browser
- Press Ctrl+P (Print)
- Save as PDF

**Option 2 - Automated (Production)**:
- Use **Playwright** (recommended) or WeasyPrint
- Playwright launches headless browser, renders HTML, exports to PDF
- Output quality matches browser rendering exactly

## Final Demo Flow

**Input**:
```bash
python transform.py my_presentation.pptx
```
(Logs: Extracting... AI restructuring Slide 1... Rendering...)

**Output**:
`French_Briefing.pdf` appears in output folder

**Comparison**:
- **Original PPT**: Dense English text, potential overflow issues
- **New PDF**: Clean, modern layout
  - Concise French titles
  - 3-4 clear bullet points per slide
  - No text overflow - professional magazine-style formatting