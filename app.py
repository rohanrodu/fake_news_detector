import gradio as gr
from newspaper import Article
from transformers import pipeline
import re

# Load summarization model
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

# Trusted sources
RELIABLE_SOURCES = [
    "bbc.com", "nytimes.com", "apnews.com", "indianexpress.com", "deccanherald.com"
]

def extract_domain(url):
    match = re.search(r"https?://(www\.)?([^/]+)", url)
    return match.group(2) if match else ""

def is_reliable_source(url):
    domain = extract_domain(url)
    return any(source in domain for source in RELIABLE_SOURCES)

def analyze_article(url):
    if not url or not re.match(r'^https?://', url):
        return "❌ Invalid URL. Please enter a valid link starting with http:// or https://", "", ""

    try:
        article = Article(url)
        article.download()
        article.parse()

        text = article.text
        if len(text) < 100:
            return "❌ Article too short or not supported.", "", ""

        summary = summarizer(text[:1024], max_length=130, min_length=30, do_sample=False)[0]['summary_text']
        credibility = "✅ Reliable Source" if is_reliable_source(url) else "⚠️ Unverified Source"

        return "", summary, credibility

    except Exception as e:
        return f"❌ Error processing article: {str(e)}", "", ""

# Gradio UI
with gr.Blocks(title="📰 News Article Analyzer") as demo:
    gr.Markdown("## 📰 News Article Analyzer")
    gr.Markdown("Analyze any online news article for a quick summary and source credibility.")

    with gr.Row():
        url_input = gr.Textbox(label="🔗 Article URL", placeholder="Enter full article URL here...", scale=4)
        analyze_btn = gr.Button("Analyze Article", scale=1)

    with gr.Row():
        error_output = gr.Markdown()

    with gr.Row():
        summary_output = gr.Textbox(label="📝 Summary", lines=6, interactive=False)
        credibility_output = gr.Textbox(label="🔍 Source Credibility", interactive=False)

    with gr.Accordion("📄 View Full Article Text (Optional)", open=False):
        full_text_output = gr.Textbox(label="Full Article Text", lines=10, interactive=False)

    def full_analysis(url):
        err, summary, credibility = analyze_article(url)
        if err:
            return err, "", "", ""
        article = Article(url)
        article.download()
        article.parse()
        return "", summary, credibility, article.text

    analyze_btn.click(fn=full_analysis, inputs=url_input,
                      outputs=[error_output, summary_output, credibility_output, full_text_output])

# Launch the app
demo.launch()
