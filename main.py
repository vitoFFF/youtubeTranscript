from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, FileResponse
from youtube_transcript_api import YouTubeTranscriptApi
import re
import os

app = FastAPI()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>YouTube Transcript Downloader</title>
    <style>
        body {{
            background-color: #121212;
            color: #e0e0e0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            padding: 2rem;
            text-align: center;
        }}
        input {{
            padding: 10px;
            width: 300px;
            border-radius: 8px;
            border: none;
            margin-bottom: 10px;
        }}
        button {{
            padding: 10px 20px;
            border: none;
            background: #1db954;
            color: white;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
        }}
        button:hover {{
            background: #1ed760;
        }}
        .transcript-box {{
            text-align: left;
            background: #1e1e1e;
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
            white-space: pre-wrap;
            max-width: 800px;
            margin-left: auto;
            margin-right: auto;
            position: relative;
        }}
        .download-btn {{
            display: inline-block;
            margin: 10px auto 20px;
            background: #2196F3;
            color: white;
            padding: 10px 20px;
            border-radius: 8px;
            text-decoration: none;
        }}
        .download-btn:hover {{
            background: #42A5F5;
        }}
        .copy-btn {{
            position: absolute;
            top: 20px;
            right: 20px;
            background: #333;
            color: #fff;
            border: none;
            padding: 6px 12px;
            border-radius: 6px;
            cursor: pointer;
        }}
        .copy-btn:hover {{
            background: #444;
        }}
    </style>
</head>
<body>
    <h1>YouTube Transcript Downloader</h1>
    <form method="post">
        <input name="url" type="text" placeholder="Paste YouTube URL..." required />
        <br>
        <button type="submit">Fetch Transcript</button>
    </form>
    {error_html}
    {transcript_html}
    <script>
        function copyTranscript() {{
            const text = document.getElementById("transcriptText").innerText;
            navigator.clipboard.writeText(text).then(() => {{
                alert("Transcript copied to clipboard!");
            }});
        }}
    </script>
</body>
</html>
"""

def extract_video_id(url):
    match = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url)
    return match.group(1) if match else None

@app.get("/", response_class=HTMLResponse)
async def get_form():
    return HTML_TEMPLATE.format(error_html="", transcript_html="")

@app.post("/", response_class=HTMLResponse)
async def handle_form(url: str = Form(...)):
    video_id = extract_video_id(url)
    if not video_id:
        return HTML_TEMPLATE.format(error_html="<p style='color:red;'>Invalid YouTube URL</p>", transcript_html="")

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        filename = f"{video_id}_transcript.txt"

        # Save to file
        with open(filename, "w", encoding="utf-8") as f:
            for entry in transcript:
                f.write(f"{entry['start']:.2f}s: {entry['text']}\n")

        # Create HTML version
        transcript_text = "\n".join(f"{entry['start']:.2f}s: {entry['text']}" for entry in transcript)
        transcript_html = f"""
            <a class="download-btn" href="/download/{filename}" download>Download Transcript (.txt)</a>
            <div class="transcript-box">
                <button class="copy-btn" onclick="copyTranscript()">Copy</button>
                <div id="transcriptText">{transcript_text}</div>
            </div>
        """
        return HTML_TEMPLATE.format(error_html="", transcript_html=transcript_html)

    except Exception as e:
        return HTML_TEMPLATE.format(error_html=f"<p style='color:red;'>{str(e)}</p>", transcript_html="")

@app.get("/download/{filename}", response_class=FileResponse)
async def download_file(filename: str):
    filepath = os.path.join(os.getcwd(), filename)
    return FileResponse(filepath, media_type='text/plain', filename=filename)
