import json
import datetime
from github_fetcher import fetch_and_stage_github
from reddit_fetcher import fetch_and_stage_reddit

def run_pipeline():
    print("=================================================================")
    print("🚀 INITIALIZING ADVANCED REAL-TIME TREND INTELLIGENCE SYSTEM")
    print("=================================================================\n")
    
    # 1. Gather rich live metadata streams from GitHub
    github_snapshot = fetch_and_stage_github()
    
    # =================================================================
    # STRATEGY A: HOT-RELOAD CACHE ACTIVATION
    # Take live keys discovered by GitHub and append them to our local cache
    # before running Reddit so that Reddit can immediately utilize them.
    # =================================================================
    try:
        try:
            with open("vocabulary_cache.txt", "r") as cache_file:
                existing_vocab = set(cache_file.read().splitlines())
        except FileNotFoundError:
            existing_vocab = set()

        new_github_keys = set(github_snapshot.keys())
        updated_vocab = existing_vocab.union(new_github_keys)

        with open("vocabulary_cache.txt", "w") as cache_file:
            for word in updated_vocab:
                if word.strip():
                    cache_file.write(f"{word.strip()}\n")
        print(f"[Strategy A] Vocabulary cache hot-reloaded! Total tracked tools: {len(updated_vocab)}")
    except Exception as cache_err:
        print(f"Failed to update vocabulary cache: {cache_err}")

    # 2. Now execute Reddit fetcher equipped with updated dynamic tokens
    reddit_snapshot = fetch_and_stage_reddit()
    
    # 3. Stage snapshots locally to maintain state resilience
    with open("staged_github.json", "w") as f:
        json.dump(github_snapshot, f, indent=4)
    with open("staged_reddit.json", "w") as f:
        json.dump(reddit_snapshot, f, indent=4)

    # 4. Handle Dynamic Discoveries using unified master key mapping
    merged_intelligence = {}
    master_keys = set(list(github_snapshot.keys()) + list(reddit_snapshot.keys()))
    
    current_sync_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    for tech in master_keys:
        git = github_snapshot.get(tech, {"repo_name": "N/A", "stars": 0, "forks": 0, "last_pushed_utc": None, "tags": []})
        red = reddit_snapshot.get(tech, {"mentions_count": 0, "cumulative_sentiment": 0, "engagement_score": 0, "latest_activity_utc": None})
        
        # Calculate standard average sentiment score to avoid division errors
        total_mentions = red["mentions_count"]
        avg_sentiment = round(red["cumulative_sentiment"] / total_mentions, 2) if total_mentions > 0 else 0.0
        
        merged_intelligence[tech] = {
            "technology_id": tech,
            "github": {
                "repository": git["repo_name"],
                "stars_volume": git["stars"],
                "forks_volume": git["forks"],
                "upstream_pushed_utc": git["last_pushed_utc"],
                "architecture_tags": git.get("tags", [])
            },
            "reddit": {
                "raw_mentions_volume": total_mentions,
                "calculated_avg_sentiment": avg_sentiment,
                "engagement_upvotes": red["engagement_score"],
                "upstream_activity_utc": red["latest_activity_utc"]
            },
            "system_pipeline_sync_utc": current_sync_time
        }
        
    print("\n=================================================================")
    print("📊 UNIFIED CORE METRICS INGESTION PAYLOAD GENERATED")
    print("=================================================================")
    print(json.dumps(merged_intelligence, indent=4))
    
    return merged_intelligence

if __name__ == "__main__":
    run_pipeline()