import os

import praw
from dotenv import load_dotenv

load_dotenv()

reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT"),
)

print(f"Authenticated as: {reddit.user.me()}")

for post in reddit.subreddit("all").search("Gemma 4", limit=5):
    print("=" * 80)
    print(post.title)
    print(post.url)
    print(post.score)