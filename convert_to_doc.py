import markdown

with open('README.md', 'r', encoding='utf-8') as f:
    text = f.read()

html = markdown.markdown(text)

# Wrap it in a basic HTML structure so Word understands it's an HTML document
word_html = f"""<html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='http://www.w3.org/TR/REC-html40'>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: 'Calibri', 'Arial', sans-serif;
            line-height: 1.5;
            margin: 1in;
        }}
        h1 {{
            color: #2e74b5;
            font-size: 24pt;
        }}
        h2 {{
            color: #2e74b5;
            font-size: 18pt;
            border-bottom: 1px solid #ccc;
            padding-bottom: 4px;
            margin-top: 24pt;
        }}
        h3 {{
            color: #1f4d78;
            font-size: 14pt;
            margin-top: 18pt;
        }}
        code {{
            font-family: 'Courier New', monospace;
            background-color: #f4f4f4;
            padding: 2px 4px;
        }}
        pre {{
            background-color: #f4f4f4;
            padding: 10px;
            border: 1px solid #ddd;
        }}
    </style>
</head>
<body>
    {html}
</body>
</html>
"""

with open('InsAnalytics_Documentation.doc', 'w', encoding='utf-8') as f:
    f.write(word_html)

print("Created InsAnalytics_Documentation.doc successfully.")
