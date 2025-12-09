
Model
ThinkingThoughts
Expand to view model thoughts

chevron_right
这份蓝图是基于我们之前所有讨论的最终定稿版。它摒弃了复杂的 PPT 还原路径，采用 “AI 重构 + Web 渲染” 的降维打击策略。
这是你的 24小时行动指南。
🚀 项目代号：AI Smart Briefing (AI 智能简报引擎)
1. 核心产品定义 (The Concept)
不是什么： 这不是一个简单的“PPT 翻译工具”。
是什么： 这是一个 “智能文档重构引擎”。它模仿 NotebookLLM 的逻辑，阅读你的 PPT，理解内容结构，然后自动生成一份排版完美、图文对照、杂志风格的 PDF 简报。
核心卖点 (The Wow Factor)： Layout Awareness (布局感知)。AI 能根据内容自动切换排版（文字页 vs 数据页 vs 金句页）。
2. 技术架构 (The Stack)
语言： Python 3.9+
输入解析： python-pptx (提取文字)
AI 大脑： OpenAI GPT-4o / Gemini 1.5 Pro (处理语义与排版决策)
渲染引擎： HTML5 + CSS3 (利用 Flexbox/Grid 实现完美排版) + Jinja2 (可选，或直接用 f-string 拼接)
最终输出： 浏览器打印 -> PDF
3. 详细执行四步走 (The Execution Plan)
🟢 第一步：数据收割 (Data Harvesting) - 预计 1 小时
目标： 将 PPT 拆解为“素材”。
图像流 (Visuals):
为了 Demo 稳定，手动将 PPT 的每一页“另存为图片”（slide1.jpg, slide2.jpg...）。
建立一个 assets 文件夹存放这些图片。
逻辑： 这是为了在最终简报的左侧展示“原件”，建立信任感 (Grounding)。
文本流 (Text):
写一个极简的 Python 脚本，遍历 pptx 的每一页。
将该页内所有文本框的内容合并成一段长文本。
输出结构： 一个简单的 List，包含 slide_index 和 raw_text。
🔵 第二步：AI 炼金 (Intelligence Layer) - 预计 2 小时
目标： 让 AI 不仅翻译，还要做“排版导演”。
Prompt 设计 (核心)：
你不需要 AI 返回 Markdown，你需要它返回 JSON。
关键指令： “你是一个专业的排版编辑。请阅读内容，并决定使用哪种模版来展示。”
定义三种模版类型 (Layout Types)：
"standard": 适合普通图文介绍（默认）。
"data": 适合包含关键财务数字、增长率的内容。
"quote": 适合愿景、使命或只有一句话的页面。
数据清洗：
运行脚本，批量调用 LLM。
保存结果为 processed_slides.json。
🟡 第三步：网页组装工厂 (The Factory) - 预计 3 小时
目标： 把 AI 的决策变成可视化的 HTML。
这里采用 “三层组装法”：
Layer 1: 外壳 (The Shell)
编写 base.html 或 Python 里的 html_head 字符串。
CSS 重点： 引入 Google Fonts (如 Inter/Roboto)，定义 A4 纸张大小，定义阴影和主色调（提取自原 PPT）。
Layer 2: 组件库 (The Components)
在 Python 中写三个函数，分别对应三种 HTML 结构：
render_standard(img, title, points) -> 生成左图右文的 HTML。
render_data(img, title, data_list) -> 生成大数字卡片的 HTML。
render_quote(img, quote) -> 生成居中大字海报的 HTML。
Layer 3: 调度器 (The Assembler)
编写主循环逻辑：
code
Text
遍历 JSON 数据:
    如果 layout_type 是 'data' -> 调用 render_data()
    如果 layout_type 是 'quote' -> 调用 render_quote()
    否则 -> 调用 render_standard()
将生成的片段拼接到一起，写入 output.html
🔴 第四步：交付与展示 (Delivery) - 预计 30 分钟
目标： 生成最终成品。
渲染： 双击打开 output.html。
检查： 确保图片路径正确，CSS 样式加载正常。
导出： 使用 Chrome 浏览器的“打印 -> 另存为 PDF”。
设置： 勾选“背景图形”，边距设为“无”。
4. 关键 Prompt 蓝图 (直接可用)
为了确保 AI 能够配合你的代码，请使用这个 Prompt 结构：
Role: You are an expert Executive Briefing Editor.
Task: Read the provided slide text (Chinese) and restructure it into a clean, concise English summary suitable for a magazine-style report.
Constraint 1 (Layout Classification):
Analyze the content and classify it into ONE of these layout types:
data: If the text contains key financial figures, percentages, or KPIs.
quote: If the text is a vision statement, mission, or a single impactful sentence.
standard: For everything else (general descriptions, bullet points).
Constraint 2 (Output Format):
Return ONLY a JSON object with these fields:
layout_type: "standard" | "data" | "quote"
english_title: A punchy headline (max 8 words).
summary: A one-sentence executive summary (max 20 words).
content:
If data: An array of objects [{"label": "Revenue", "value": "+20%"}, ...]
If quote: A single string.
If standard: An array of strings (bullet points, max 4 items).
Input Text: [插入你的 PPT 文本]

# --- 组件 A: 标准版 (图文列表) ---
def render_standard_slide(img_path, title, summary, points):
    # 把 points 列表转换成 <li> 字符串
    li_html = "".join([f"<li>{p}</li>" for p in points])
    
    return f"""
    <div class="a4-page layout-standard">
        <div class="content-header"><span class="tag">Standard View</span></div>
        <div class="split-layout">
            <div class="left-col"><img src="{img_path}" class="original-preview"></div>
            <div class="right-col">
                <h2>{title}</h2>
                <div class="summary-box">{summary}</div>
                <ul>{li_html}</ul>
            </div>
        </div>
    </div>
    """

# --- 组件 B: 数据版 (大数字卡片) ---
def render_data_slide(img_path, title, data_points):
    # data_points 结构: [{"val": "25%", "label": "Growth"}, ...]
    cards_html = ""
    for item in data_points:
        cards_html += f"""
        <div class="data-card">
            <span class="data-number">{item['val']}</span>
            <span class="data-label">{item['label']}</span>
        </div>
        """
    
    return f"""
    <div class="a4-page layout-data">
        <div class="content-header"><span class="tag" style="background:#8B5CF6">Data Insight</span></div>
        <div class="split-layout">
            <div class="left-col"><img src="{img_path}" class="original-preview"></div>
            <div class="right-col">
                <h2>{title}</h2>
                <div class="data-grid"> <!-- 注意这里用了 Grid -->
                    {cards_html}
                </div>
            </div>
        </div>
    </div>
    """

# --- 组件 C: 金句版 (海报风格) ---
def render_quote_slide(img_path, quote_text):
    return f"""
    <div class="a4-page layout-quote">
        <div class="content-header"><span class="tag" style="background:#EC4899">Vision</span></div>
        <div class="quote-container">
            <div class="quote-text">{quote_text}</div>
            <div class="mini-preview"><img src="{img_path}"></div>
        </div>
    </div>
    """

    html_head = """
<!DOCTYPE html>
<html>
<head>
    <style>
        /* 这里放之前给你的那一大段 CSS，包含 .layout-data, .layout-quote 等所有样式 */
        /* 只要把所有样式都放在这里，下面的组件就能自动生效 */
        body { font-family: sans-serif; background: #eee; }
        .a4-page { background: white; margin: 20px auto; padding: 40px; width: 210mm; min-height: 297mm; box-sizing: border-box;}
        /* ... 其他 CSS ... */
    </style>
</head>
<body>
"""

html_footer = "</body></html>"

# 假设这是你从 AI 那里拿到的结构化数据
# 注意：每一页都有一个 'type' 字段，这是 AI 判断出来的
slides_data_from_ai = [
    {
        "type": "standard",
        "img": "slide1.jpg",
        "title": "公司简介",
        "summary": "成立于2020年，致力于AI变革。",
        "points": ["全球分布", "技术领先", "客户众多"]
    },
    {
        "type": "data",
        "img": "slide2.jpg",
        "title": "2023 财务表现",
        "data": [
            {"val": "+50%", "label": "年收入增长"},
            {"val": "10M", "label": "活跃用户"}
        ]
    },
    {
        "type": "quote",
        "img": "slide3.jpg",
        "quote": "我们的征途是星辰大海。"
    }
]

# === 开始组装 ===
final_html_body = ""

for slide in slides_data_from_ai:
    if slide['type'] == 'standard':
        # 调用标准模版
        final_html_body += render_standard_slide(
            slide['img'], slide['title'], slide['summary'], slide['points']
        )
        
    elif slide['type'] == 'data':
        # 调用数据模版
        final_html_body += render_data_slide(
            slide['img'], slide['title'], slide['data']
        )
        
    elif slide['type'] == 'quote':
        # 调用金句模版
        final_html_body += render_quote_slide(
            slide['img'], slide['quote']
        )

# === 生成最终文件 ===
full_html = html_head + final_html_body + html_footer

with open("smart_briefing.html", "w", encoding="utf-8") as f:
    f.write(full_html)