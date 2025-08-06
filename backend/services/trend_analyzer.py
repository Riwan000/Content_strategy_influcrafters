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
        
        return result
    else:
        # Return mock data with Reddit data if available
        mock_data = get_mock_trend_data(keyword)
        mock_data["reddit_topics"] = reddit_data.get("reddit_topics", [])
        mock_data["reddit_trends"] = reddit_data.get("reddit_trends", [])
        return mock_data 