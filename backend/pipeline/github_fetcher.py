import requests
import datetime
import openai
from models import GitHubValidationModel

client = openai.OpenAI()

def fetch_and_stage_github():
    print("[GitHub Pipeline] Querying live velocity endpoints...")
    
    # Track items pushed to within the last 30 days to catch real velocity (Fixes Hole 4)
    thirty_days_ago = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
    query = f"stars:>500+pushed:>{thirty_days_ago}"
    
    url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc"
    headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "TrendIntelPlatform-Dev"}
    
    response = requests.get(url, headers=headers)
    github_profiles = {}
    
    if response.status_code == 200:
        repos = response.json().get("items", [])
        
        for repo in repos[:15]:
            context_str = f"Repo: {repo['full_name']} | Primary Lang: {repo['language']} | Desc: {repo['description']}"
            
            try:
                # Force dynamic translation via structured output (Fixes Holes 1, 2, Cold Start)
                completion = client.beta.chat.completions.parse(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an elite technical archivist. Extract a single-word lowercase canonical slug for the technology. Example: 'tiangolo/fastapi' becomes 'fastapi', 'facebook/react' becomes 'react'."},
                        {"role": "user", "content": f"Analyze this project: {context_str}"}
                    ],
                    response_format=GitHubValidationModel,
                )
                
                analysis = completion.choices[0].message.parsed
                
                if not analysis.is_valid_dev_tool:
                    continue
                
                # FIX: Standardize upstream UTC pushed_at string directly from GitHub's server clock
                raw_pushed_time = repo.get("pushed_at")  # E.g., '2026-06-07T08:12:00Z'
                
                tech_id = analysis.tech_id
                github_profiles[tech_id] = {
                    "repo_name": repo["full_name"],
                    "stars": repo["stargazers_count"],
                    "forks": repo["forks_count"],
                    "last_pushed_utc": raw_pushed_time,
                    "tags": analysis.relevance_tags
                }
            except Exception as e:
                print(f"Skipping GitHub item due to parsing exception: {e}")
    else:
        print(f" GitHub Gateway Error: {response.status_code}")
        
    return github_profiles