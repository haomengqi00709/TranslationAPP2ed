# Integration Guide: Adding PDF Export to Your Existing PPT Translator

## Overview

You now have **two translation modes**:

1. **PPT → PPT Translation** (Your existing system)
2. **PPT → PDF Translation** (New AI-powered system with chart recreation) ✨

This guide shows you how to integrate them into your existing frontend.

---

## Architecture

```
Your Existing Frontend
    │
    ├── [Existing] Direct Translation Button
    │   └── PPT → PPT (Your current API)
    │
    └── [NEW] AI PDF Translation Button  ⭐
        └── PPT → PDF (New pipeline API)
            ├── Extract content
            ├── AI vision for charts
            ├── Translate to French
            ├── Render HTML with Chart.js
            └── Export to PDF
```

---

## Integration Steps

### Step 1: Install Backend Dependencies

```bash
cd /path/to/Layout_solution

# Install Flask API dependencies
pip3 install flask flask-cors

# Verify all dependencies are installed
pip3 install python-pptx Pillow pdf2image google-generativeai jinja2 playwright python-dotenv
playwright install chromium
```

### Step 2: Start the API Server

```bash
# Terminal 1: Start the PDF translation API server
python3 api_server.py

# Server will run on http://localhost:5000
```

**Server Endpoints:**
- `POST /api/translate/pdf` - Start translation (upload PPT)
- `GET /api/jobs/<job_id>/status` - Check progress
- `GET /api/jobs/<job_id>/download?type=pdf` - Download PDF
- `GET /api/jobs/<job_id>/download?type=html` - Download HTML

### Step 3: Test the Standalone Frontend

```bash
# Open the example frontend to test
open frontend_example.html

# Or serve it:
python3 -m http.server 8080
# Then visit: http://localhost:8080/frontend_example.html
```

### Step 4: Integrate Into Your Existing Frontend

#### Option A: Add as Separate Button (Recommended)

Add this to your existing upload page:

```html
<!-- Your existing translation button -->
<button onclick="translatePPTtoPPT()">
    Direct Translation (PPT → PPT)
</button>

<!-- NEW: AI PDF translation button -->
<button onclick="translatePPTtoPDF()" class="ai-feature">
    🎨 AI Translation to PDF (Beta)
</button>
```

#### Option B: Add as Tab/Mode Selector

```html
<div class="translation-modes">
    <button class="mode" data-mode="ppt">PPT to PPT</button>
    <button class="mode active" data-mode="pdf">AI PDF (Beta)</button>
</div>
```

---

## Frontend Integration Code

### JavaScript API Client

Add this to your existing JavaScript:

```javascript
class PDFTranslationAPI {
    constructor(baseURL = 'http://localhost:5000/api') {
        this.baseURL = baseURL;
    }

    async startTranslation(file) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${this.baseURL}/translate/pdf`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Upload failed');
        }

        return await response.json(); // Returns { job_id, status, message }
    }

    async getJobStatus(jobId) {
        const response = await fetch(`${this.baseURL}/jobs/${jobId}/status`);
        return await response.json();
    }

    getDownloadURL(jobId, type = 'pdf') {
        return `${this.baseURL}/jobs/${jobId}/download?type=${type}`;
    }

    async pollUntilComplete(jobId, onProgress) {
        while (true) {
            const job = await this.getJobStatus(jobId);

            if (onProgress) {
                onProgress(job.progress);
            }

            if (job.status === 'completed') {
                return job.result;
            }

            if (job.status === 'failed') {
                throw new Error(job.result.error || 'Translation failed');
            }

            await new Promise(resolve => setTimeout(resolve, 1000));
        }
    }
}

// Usage
const pdfAPI = new PDFTranslationAPI();

async function translatePPTtoPDF(file) {
    try {
        // Start translation
        const { job_id } = await pdfAPI.startTranslation(file);

        // Poll for progress
        const result = await pdfAPI.pollUntilComplete(job_id, (progress) => {
            updateProgressUI(progress);
        });

        if (result.success) {
            // Show success and download link
            const downloadURL = pdfAPI.getDownloadURL(job_id, 'pdf');
            showSuccess(downloadURL, result.stats);
        }
    } catch (error) {
        showError(error.message);
    }
}
```

---

## UI Component Examples

### Progress Indicator

```javascript
function updateProgressUI(progress) {
    const { current_stage, total_stages, progress_percent, message } = progress;

    // Update progress bar
    progressBar.style.width = `${progress_percent}%`;
    progressText.textContent = message;

    // Stage names
    const stages = ['Extract', 'Images', 'AI + Vision', 'Render', 'PDF'];

    // Update stage indicators
    stages.forEach((name, index) => {
        const stageEl = document.getElementById(`stage-${index + 1}`);
        if (index + 1 < current_stage) {
            stageEl.className = 'complete';
        } else if (index + 1 === current_stage) {
            stageEl.className = 'active';
        } else {
            stageEl.className = 'pending';
        }
    });
}
```

### Success Display

```javascript
function showSuccess(downloadURL, stats) {
    successContainer.innerHTML = `
        <h3>✅ Translation Complete!</h3>
        <div class="stats">
            <div>Source Slides: ${stats.source_slides}</div>
            <div>Output Slides: ${stats.output_slides}</div>
            <div>Charts Recreated: ${stats.chart_slides}</div>
            <div>PDF Size: ${stats.pdf_size_mb} MB</div>
        </div>
        <a href="${downloadURL}" class="download-btn">
            📥 Download PDF
        </a>
    `;
}
```

---

## Comparison: PPT vs PDF Translation

| Feature | PPT → PPT (Existing) | PPT → PDF (New) |
|---------|---------------------|-----------------|
| **Speed** | ⚡ Fast (~10s) | 🐢 Slower (~60s for 20 slides) |
| **Output Format** | .pptx | .pdf + .html |
| **Chart Handling** | Images (static) | Chart.js (recreated) |
| **Layout** | Preserves original | AI-optimized layouts |
| **Text Overflow** | May occur | AI prevents overflow |
| **Editability** | ✅ Editable PPT | ❌ Final PDF only |
| **Use Case** | Quick translation | Polished final output |

---

## Deployment Considerations

### Development (Current Setup)

```bash
# Backend API
python3 api_server.py

# Frontend (your existing app)
npm run dev  # or your current setup
```

### Production

#### Option 1: Docker (Recommended)

```dockerfile
FROM python:3.11

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libreoffice \
    poppler-utils

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install --with-deps chromium

# Copy application
COPY . .

# Expose port
EXPOSE 5000

# Run with gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "--timeout", "600", "api_server:app"]
```

#### Option 2: Cloud Functions

Deploy each stage as separate cloud functions:
- `ppt-extract`: Extract stage
- `ppt-translate`: AI translation
- `ppt-render`: HTML rendering
- `ppt-export`: PDF export

Use queue (Redis/RabbitMQ) for async processing.

---

## Configuration Options

### Environment Variables

Create `.env` file:

```bash
# Required
GEMINI_API_KEY=your_api_key_here

# Optional
API_PORT=5000
MAX_FILE_SIZE_MB=50
UPLOAD_FOLDER=uploads
OUTPUT_FOLDER=output
ENABLE_CORS=true
```

### Customization

**Change primary color:**

```python
# In api_wrapper.py
result = render_html_v5(
    slides_data=flattened_slides,
    output_path=str(html_output),
    primary_color="#YOUR_COLOR_HERE"  # Customize
)
```

**Adjust API timeouts:**

```python
# In api_server.py
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
```

---

## Error Handling

### Common Errors and Solutions

**1. API quota exceeded**
```json
{
    "error": "429 You exceeded your current quota..."
}
```
**Solution:** Wait for quota reset or upgrade Gemini API tier

**2. Chart rendering failed**
```json
{
    "error": "Chart.js not loaded"
}
```
**Solution:** Already fixed with Chart.js plugin registration in template

**3. File upload too large**
```json
{
    "error": "File too large"
}
```
**Solution:** Increase `MAX_CONTENT_LENGTH` in Flask config

**4. Browser timeout**
```json
{
    "error": "Target page closed"
}
```
**Solution:** Already fixed with `--single-process` flag in export_pdf.py

---

## Testing

### Test the API Directly

```bash
# Test upload
curl -X POST http://localhost:5000/api/translate/pdf \
  -F "file=@test.pptx"

# Response: {"job_id": "...", "status": "processing"}

# Check status
curl http://localhost:5000/api/jobs/<job_id>/status

# Download PDF
curl -o output.pdf "http://localhost:5000/api/jobs/<job_id>/download?type=pdf"
```

### Test with Frontend Example

```bash
# Serve the example frontend
python3 -m http.server 8080

# Visit http://localhost:8080/frontend_example.html
# Upload a test PowerPoint and verify:
# - Progress updates in real-time
# - All 5 stages complete
# - PDF downloads successfully
# - Charts are rendered (not images)
```

---

## Performance Optimization

### For Production

1. **Use Job Queue** (Celery + Redis)
   - Prevents blocking API requests
   - Allows horizontal scaling

2. **Cache Results**
   - Cache translated content for 24 hours
   - Reuse if same file uploaded

3. **Parallel Processing**
   - Process multiple slides concurrently
   - Batch vision API calls

4. **CDN for Static Assets**
   - Chart.js library from CDN
   - Faster loading

---

## Monitoring

### Key Metrics to Track

```javascript
// In your analytics
trackEvent('pdf_translation_started', {
    file_size: file.size,
    filename: file.name
});

trackEvent('pdf_translation_completed', {
    job_id: jobId,
    duration_seconds: duration,
    source_slides: stats.source_slides,
    chart_slides: stats.chart_slides
});

trackEvent('pdf_downloaded', {
    job_id: jobId,
    file_type: 'pdf'
});
```

### Logs to Monitor

- Translation errors (API failures)
- Chart vision failures (fallback to image)
- PDF export failures
- Average processing time per slide

---

## Migration Path

### Phase 1: Beta Launch (Current)
- Add "AI PDF Translation (Beta)" button
- Show disclaimer: "Processing takes 1-2 minutes"
- Collect user feedback

### Phase 2: Optimization
- Implement job queue for async processing
- Add email notification when complete
- Cache frequently translated files

### Phase 3: Full Integration
- Make PDF the default for final reports
- Keep PPT-to-PPT for quick iterations
- Add "Export Options" dropdown

---

## Support & Troubleshooting

### FAQ

**Q: Can users cancel in-progress translations?**
A: Not yet - add DELETE endpoint for job cancellation

**Q: What happens if the server restarts?**
A: In-progress jobs are lost (use persistent queue in production)

**Q: Can I process multiple files simultaneously?**
A: Yes - each job runs in separate thread

**Q: How long are results stored?**
A: Currently indefinitely - add cleanup cron job

---

## Next Steps

1. ✅ Test the API server: `python3 api_server.py`
2. ✅ Test the frontend example: `open frontend_example.html`
3. 🔨 Integrate into your existing frontend
4. 🎨 Customize UI to match your design system
5. 🚀 Deploy to production

---

## Code Reference

**Key Files:**
- `api_wrapper.py` - Single-function pipeline wrapper
- `api_server.py` - Flask REST API
- `frontend_example.html` - Complete UI example
- `INTEGRATION_GUIDE.md` - This file

**Integration Pattern:**

```
Your Frontend
    ↓
[Call] api_server.py (Flask API)
    ↓
[Execute] api_wrapper.py (Pipeline wrapper)
    ↓
[Run] translate_ai_v5.py → render_html_v5.py → export_pdf.py
    ↓
[Return] PDF file to user
```

---

Need help integrating? Check the example code in `frontend_example.html` - it's a complete working implementation you can copy from!
