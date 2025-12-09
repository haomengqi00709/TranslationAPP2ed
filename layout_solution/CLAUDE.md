# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This project transforms English PowerPoint presentations into French-language PDF briefings while solving text overflow issues. French text is typically 15-30% longer than English, causing layout problems in fixed PPT layouts. The system extracts content from PPT files, uses AI to translate and restructure content to fit layout constraints, and renders the output as a styled HTML document before converting to PDF.

**Core Pipeline:** PPT (English) → Data Extraction → AI Translation & Restructuring (French) → HTML Rendering → PDF Export

The goal is to solve layout overflow issues by using HTML/CSS for automatic layout management rather than fighting PPT's pixel-perfect positioning.

## Architecture

### Four-Stage Processing Pipeline

1. **Extraction Stage**
   - Uses `python-pptx` to parse PowerPoint files
   - Extracts title and body content from each slide
   - Optionally captures slide thumbnails as reference images
   - Outputs structured JSON with slide metadata

2. **AI Restructuring Stage**
   - Processes extracted English content through LLM (OpenAI/Gemini)
   - Translates to French AND condenses into concise bullet points
   - Enforces constraints: max 4 points per slide, max 20 words per point (accounting for French expansion)
   - Generates `summary_one_liner` for each slide
   - This stage prevents text overflow by translating AND reducing content at the source

3. **HTML Rendering Stage**
   - Uses Jinja2 templates to generate HTML
   - Implements dual-pane layout: original slide preview (35% width) + AI content (65% width)
   - Leverages Flexbox/CSS Grid for automatic layout management
   - Extracts and applies primary color from original PPT for theming
   - Each slide becomes a fixed-height card (600px) with overflow protection

4. **PDF Export Stage**
   - Converts HTML to PDF using Playwright (headless browser)
   - Alternative: WeasyPrint for simpler deployments
   - Output mimics NotebookLLM's clean, magazine-style formatting

### Key Design Decisions

**Why HTML instead of direct PDF generation?**
- Web layout engines handle text reflow automatically
- CSS provides sophisticated typography and spacing controls
- Easier to iterate on design vs. calculating pixel positions
- Browser print APIs produce high-quality PDF output

**Overflow Prevention Strategy**
- Source-level: AI limits content volume (word/point counts)
- Layout-level: CSS flexbox allows dynamic height adjustment
- Constraint: Fixed 600px height per slide card forces content fitting

## Development Approach

### V1.0 Simplifications

**Slide Screenshots**: Don't attempt programmatic screenshot capture. Instead:
- Pre-export slides as PNG/JPG using PowerPoint's "Save as Pictures" feature
- Reference these pre-generated images by index in the Python script

**Color Extraction**: For professional theming:
- Extract primary color from PPT using `colorgram.py` library
- Inject as CSS variable `--primary-color` in the template
- Fallback: Manual category mapping (tech=blue, medical=green)

### Template Structure

The HTML template uses a card-based layout with:
- `.page-container`: Flexbox container with box-shadow for depth
- `.slide-preview`: Left panel showing original slide thumbnail
- `.ai-content`: Right panel with title, summary, bullet points, citation
- `.citation`: Auto-positioned at bottom using `margin-top: auto`

## File Organization

Expected structure:
```
/
├── plan.md              # Initial architecture plan (Chinese)
├── plan2.md             # V1.0 execution details (Chinese)
├── transform.py         # Main processing script (to be implemented)
├── template.html        # Jinja2 HTML template (to be implemented)
├── slides/              # Pre-exported PNG images from PPT
└── output/              # Generated HTML and PDF files
```

## LLM Integration

**Prompt Structure for Content Restructuring:**
```
You are a professional PPT designer. Read the following English content
and restructure it as French slide content.

Requirements:
- Translate and condense: maintain meaning but use concise French (bullet point style)
- Structured output: Return JSON with french_title, summary_one_liner, and french_points (array)
- Fit constraints: Max 4 points, max 20 words per point (prevent overflow despite French being longer)
```

**Expected JSON Response:**
```json
{
  "french_title": "...",
  "summary_one_liner": "...",
  "french_points": ["...", "...", "..."]
}
```

## Technical Stack

- **PPT Parsing**: `python-pptx`
- **Templating**: `jinja2`
- **PDF Generation**: `playwright` (preferred) or `weasyprint`
- **LLM API**: OpenAI or Gemini
- **Color Extraction**: `colorgram.py`
- **Image Format**: PNG for slide thumbnails

## Quality Targets

The output PDF should achieve:
- No text overflow or clipping
- Magazine-style visual polish (shadows, spacing, typography)
- Left-right layout showing original context + AI summary
- Theme colors matching original presentation
- "Executive Briefing" presentation quality
