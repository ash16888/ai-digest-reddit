import json
import re
from datetime import datetime

import bleach
import markdown
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request

from .s3_storage import s3_storage


app = FastAPI(title="Reddit AI Digest")

# Mount static files
app.mount("/static", StaticFiles(directory="src/static"), name="static")

# Templates configuration for Lambda
templates = Jinja2Templates(directory="src/templates")


# Add custom filters
def format_number(value):
    """Format number with thousands separators."""
    try:
        return f"{int(value):,}".replace(",", " ")
    except (ValueError, TypeError):
        return str(value)


templates.env.filters["number_format"] = format_number



def get_stats() -> dict[str, int]:
    """Get overall statistics for the site."""
    total_digests = 0
    total_posts = 0
    subreddits = set()

    # Get configured subreddits from environment or default
    import os

    from dotenv import load_dotenv

    load_dotenv()

    configured_subreddits = os.getenv(
        "REDDIT_SUBREDDITS", "ChatGPT,OpenAI,ClaudeAI,Bard,GeminiAI,DeepSeek,grok"
    )
    configured_list = [
        sub.strip().strip('"')
        for sub in configured_subreddits.split(",")
        if sub.strip()
    ]

    # Count digests from S3
    s3_digest_files = s3_storage.list_files("reports/digest_")
    total_digests = len([f for f in s3_digest_files if f.endswith('.md')])

    # Count posts from S3 data files
    s3_data_files = s3_storage.list_files("data/posts_")
    for file_key in s3_data_files:
        if file_key.endswith('.json'):
            try:
                data = s3_storage.download_json(file_key)
                if data:
                    # Add total posts count
                    if "total_posts_collected" in data:
                        total_posts += data["total_posts_collected"]
                    elif "total_posts" in data:
                        total_posts += data["total_posts"]
                    elif "posts" in data:
                        total_posts += len(data["posts"])

                    # Extract unique subreddits (only configured ones)
                    if "posts" in data:
                        for post in data["posts"]:
                            if "subreddit" in post and post["subreddit"] in configured_list:
                                subreddits.add(post["subreddit"])
            except Exception:
                continue

    return {
        "total_digests": total_digests,
        "total_subreddits": len(
            configured_list
        ),  # Use configured count, not found count
        "total_posts": total_posts,
    }


def get_digest_list() -> list[dict[str, str]]:
    """Get list of all digests sorted by date (newest first)."""
    digests = []
    
    # Get digest list from S3
    s3_files = s3_storage.list_files("reports/digest_")
    
    for file_key in s3_files:
        if file_key.endswith('.md'):
            try:
                # Extract date from filename
                filename = file_key.split('/')[-1]
                date_str = filename.replace("digest_", "").replace(".md", "")
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                
                # Format Russian month names
                months = {
                    1: "января", 2: "февраля", 3: "марта", 4: "апреля",
                    5: "мая", 6: "июня", 7: "июля", 8: "августа",
                    9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
                }
                
                formatted_date = f"{date_obj.day} {months[date_obj.month]} {date_obj.year}"
                
                digests.append({
                    "date": date_str,
                    "title": f"Дайджест Reddit • {date_obj.strftime('%d-%m-%Y')}",
                    "formatted_date": formatted_date,
                    "file_name": filename,
                })
            except Exception as e:
                print(f"Error processing S3 file {file_key}: {e}")
                continue

    # Sort by date (newest first)
    digests.sort(key=lambda x: x["date"], reverse=True)
    return digests


def get_digest_stats(date: str) -> dict:
    """Get statistics for a specific digest date."""
    # Get data from S3
    data = s3_storage.download_json(f"data/posts_{date}.json")

    if data is None:
        return {}

    try:
        # Count posts by subreddit
        subreddit_counts = {}
        configured_subreddits = [
            "ChatGPT",
            "OpenAI",
            "ClaudeAI",
            "Bard",
            "GeminiAI",
            "DeepSeek",
            "grok",
        ]

        if "posts" in data:
            for post in data["posts"]:
                subreddit = post.get("subreddit", "unknown")
                if subreddit in configured_subreddits:
                    subreddit_counts[subreddit] = subreddit_counts.get(subreddit, 0) + 1

        return {
            "total_posts": data.get("total_posts_collected", data.get("total_posts", 0)),
            "filtered_posts": data.get("total_posts_filtered", data.get("filtered_posts", 0)),
            "subreddit_counts": subreddit_counts,
            "date": date,
        }
    except Exception:
        return {}


def read_digest(date: str) -> str:
    """Read digest content by date."""
    # Get content from S3
    content = s3_storage.download_markdown(f"reports/digest_{date}.md")

    if content is None:
        raise HTTPException(status_code=404, detail="Digest not found")

    # Convert markdown to HTML
    md = markdown.Markdown(
        extensions=["extra", "codehilite", "nl2br", "sane_lists", "attr_list"]
    )
    html_content = md.convert(content)

    # Add target="_blank" to all links
    html_content = re.sub(
        r'<a href="([^"]+)"([^>]*)>',
        r'<a href="\1" target="_blank" rel="noopener noreferrer"\2>',
        html_content,
    )

    # Sanitize HTML to prevent XSS attacks
    allowed_tags = [
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "p",
        "br",
        "hr",
        "b",
        "strong",
        "i",
        "em",
        "u",
        "s",
        "del",
        "ins",
        "a",
        "ul",
        "ol",
        "li",
        "blockquote",
        "code",
        "pre",
        "table",
        "thead",
        "tbody",
        "tr",
        "th",
        "td",
        "div",
        "span",
    ]
    allowed_attrs = {
        "*": ["class"],
        "a": ["href", "target", "rel", "title"],
        "code": ["class"],
        "div": ["class"],
        "span": ["class"],
    }

    clean_html = bleach.clean(
        html_content, tags=allowed_tags, attributes=allowed_attrs, strip=True
    )

    return clean_html


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main page with latest 4 digests."""
    all_digests = get_digest_list()
    # Show only latest 4 digests on main page
    recent_digests = all_digests[:4]
    stats = get_stats()

    # Format current date
    current_date = (
        datetime.now()
        .strftime("%A, %d %B %Y г.")
        .replace("Monday", "понедельник")
        .replace("Tuesday", "вторник")
        .replace("Wednesday", "среда")
        .replace("Thursday", "четверг")
        .replace("Friday", "пятница")
        .replace("Saturday", "суббота")
        .replace("Sunday", "воскресенье")
        .replace("January", "января")
        .replace("February", "февраля")
        .replace("March", "марта")
        .replace("April", "апреля")
        .replace("May", "мая")
        .replace("June", "июня")
        .replace("July", "июля")
        .replace("August", "августа")
        .replace("September", "сентября")
        .replace("October", "октября")
        .replace("November", "ноября")
        .replace("December", "декабря")
    )

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "digests": recent_digests,
            "total_count": len(all_digests),
            "recent_count": len(recent_digests),
            "has_more": len(all_digests) > 4,
            "stats": stats,
            "current_date": current_date,
        },
    )


@app.get("/digest/{date}", response_class=HTMLResponse)
async def show_digest(request: Request, date: str):
    """Show specific digest by date."""
    try:
        content = read_digest(date)
        digest_date = datetime.strptime(date, "%Y-%m-%d")

        # Get digest statistics
        digest_stats = get_digest_stats(date)

        # Get navigation info
        digests = get_digest_list()
        current_index = next(
            (i for i, d in enumerate(digests) if d["date"] == date), -1
        )

        prev_digest = (
            digests[current_index + 1] if current_index < len(digests) - 1 else None
        )
        next_digest = digests[current_index - 1] if current_index > 0 else None

        return templates.TemplateResponse(
            "digest.html",
            {
                "request": request,
                "content": content,
                "date": date,
                "formatted_date": digest_date.strftime("%d %B %Y"),
                "prev_digest": prev_digest,
                "next_digest": next_digest,
                "digest_stats": digest_stats,
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/digests")
async def api_digest_list():
    """API endpoint to get list of all digests."""
    return {"digests": get_digest_list()}


@app.get("/api/digest/{date}")
async def api_get_digest(date: str):
    """API endpoint to get specific digest content."""
    # Get content from S3
    content = s3_storage.download_markdown(f"reports/digest_{date}.md")

    if content is None:
        raise HTTPException(status_code=404, detail="Digest not found")

    return {"date": date, "content": content, "html": read_digest(date)}


@app.get("/archive", response_class=HTMLResponse)
async def archive_page(request: Request):
    """Archive page with all digests."""
    digests = get_digest_list()

    # Format current date
    current_date = (
        datetime.now()
        .strftime("%A, %d %B %Y г.")
        .replace("Monday", "понедельник")
        .replace("Tuesday", "вторник")
        .replace("Wednesday", "среда")
        .replace("Thursday", "четверг")
        .replace("Friday", "пятница")
        .replace("Saturday", "суббота")
        .replace("Sunday", "воскресенье")
        .replace("January", "января")
        .replace("February", "февраля")
        .replace("March", "марта")
        .replace("April", "апреля")
        .replace("May", "мая")
        .replace("June", "июня")
        .replace("July", "июля")
        .replace("August", "августа")
        .replace("September", "сентября")
        .replace("October", "октября")
        .replace("November", "ноября")
        .replace("December", "декабря")
    )

    # Get oldest and newest dates for description
    oldest_date = digests[-1]["formatted_date"] if digests else "сегодня"
    newest_date = digests[0]["formatted_date"] if digests else "сегодня"

    return templates.TemplateResponse(
        "archive.html",
        {
            "request": request,
            "digests": digests,
            "total_count": len(digests),
            "current_date": current_date,
            "oldest_date": oldest_date,
            "newest_date": newest_date,
        },
    )


@app.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    """About page with project information."""
    # Format current date
    current_date = (
        datetime.now()
        .strftime("%A, %d %B %Y г.")
        .replace("Monday", "понедельник")
        .replace("Tuesday", "вторник")
        .replace("Wednesday", "среда")
        .replace("Thursday", "четверг")
        .replace("Friday", "пятница")
        .replace("Saturday", "суббота")
        .replace("Sunday", "воскресенье")
        .replace("January", "января")
        .replace("February", "февраля")
        .replace("March", "марта")
        .replace("April", "апреля")
        .replace("May", "мая")
        .replace("June", "июня")
        .replace("July", "июля")
        .replace("August", "августа")
        .replace("September", "сентября")
        .replace("October", "октября")
        .replace("November", "ноября")
        .replace("December", "декабря")
    )

    # Get stats for about page
    stats = get_stats()

    return templates.TemplateResponse(
        "about.html",
        {"request": request, "current_date": current_date, "stats": stats},
    )


