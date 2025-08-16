from pytrends.request import TrendReq
from datetime import datetime, timedelta
import time
import random
import requests
import praw
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
import os

# OpenRouter config (optional)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct")

def call_model_summary(prompt: str, max_tokens: int = 300) -> str:
    """Call OpenRouter (chat completion) synchronously to get a summary."""
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY not set")
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 40
    }
    try:
        resp = requests.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        # Navigate response structure defensively
        choices = data.get("choices") or []
        if choices and isinstance(choices, list):
            msg = choices[0].get("message", {}).get("content") if isinstance(choices[0], dict) else None
            if msg:
                return msg.strip()
        # fallback to text if present
        return data.get("text", "").strip()
    except Exception as e:
        raise


def synthesize_summary_from_data(result: dict, keyword: str) -> str:
    """Create a concise 3-6 bullet summary from available trend data when model is unavailable."""
    bullets = []
    try:
        related = result.get('related_topics', [])[:4]
        rising = result.get('rising_trends', [])[:4]
        reddit = result.get('reddit_trends', [])[:3]
        interest = result.get('interest_over_time', [])

        if related:
            bullets.append(f"Top related searches: {', '.join(related)}.")

        if rising:
            bullets.append(f"Rising trends to watch: {', '.join(rising)}.")

        if reddit:
            bullets.append(f"Reddit highlights: {', '.join(reddit)}.")

        # interest trend direction
        if interest and isinstance(interest, list) and len(interest) >= 2:
            try:
                first = int(interest[0].get('score', 0))
                last = int(interest[-1].get('score', 0))
                if last > first:
                    bullets.append(f"Interest is rising (from {first} to {last}). Consider doubling down on timely content.")
                elif last < first:
                    bullets.append(f"Interest is declining (from {first} to {last}). Consider evergreen content or re-testing messaging.")
                else:
                    bullets.append("Interest appears stable over the sampled period.")
            except Exception:
                pass

        # short actionable recommendations
        if len(bullets) < 3:
            bullets.append(f"Action: experiment with content around '{keyword}' using formats: short reels, how-to posts, and case studies.")

        # Ensure 3-6 bullets
        return '\n'.join([f"- {b}" for b in bullets[:6]])
    except Exception as e:
        return f"No summary available: {e}"

def get_reddit_trends(keyword: str) -> dict:
    """Fetch trending Reddit posts and topics related to the keyword"""
    try:
        # Initialize Reddit client
        reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent=os.getenv('REDDIT_USER_AGENT', 'content-strategy-planner/0.1')
        )
        
        print(f"Fetching Reddit trends for: {keyword}")
        
        # Define relevant subreddits for tech/business trends
        subreddits = [
            'technology', 'programming', 'startups', 'entrepreneur',
            'business', 'marketing', 'artificial', 'MachineLearning',
            'datascience', 'webdev', 'productivity', 'innovation'
        ]
        
        reddit_topics = []
        reddit_trends = []
        
        # Search for posts containing the keyword
        for subreddit_name in subreddits[:5]:  # Limit to first 5 subreddits
            try:
                subreddit = reddit.subreddit(subreddit_name)
                
                # Search for posts with the keyword
                search_results = subreddit.search(keyword, sort='hot', limit=3)
                
                for post in search_results:
                    # Extract topic from post title
                    topic = post.title[:100] + "..." if len(post.title) > 100 else post.title
                    reddit_topics.append(topic)
                    
                    # Add subreddit context
                    reddit_trends.append(f"r/{subreddit_name}: {post.title[:80]}")
                    
                    if len(reddit_topics) >= 5:  # Limit results
                        break
                        
            except Exception as e:
                print(f"Error fetching from r/{subreddit_name}: {e}")
                continue
        
        # If no results found, try broader search
        if not reddit_topics:
            try:
                # Search across all subreddits
                search_results = reddit.subreddit('all').search(keyword, sort='hot', limit=5)
                
                for post in search_results:
                    topic = post.title[:100] + "..." if len(post.title) > 100 else post.title
                    reddit_topics.append(topic)
                    reddit_trends.append(f"r/{post.subreddit}: {post.title[:80]}")
                    
            except Exception as e:
                print(f"Error in broad Reddit search: {e}")
        
        print(f"Found {len(reddit_topics)} Reddit topics and {len(reddit_trends)} trends")
        
        return {
            "reddit_topics": reddit_topics,
            "reddit_trends": reddit_trends
        }
        
    except Exception as e:
        print(f"Reddit API error: {e}")
        return {
            "reddit_topics": [],
            "reddit_trends": []
        }

def get_mock_trend_data(keyword: str) -> dict:
    """Generate mock trend data when Google Trends fails"""
    # More realistic mock data based on the keyword
    mock_topics = [
        f"{keyword} tips", f"{keyword} guide", f"{keyword} tutorial",
        f"{keyword} examples", f"{keyword} best practices", f"{keyword} strategies",
        f"{keyword} tools", f"{keyword} resources", f"{keyword} case studies"
    ]
    
    mock_trends = [
        f"new {keyword} trends", f"{keyword} 2024", f"{keyword} latest",
        f"{keyword} updates", f"{keyword} innovations", f"{keyword} future",
        f"{keyword} predictions", f"{keyword} developments"
    ]
    
    # Generate mock interest over time data with more realistic patterns
    mock_interest = []
    base_date = datetime.now() - timedelta(days=30)
    for i in range(30):
        # Create a more realistic trend pattern
        base_score = 30 + (i % 7) * 5  # Weekly pattern
        random_variation = random.randint(-10, 10)
        score = max(10, min(100, base_score + random_variation))
        
        mock_interest.append({
            "date": (base_date + timedelta(days=i)).strftime("%Y-%m-%d"),
            "score": score
        })
    
    return {
        "keyword": keyword,
        "related_topics": mock_topics,
        "rising_trends": mock_trends,
        "interest_over_time": mock_interest,
        "reddit_topics": [],
        "reddit_trends": [],
        "note": "Sample data - APIs unavailable"
    }

def try_google_trends_with_retry(keyword: str, max_retries: int = 3) -> dict:
    """Try Google Trends with retry mechanism"""
    for attempt in range(max_retries):
        try:
            print(f"Google Trends attempt {attempt + 1}/{max_retries}")
            
            # Initialize with different parameters each attempt
            pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 25))
            kw_list = [keyword]
            
            # Build payload
            pytrends.build_payload(kw_list, cat=0, timeframe='today 12-m', geo='', gprop='')
            
            # Longer delay between attempts
            time.sleep(3 + attempt * 2)
            
            # Try to get data
            related_topics = []
            rising_trends = []
            interest_over_time = []
            
            # Related queries
            try:
                related = pytrends.related_queries()
                if isinstance(related, dict) and keyword in related and related[keyword] is not None:
                    keyword_data = related[keyword]
                    
                    if 'top' in keyword_data and keyword_data['top'] is not None:
                        top_df = keyword_data['top']
                        if hasattr(top_df, 'head') and len(top_df) > 0:
                            related_topics = top_df['query'].head(5).tolist()
                    
                    if 'rising' in keyword_data and keyword_data['rising'] is not None:
                        rising_df = keyword_data['rising']
                        if hasattr(rising_df, 'head') and len(rising_df) > 0:
                            rising_trends = rising_df['query'].head(5).tolist()
            except Exception as e:
                print(f"Related queries failed: {e}")
            
            # Interest over time
            try:
                interest = pytrends.interest_over_time()
                if not interest.empty and keyword in interest.columns:
                    for idx, row in interest.iterrows():
                        try:
                            score = int(row[keyword])
                            interest_over_time.append({
                                "date": idx.strftime("%Y-%m-%d"),
                                "score": score
                            })
                        except (ValueError, KeyError, TypeError):
                            continue
            except Exception as e:
                print(f"Interest over time failed: {e}")
            
            # If we got any real data, return it
            if related_topics or rising_trends or interest_over_time:
                print(f"Success! Got {len(related_topics)} topics, {len(rising_trends)} trends, {len(interest_over_time)} interest points")
                return {
                    "keyword": keyword,
                    "related_topics": related_topics,
                    "rising_trends": rising_trends,
                    "interest_over_time": interest_over_time
                }
            
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)  # Wait before retry
    
    # All attempts failed
    print("All Google Trends attempts failed")
    return None

def analyze_trends(keyword: str) -> dict:
    print(f"Analyzing trends for keyword: {keyword}")
    
    # Get Reddit trends
    reddit_data = get_reddit_trends(keyword)
    
    # Try Google Trends
    google_data = try_google_trends_with_retry(keyword)
    
    if google_data:
        # Combine Google Trends with Reddit data
        result = {
            "keyword": keyword,
            "related_topics": google_data.get("related_topics", []),
            "rising_trends": google_data.get("rising_trends", []),
            "interest_over_time": google_data.get("interest_over_time", []),
            "reddit_topics": reddit_data.get("reddit_topics", []),
            "reddit_trends": reddit_data.get("reddit_trends", [])
        }
        
        # Supplement with mock data if needed
        if not result.get("related_topics") or not result.get("rising_trends"):
            print("Supplementing with mock related data")
            mock_data = get_mock_trend_data(keyword)
            if not result.get("related_topics"):
                result["related_topics"] = mock_data["related_topics"]
            if not result.get("rising_trends"):
                result["rising_trends"] = mock_data["rising_trends"]

        # Append a concise AI-generated summary (highlights) when possible
        try:
            if OPENROUTER_API_KEY:
                # Build a short context for the model
                top_related = result.get("related_topics", [])[:6]
                top_rising = result.get("rising_trends", [])[:6]
                top_reddit = result.get("reddit_trends", [])[:6]
                interest = result.get("interest_over_time", [])
                interest_summary = ""
                if interest:
                    try:
                        scores = [int(p.get("score", 0)) for p in interest if isinstance(p, dict)]
                        if scores:
                            interest_summary = f"interest points: min={min(scores)}, max={max(scores)}, latest={scores[-1]}"
                    except Exception:
                        interest_summary = "interest data present"

                prompt_parts = [
                    f"Keyword: {keyword}",
                    f"Top related topics: {', '.join(top_related) if top_related else 'none'}",
                    f"Rising trends: {', '.join(top_rising) if top_rising else 'none'}",
                    f"Reddit highlights: {', '.join(top_reddit) if top_reddit else 'none'}",
                    f"{interest_summary}",
                    "\nProvide a concise summary (3-6 bullet highlights) of the most important insights and recommended actions for a marketer according to the reddit and google trends insight given above. Make sure every point is explained in detail in bullet points."
                ]
                prompt = "\n".join([p for p in prompt_parts if p])
                try:
                    summary = call_model_summary(prompt, max_tokens=5000)
                    if summary:
                        result["summary"] = summary
                except Exception as e:
                    print(f"Model summary failed: {e}")
        except Exception as e:
            print(f"Unexpected error when generating summary: {e}")

        # Ensure summary exists even if model was not used or failed
        if "summary" not in result:
            result["summary"] = synthesize_summary_from_data(result, keyword)

        return result
    else:
        # Return mock data with Reddit data if available
        mock_data = get_mock_trend_data(keyword)
        mock_data["reddit_topics"] = reddit_data.get("reddit_topics", [])
        mock_data["reddit_trends"] = reddit_data.get("reddit_trends", [])
        # Also attempt to summarize mock+reddit if model available
        try:
            if OPENROUTER_API_KEY:
                prompt = f"Keyword: {keyword}\nTop related topics: {', '.join(mock_data.get('related_topics', [])[:6])}\nRising trends: {', '.join(mock_data.get('rising_trends', [])[:6])}\nReddit highlights: {', '.join(mock_data.get('reddit_trends', [])[:6])}\n\nProvide a concise summary (3-6 bullet highlights) and recommended actions for a marketer."
                try:
                    summary = call_model_summary(prompt, max_tokens=200)
                    if summary:
                        mock_data['summary'] = summary
                except Exception as e:
                    print(f"Model summary on mock data failed: {e}")
        except Exception:
            print("Unexpected error when generating mock summary")

        # Ensure summary exists even if model not available
        if 'summary' not in mock_data:
            mock_data['summary'] = synthesize_summary_from_data(mock_data, keyword)

        return mock_data