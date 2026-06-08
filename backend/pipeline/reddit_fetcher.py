import praw
import openai
import datetime
from models import RedditBatchResponse

client = openai.OpenAI()

# Base fallback filter to protect against API bill overflows during development
BASE_VOCAB_FILTER = ["fastapi", "python", "nextjs", "next.js", "react", "pytorch", "torch", "docker", "k8s", "kubernetes", "rust", "go", "bun", "supabase"]

def fetch_and_stage_reddit():
    print("[Reddit Pipeline] Scanning forums for developer activity tracks...")
    
    # STRATEGY A: Dynamic Hot-Reload Loading
    local_filter = set(BASE_VOCAB_FILTER)
    try:
        with open("vocabulary_cache.txt", "r") as cache_file:
            cached_words = cache_file.read().splitlines()
            for word in cached_words:
                if word.strip():
                    local_filter.add(word.strip().lower())
        print(f"🔍 [Strategy A] Filter running with {len(local_filter)} total dynamic tokens.")
    except FileNotFoundError:
        print("ℹ️ No vocabulary cache file found yet. Defaulting to base filter list.")

    reddit = praw.Reddit(client_id=None, client_secret=None, user_agent="TrendIntelPlatform:v1.0")
    staged_posts = []
    
    try:
        subreddit = reddit.subreddit("Python+webdev+programming")
        for submission in subreddit.hot(limit=30):
            title_lower = submission.title.lower()
            
            # Match titles against the dynamic hot-reloaded filter!
            if any(keyword in title_lower for keyword in local_filter):
                utc_timestamp = datetime.datetime.fromtimestamp(submission.created_utc, tz=datetime.timezone.utc).isoformat()
                
                staged_posts.append({
                    "title": submission.title,
                    "score": submission.score,
                    "created_utc": utc_timestamp
                })
    except Exception:
        # High-fidelity sandbox fallback simulating real structural logs
        print("⚠️ Reddit API unauthenticated or offline. Falling back to development sandbox matrix...")
        utc_now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        staged_posts = [
            {"title": "Why FastAPI is absolutely dominating my production workloads", "score": 120, "created_utc": utc_now},
            {"title": "Is it worth switching from express to next.js for modern web apps?", "score": 45, "created_utc": utc_now},
            {"title": "Avoid using Bun for production databases right now, it kept corrupting our logs", "score": 340, "created_utc": utc_now}
        ]

    reddit_analytics = {}
    if not staged_posts:
        return reddit_analytics

    # Construct a payload for the batch call
    just_titles = [post["title"] for post in staged_posts]

    try:
        # Batch Transaction processing
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a developer sentiment analytics engineer processing social listening data."},
                {"role": "user", "content": f"Analyze these forum topics: {just_titles}"}
            ],
            response_format=RedditBatchResponse,
        )
        
        parsed_batch = completion.choices[0].message.parsed
        
        # Loop through matched items and aggregate using structural indices
        for i, entity in enumerate(parsed_batch.mentions):
            if entity.is_valid_dev_tool and i < len(staged_posts):
                tech_id = entity.tech_id
                original_post = staged_posts[i]
                
                if tech_id not in reddit_analytics:
                    reddit_analytics[tech_id] = {
                        "mentions_count": 0,
                        "cumulative_sentiment": 0,
                        "engagement_score": 0,
                        "latest_activity_utc": original_post["created_utc"]
                    }
                
                # Aggregate fields over multiple text captures
                reddit_analytics[tech_id]["mentions_count"] += 1
                reddit_analytics[tech_id]["cumulative_sentiment"] += entity.sentiment_score
                reddit_analytics[tech_id]["engagement_score"] += original_post["score"]
                
                # Keep track of the most recent activity timestamp safely
                if original_post["created_utc"] > reddit_analytics[tech_id]["latest_activity_utc"]:
                    reddit_analytics[tech_id]["latest_activity_utc"] = original_post["created_utc"]
                    
    except Exception as e:
        print(f"Reddit Batch Processing Loop Error: {e}")
        
    return reddit_analytics