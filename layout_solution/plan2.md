# Implementation Details (V1.0 Shortcuts)

## Step 1: Prepare Assets (Practical Shortcuts for Demo)

**Technical Challenge**: Programmatically capturing high-quality slide screenshots is complex on non-Windows platforms.

**V1.0 Shortcut**: Don't fight with screenshot code.

**Manual Process**:
1. Open your PPT file
2. Go to "File → Save as → Pictures (PNG/JPG) → All Slides"
3. Result: You get a folder with `Slide1.PNG`, `Slide2.PNG`, etc.

**Code Logic**: Your Python script simply references these pre-exported images by index.
## Step 2: Extraction & AI Restructuring

Same as main plan: use `python-pptx` to extract text, use LLM to restructure.

**Key Prompt Enhancement**:
Ensure AI returns JSON with `summary_one_liner` field (one-sentence summary). This makes the layout look more professional.
## Step 3: HTML Layout (The Heart of V1.0)

Don't create a top-to-bottom flow document. Use a **Grid layout** instead.

### template.html Design Logic:
<style>
  /* V1.0 Core: Magazine-style CSS */
  :root {
    --primary-color: #0056b3; /* Dynamically replaced with PPT's primary color */
  }
  body { font-family: 'Helvetica Neue', sans-serif; background: #f4f4f4; }
  
  .page-container {
    display: flex;       /* Left-right split layout */
    background: white;
    margin-bottom: 20px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1); /* Card-like depth */
    overflow: hidden;    /* Prevent overflow */
    height: 600px;       /* Fixed height (A4 landscape half or PPT aspect ratio) */
  }

  /* Left: Original slide preview (35% width) */
  .slide-preview {
    flex: 0 0 35%;
    background-color: #eee;
    display: flex;
    align-items: center;
    justify-content: center;
    border-right: 1px solid #ddd;
  }
  .slide-preview img {
    max-width: 90%;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
  }

  /* Right: AI content area (65% width) */
  .ai-content {
    flex: 1;
    padding: 40px;
    display: flex;
    flex-direction: column;
  }

  /* Decorative details */
  h2 { color: var(--primary-color); margin-top: 0; }
  .summary {
    font-style: italic;
    color: #666;
    border-left: 4px solid var(--primary-color);
    padding-left: 10px;
    margin-bottom: 20px;
  }
  ul { line-height: 1.8; color: #333; }
  .citation {
    margin-top: auto; /* Push to bottom */
    font-size: 12px; color: #999; text-align: right;
  }
</style>

<!-- Each PPT slide corresponds to one block like this -->
<div class="page-container">
  <div class="slide-preview">
    <img src="{{ slide_image_path }}" />
  </div>
  <div class="ai-content">
    <h2>{{ french_title }}</h2>
    <div class="summary">{{ summary_one_liner }}</div>
    <ul>
      {% for point in points %}
      <li>{{ point }}</li>
      {% endfor %}
    </ul>
    <div class="citation">Source: Slide {{ slide_number }} | Refactored by AI</div>
  </div>
</div>
## Step 4: Add Soul (Color Extraction)

To achieve V1.0's "professional feel", don't make all PDFs blue.

**Simple Approach**:
Write a basic mapping in your Python script:
- Tech presentations → Deep blue
- Medical presentations → Teal/green
- Or extract primary color from first slide's background using `colorgram.py` library (just a few lines of code)

Pass this color code to the HTML's `--primary-color` variable.

**Effect**: Instantly, your PDF has a "customized" feel.
## Final V1.0 Deliverable

When you share this PDF, people won't see a "translation document" - they'll see:

**Cover**: Beautiful title reading "Executive Briefing: [original filename]"

**Content Pages**:
- **Left**: Original PPT thumbnail (gives context and confidence)
- **Right**: Perfectly formatted French bullet points with zero overflow
- **Theme**: Colors match original PPT exactly
- **Footer**: "Powered by Layout-Aware AI Engine"

## Why This Qualifies as Mature V1.0

1. **Solves Core Pain Point**: Text overflow is eliminated (HTML auto-reflows)
2. **Adds Value**: Not just translation - transforms messy slides into structured briefing
3. **Visual Polish**: Side-by-side comparison + theme color adaptation = high perceived completion