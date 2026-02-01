from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

ytt_api = YouTubeTranscriptApi()


def extract_video_id(url: str) -> str | None:
    parsed = urlparse(url)

    # Standard YouTube URLs
    if parsed.hostname in ("www.youtube.com", "youtube.com", "m.youtube.com"):
        qs = parse_qs(parsed.query)

        # watch?v=VIDEO_ID
        if "v" in qs:
            return qs["v"][0]

    # Shortened URLs: youtu.be/VIDEO_ID
    if parsed.hostname == "youtu.be":
        return parsed.path.lstrip("/")

    return None


def fetch_transcript(video_id):
    try:
        fetched_transcript = ytt_api.fetch(video_id)

        # Join transcript text, skipping [Music], [Applause], etc.
        full_transcript = " ".join(
            item.text for item in fetched_transcript if not item.text.startswith("[")
        )
        return full_transcript
    except Exception:
        print("No captions available for this video.")
