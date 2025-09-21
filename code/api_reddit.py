# code/api_reddit.py  (versión corta)
import os, csv
from datetime import datetime, timezone
import praw
from dotenv import load_dotenv


SUBREDDITS = ["politics", "PoliticalDiscussion", "worldnews"]
POSTS_PER_SUB = 20
COMMENTS_PER_POST = 5
LISTING = "top"  # o "hot"

load_dotenv()
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    username=os.getenv("REDDIT_USERNAME"),
    password=os.getenv("REDDIT_PASSWORD"),
    user_agent=os.getenv("REDDIT_USER_AGENT") or "webscrappingProject",
)

print("Conectado como:", reddit.user.me())

# --- 1) Posts ---
posts_rows = []
for sr in SUBREDDITS:
    for post in getattr(reddit.subreddit(sr), LISTING)(limit=POSTS_PER_SUB):
        posts_rows.append({
            "subreddit": sr,
            "post_id": post.id,
            "title": post.title,
            "score": post.score,
            "num_comments": post.num_comments,
            "url": post.url,
            "created_utc": datetime.fromtimestamp(post.created_utc, tz=timezone.utc).isoformat()
        })

os.makedirs("output", exist_ok=True)
with open("output/posts.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(posts_rows[0].keys()))
    w.writeheader(); w.writerows(posts_rows)
print("posts.csv guardado:", len(posts_rows))

# --- 2) Comentarios (subconjunto simple) ---
# Tomamos los 10 posts con mayor score por subreddit (definición simple de "más relevantes")
comments_rows = []
for sr in SUBREDDITS:
    top_posts = [p for p in posts_rows if p["subreddit"] == sr]
    top_posts.sort(key=lambda r: r["score"], reverse=True)
    for p in top_posts[:10]:
        s = reddit.submission(id=p["post_id"])
        s.comments.replace_more(limit=0)
        for c in sorted(s.comments.list(), key=lambda x: getattr(x, "score", 0), reverse=True)[:COMMENTS_PER_POST]:
            comments_rows.append({
                "post_id": p["post_id"],
                "comment_id": getattr(c, "id", ""),
                "body": getattr(c, "body", ""),
                "score": getattr(c, "score", 0)
            })

with open("output/comments.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(comments_rows[0].keys()))
    w.writeheader(); w.writerows(comments_rows)
print("comments.csv guardado:", len(comments_rows))
