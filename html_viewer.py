# html_viewer.py
import tempfile
import webbrowser
import json

def normalize_summary_to_markdown(summary_text: str) -> str:
    """Convert JSON or plain text summary into readable markdown."""
    try:
        data = json.loads(summary_text)
        md = []
        for section, content in data.items():
            md.append(f"## {section}")
            if isinstance(content, dict):
                for k,v in content.items():
                    md.append(f"- **{k}**: {v}")
            elif isinstance(content, list):
                for item in content:
                    md.append(f"- {item}")
            else:
                md.append(str(content))
        return "\n".join(md)
    except Exception:
        return summary_text

def _try_markdown_to_html(md_text: str) -> str:
    """
    Convert Markdown to HTML (with table support) if markdown package is available,
    otherwise wrap content in <pre>.
    """
    try:
        from markdown import markdown
        return markdown(md_text, extensions=["tables"])
    except Exception:
        # Fallback: preserve spacing in <pre>
        safe = (
            md_text.replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;")
        )
        return f"<pre>{safe}</pre>"

def show_in_browser(title: str, content: str) -> None:
    html_content = _try_markdown_to_html(content)
    html_template = f"""<!doctype html>
                        <html>
                        <head>
                        <meta charset="utf-8"/>
                        <title>{title}</title>
                        <style>
                            body {{
                                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
                                margin: 28px;
                                background: #fafafa;
                                color: #222;
                                line-height: 1.5;
                            }}
                            h1,h2 {{ margin: 0 0 16px 0; }}
                            table {{
                                border-collapse: collapse;
                                width: 100%;
                                font-size: 15px;
                                background: #fff;
                            }}
                            th, td {{
                                border: 1px solid #ddd;
                                padding: 8px 10px;
                                text-align: left;
                                vertical-align: top;
                            }}
                            th {{
                                background: #0b6bd3;
                                color: #fff;
                                position: sticky;
                                top: 0;
                                z-index: 1;
                            }}
                            tr:nth-child(even) {{ background: #f6f6f6; }}
                            code, pre {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
                        </style>
                        </head>
                        <body>
                        <h1>{title}</h1>
                        {html_content}
                        </body>
                        </html>"""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
    tmp.write(html_template.encode("utf-8"))
    tmp.close()
    webbrowser.open(f"file://{tmp.name}")
