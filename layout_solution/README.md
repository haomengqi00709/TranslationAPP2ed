# PowerPoint to French PDF Translation Pipeline

**AI-Powered PPT → PDF Translation with Chart Recreation**

Transform English PowerPoint presentations into professionally-formatted French PDF documents with AI vision analysis, chart recreation, and intelligent layout optimization.

---

## 🌟 What Makes This Special

### **Chart Recreation with AI Vision**
Unlike traditional converters that export charts as static images, this system:
- 🔍 **AI Vision analyzes** PowerPoint chart images
- 📊 **Extracts data** automatically (values, labels, colors)
- ✨ **Recreates charts** using Chart.js (live, interactive rendering)
- 📄 **PDF-ready output** with data labels visible (no tooltips needed)

### **Intelligent Layout Management**
- 🤖 **AI decides** optimal layout for each slide
- 🇫🇷 **Prevents overflow** caused by French text expansion (15-30%)
- 📐 **7+ layout types** automatically selected
- 🎨 **Magazine-style** professional formatting

### **100% Generalized Pipeline**
- ✅ Works with **ANY** PowerPoint file
- ✅ **No hardcoded** slide numbers, chart types, or content
- ✅ Charts, tables, text all detected **automatically**
- ✅ AI makes all decisions **dynamically**

---

## 📊 Quick Stats

**Current Working Example:**
- Input: 20-slide English PowerPoint with 5 charts
- Output: 0.68 MB professional French PDF
- Charts: 4 recreated with Chart.js, 1 fallback image
- Processing: ~60-90 seconds (including AI vision analysis)

---

## 🚀 Two Ways to Use

### **1. Standalone Pipeline** (Direct Use)

```bash
# Extract → Translate → Render → Export
python3 extract_ppt_v2.py your-file.pptx
python3 export_slides_as_images.py your-file.pptx
python3 translate_ai_v5.py
python3 render_html_v5.py
python3 export_pdf.py

# Result: output/output_v5.pdf
```

### **2. REST API Integration** (For Existing Systems)

```bash
# Start API server
python3 api_server.py

# Use from your frontend
POST /api/translate/pdf (upload file)
GET  /api/jobs/{id}/status (poll progress)
GET  /api/jobs/{id}/download (download PDF)
```

---

## 🎯 Complete Pipeline Overview

```
PowerPoint (.pptx)
    ↓
┌─────────────────────────────────────────┐
│ Stage 1: Extract                        │
│ • Detect charts, tables, text           │
│ • Extract metadata                      │
│ → extracted_slides_v2.json              │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ Stage 2: Image Export                   │
│ • Convert PPT → PDF → PNG (300 DPI)     │
│ • One image per slide                   │
│ → slides_images/slide*.png              │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ Stage 3: AI Translation + Vision        │
│ • Text slides: Analyze & translate      │
│ • Chart slides: Vision AI extracts data │
│ • Choose optimal layouts                │
│ → translated_slides_v5.json             │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ Stage 4: HTML Rendering                 │
│ • Render with Jinja2 template           │
│ • Charts rendered with Chart.js         │
│ • All layouts styled                    │
│ → output_v5.html                        │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ Stage 5: PDF Export                     │
│ • Playwright renders HTML → PDF         │
│ • Waits for Chart.js to finish          │
│ • High-quality print output             │
│ → output_v5.pdf                         │
└─────────────────────────────────────────┘
```

---

## 📦 Installation

### Prerequisites

```bash
# Python 3.11+
python3 --version

# System dependencies (macOS)
brew install --cask libreoffice
brew install poppler

# System dependencies (Ubuntu/Debian)
apt-get install libreoffice poppler-utils
```

### Python Dependencies

```bash
# Install all dependencies
pip3 install -r requirements.txt

# Install Playwright browser
playwright install chromium
```

### Configuration

```bash
# 1. Create .env file
echo "GEMINI_API_KEY=your_api_key_here" > .env

# 2. Create glossary.json (optional)
cat > glossary.json << 'EOF'
{
  "accommodation": "mesure d'adaptation",
  "disability": "handicap",
  "supervisor": "superviseur",
  "request": "demande"
}
EOF
```

---

## 🎮 Usage

### Standalone Mode

```bash
# Step 1: Extract content from PowerPoint
python3 extract_ppt_v2.py path/to/your-presentation.pptx

# Step 2: Export slide images for vision analysis
python3 export_slides_as_images.py path/to/your-presentation.pptx

# Step 3: AI translation and vision analysis
python3 translate_ai_v5.py

# Step 4: Render HTML with Chart.js
python3 render_html_v5.py

# Step 5: Export to PDF
python3 export_pdf.py

# Open result
open output/output_v5.pdf
```

### API Server Mode

```bash
# Terminal 1: Start server
python3 api_server.py
# Server runs on http://localhost:5000

# Terminal 2: Test with example frontend
open frontend_example.html

# Or test API directly
curl -X POST http://localhost:5000/api/translate/pdf \
  -F "file=@test.pptx"
```

### Programmatic Use

```python
from api_wrapper import ppt_to_pdf_pipeline

# Simple one-function call
result = ppt_to_pdf_pipeline(
    ppt_path="presentation.pptx",
    output_dir="output",
    progress_callback=lambda p: print(p.to_dict())
)

if result["success"]:
    print(f"PDF: {result['pdf_path']}")
    print(f"Stats: {result['stats']}")
```

---

## 📊 Chart Vision Analysis

### Supported Chart Types

| PowerPoint Type | Detection | Recreation | Quality |
|----------------|-----------|------------|---------|
| Column/Bar Chart | ✅ Auto | Chart.js | ⭐⭐⭐⭐⭐ |
| Pie/Doughnut | ✅ Auto | Chart.js | ⭐⭐⭐⭐⭐ |
| Line Chart | ✅ Auto | Chart.js | ⭐⭐⭐⭐⭐ |
| Stacked Charts | ✅ Auto | Chart.js | ⭐⭐⭐⭐ |
| Complex Multi-series | ✅ Auto | Fallback (image) | ⭐⭐⭐ |

### How Vision Analysis Works

```python
# 1. AI receives chart image
image_path = "output/slides_images/slide8.png"

# 2. Gemini Vision API analyzes
prompt = """
Analyze this chart and extract data in Chart.js format.
Return: chart type, labels, data, colors
"""

# 3. Returns structured data
{
  "layout_decision": "bar_chart",
  "chart_data": {
    "labels": ["Category 1", "Category 2", ...],
    "datasets": [{
      "data": [22, 41, 25, 6, 6],
      "backgroundColor": "#6A329F"
    }]
  }
}

# 4. Chart.js recreates in HTML
<canvas id="chart-8"></canvas>
new Chart(ctx, { type: 'bar', data: chart_data });

# 5. Playwright renders to PDF
```

**Result:** High-quality vector chart in PDF, not a pixelated screenshot!

---

## 🎨 Layout Types

AI automatically selects from 7+ layout types:

### **Text-Based Layouts**
- **`text_bullets`** - Standard bullet points (max 4 bullets, 20 words each)
- **`section_header`** - Chapter/section dividers
- **`quote`** - Emphasized key insights

### **Data Visualization**
- **`bar_chart`** - Vertical bars comparing categories
- **`column_chart`** - Horizontal bars for long labels
- **`pie_chart`** - Parts of a whole (proportions)
- **`line_chart`** - Trends over time
- **`chart_image`** - Fallback for complex charts

### **Structured Data**
- **`styled_table`** - Multi-column comparisons
- **`clean_cards`** - 2-4 key statistics with emphasis

**Example AI Decision:**
```json
{
  "content_type": "comparison-heavy",
  "density": "dense",
  "decision": "Split into 2 slides",
  "layouts": ["text_bullets", "styled_table"]
}
```

---

## 🛠️ Technical Architecture

### Core Components

| File | Purpose | Input | Output |
|------|---------|-------|--------|
| `extract_ppt_v2.py` | Parse PPT structure | .pptx | JSON |
| `export_slides_as_images.py` | Generate slide images | .pptx | PNG files |
| `analyze_charts_vision.py` | AI vision for charts | PNG + metadata | Chart.js data |
| `translate_ai_v5.py` | AI translation + restructure | JSON + images | JSON |
| `render_html_v5.py` | HTML generation | JSON | HTML |
| `template_v4.html` | Jinja2 template | Variables | Rendered HTML |
| `export_pdf.py` | PDF export | HTML | PDF |

### Integration Layer

| File | Purpose | Use Case |
|------|---------|----------|
| `api_wrapper.py` | Single-function wrapper | Simple programmatic use |
| `api_server.py` | Flask REST API | Frontend integration |
| `frontend_example.html` | Complete UI demo | Reference implementation |

---

## 🔧 Configuration Options

### Environment Variables

```bash
# Required
GEMINI_API_KEY=your_api_key_here

# Optional (with defaults)
API_PORT=5000
MAX_FILE_SIZE_MB=50
UPLOAD_FOLDER=uploads
OUTPUT_FOLDER=output
```

### Customization Examples

**Change primary color:**
```python
# In render_html_v5.py
render_html_v5(
    slides_data=slides,
    primary_color="#0056b3"  # Your brand color
)
```

**Adjust AI content limits:**
```python
# In translate_ai_v5.py, build_analysis_prompt()
- Max 4 bullet points per slide
- Max 20 words per bullet
- Modify these constraints in prompt
```

**Custom glossary:**
```json
{
  "technical_term": "terme technique",
  "your_product_name": "Nom de votre produit"
}
```

---

## 📈 Performance & Cost

### Processing Time (20-slide deck)

| Stage | Time | Bottleneck |
|-------|------|------------|
| 1. Extract | 5s | I/O |
| 2. Images | 15s | LibreOffice conversion |
| 3. AI Translation | 30-40s | API calls (rate-limited) |
| 4. Render HTML | 3s | Template processing |
| 5. Export PDF | 10s | Playwright rendering |
| **Total** | **60-90s** | AI API calls |

### API Costs (Gemini Flash)

- **Free tier:** 10 req/min, 20 req/day
- **Text analysis:** ~2 requests/slide = 40 requests
- **Vision analysis:** 1 request/chart = ~5 requests
- **Total tokens:** ~30-35k tokens per deck
- **Cost:** $0.05-0.10 per deck (within free tier limits)

### Optimization Tips

1. **Parallel processing** - Process non-chart slides concurrently
2. **Caching** - Store results for 24 hours (avoid reprocessing)
3. **Rate limiting** - Already implemented (6s delay between vision calls)
4. **Batch mode** - Process multiple files sequentially

---

## 🚨 Troubleshooting

### Common Issues

**1. Charts not showing in PDF**
```
Issue: ChartDataLabels plugin not registered
Fix: Already fixed - plugin loads in <head> before charts
```

**2. French translation missing for charts**
```
Issue: Old output from before translation feature
Fix: Re-run python3 translate_ai_v5.py
```

**3. API quota exceeded**
```
Error: 429 You exceeded your current quota
Fix: Wait for quota reset (10 req/min limit)
     Or upgrade to paid tier
```

**4. PDF export fails on macOS**
```
Error: Browser closed unexpectedly
Fix: Already fixed - using --single-process flag
```

**5. Charts render as blank boxes**
```
Issue: Chart.js not loaded or network timeout
Fix: Check internet connection (Chart.js CDN)
     Or download Chart.js locally
```

### Debug Mode

```python
# Enable verbose logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check intermediate outputs
ls output/
cat output/extracted_slides_v2.json
cat output/translated_slides_v5.json
open output/output_v5.html  # Debug before PDF export
```

---

## 📁 File Structure

```
Layout_solution/
├── Core Pipeline
│   ├── extract_ppt_v2.py              # Stage 1: PPT extraction
│   ├── export_slides_as_images.py     # Stage 2: Image export
│   ├── translate_ai_v5.py             # Stage 3: AI translation
│   ├── analyze_charts_vision.py       #   └─ Vision analysis
│   ├── render_html_v5.py              # Stage 4: HTML rendering
│   └── export_pdf.py                  # Stage 5: PDF export
│
├── Integration Layer
│   ├── api_wrapper.py                 # Single-function API
│   ├── api_server.py                  # Flask REST server
│   └── frontend_example.html          # Complete UI demo
│
├── Templates & Config
│   ├── template_v4.html               # Jinja2 template
│   ├── glossary.json                  # Translation glossary
│   ├── .env                           # API keys (create this)
│   └── requirements.txt               # Python dependencies
│
├── Documentation
│   ├── README.md                      # This file
│   ├── INTEGRATION_GUIDE.md           # Integration instructions
│   └── demo_charts.html               # Chart.js demo
│
└── Output
    ├── extracted_slides_v2.json       # Stage 1 output
    ├── slides_images/                 # Stage 2 output
    ├── translated_slides_v5.json      # Stage 3 output
    ├── output_v5.html                 # Stage 4 output
    └── output_v5.pdf                  # Stage 5 output (final)
```

---

## 🔌 API Reference

### REST Endpoints

```
POST /api/translate/pdf
  - Upload PowerPoint file
  - Returns: { job_id, status, message }

GET /api/jobs/{job_id}/status
  - Check progress
  - Returns: { progress, status, result }

GET /api/jobs/{job_id}/download?type=pdf
  - Download generated PDF
  - type: 'pdf' or 'html'

GET /api/health
  - Health check
  - Returns: { status: "healthy" }
```

### Progress Callback Format

```json
{
  "current_stage": 3,
  "total_stages": 5,
  "progress_percent": 60,
  "status": "running",
  "message": "AI analyzing charts...",
  "error": null
}
```

### Result Format

```json
{
  "success": true,
  "pdf_path": "/path/to/output.pdf",
  "html_path": "/path/to/output.html",
  "stats": {
    "source_slides": 20,
    "output_slides": 22,
    "chart_slides": 4,
    "pdf_size_mb": 0.68
  }
}
```

---

## 🌐 Integration Examples

### React Example

```jsx
import { useState } from 'react';

function PPTTranslator() {
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);

  const translateToPDF = async (file) => {
    // Upload
    const formData = new FormData();
    formData.append('file', file);

    const { job_id } = await fetch('/api/translate/pdf', {
      method: 'POST',
      body: formData
    }).then(r => r.json());

    // Poll progress
    const interval = setInterval(async () => {
      const job = await fetch(`/api/jobs/${job_id}/status`)
        .then(r => r.json());

      setProgress(job.progress.progress_percent);

      if (job.status === 'completed') {
        clearInterval(interval);
        setResult(job.result);
      }
    }, 1000);
  };

  return (
    <div>
      <input type="file" onChange={e => translateToPDF(e.target.files[0])} />
      {progress > 0 && <ProgressBar value={progress} />}
      {result && <a href={`/api/jobs/${job_id}/download`}>Download PDF</a>}
    </div>
  );
}
```

### Vue Example

```vue
<template>
  <div>
    <input type="file" @change="handleFile" />
    <progress :value="progress" max="100" />
    <a v-if="pdfUrl" :href="pdfUrl">Download PDF</a>
  </div>
</template>

<script>
export default {
  data() {
    return {
      progress: 0,
      pdfUrl: null
    }
  },
  methods: {
    async handleFile(e) {
      const file = e.target.files[0];
      const formData = new FormData();
      formData.append('file', file);

      const { job_id } = await fetch('/api/translate/pdf', {
        method: 'POST',
        body: formData
      }).then(r => r.json());

      this.pollProgress(job_id);
    },
    async pollProgress(jobId) {
      const interval = setInterval(async () => {
        const job = await fetch(`/api/jobs/${jobId}/status`)
          .then(r => r.json());

        this.progress = job.progress.progress_percent;

        if (job.status === 'completed') {
          clearInterval(interval);
          this.pdfUrl = `/api/jobs/${jobId}/download?type=pdf`;
        }
      }, 1000);
    }
  }
}
</script>
```

---

## 🚀 Deployment

### Docker

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libreoffice \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install --with-deps chromium

# Copy application
COPY . .

# Create directories
RUN mkdir -p uploads output

EXPOSE 5000

# Run with gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", \
     "--timeout", "600", "api_server:app"]
```

### Environment Variables (Production)

```bash
GEMINI_API_KEY=prod_key_here
API_PORT=5000
MAX_FILE_SIZE_MB=50
FLASK_ENV=production
CORS_ORIGINS=https://yourdomain.com
```

---

## 📊 Comparison: Pipeline vs Direct Conversion

| Feature | This Pipeline | Direct PPT→PDF |
|---------|---------------|----------------|
| Chart Quality | ⭐⭐⭐⭐⭐ Vector (Chart.js) | ⭐⭐ Raster image |
| French Text | ⭐⭐⭐⭐⭐ AI-optimized | ⭐⭐ Direct translation |
| Layout | ⭐⭐⭐⭐⭐ AI-chosen | ⭐⭐⭐ Fixed from PPT |
| File Size | 0.68 MB | 5-10 MB |
| Processing | 60-90s | 5-10s |
| Editability | PDF only | PPT editable |
| **Best For** | **Final polished output** | **Quick previews** |

---

## 🎓 Learning Resources

### Understanding the Pipeline

1. **Chart Vision Analysis** - See `analyze_charts_vision.py`
   - How AI extracts chart data from images
   - Chart.js format conversion

2. **AI Layout Decisions** - See `translate_ai_v5.py`
   - Content density analysis
   - Layout type selection logic

3. **Template Rendering** - See `template_v4.html`
   - Jinja2 conditionals for each layout
   - Chart.js integration

4. **PDF Export** - See `export_pdf.py`
   - Playwright browser automation
   - Waiting for dynamic content

---

## 🤝 Contributing

This is a production-ready system. To extend it:

### Add New Layout Types

1. Update AI prompt in `translate_ai_v5.py`
2. Add template block in `template_v4.html`
3. Add CSS styling for new layout

### Add New Chart Types

1. Update vision prompt in `analyze_charts_vision.py`
2. Add Chart.js rendering in `template_v4.html`
3. Test with sample charts

### Improve Performance

1. Implement Redis job queue
2. Add result caching
3. Parallelize slide processing
4. Batch vision API calls

---

## 📄 License

Internal use. Modify and extend as needed.

---

## 🙏 Credits

- **AI Vision:** Google Gemini Flash & Vision
- **Charts:** Chart.js + chartjs-plugin-datalabels
- **PDF Export:** Playwright (Chromium)
- **Template Engine:** Jinja2
- **PPT Parsing:** python-pptx
- **Design Inspiration:** NotebookLLM

---

## 📞 Support

- **Issues:** Create detailed bug reports with sample files
- **Questions:** Check INTEGRATION_GUIDE.md first
- **Customization:** All prompts are in Python files (easy to modify)

---

**Built with ❤️ using AI-powered content analysis and vision capabilities**

Last Updated: 2025-12-07
Version: 1.0.0 (Production Ready)
