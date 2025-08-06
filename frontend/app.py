import streamlit as st
import requests
import pandas as pd
import os

# Get backend URL from environment variable or use default for local development
raw_backend_url = os.environ.get("BACKEND_URL", "http://localhost:8000")
if not raw_backend_url.startswith("http"):
    BACKEND_URL = f"http://{raw_backend_url}"
else:
    BACKEND_URL = raw_backend_url

st.set_page_config(page_title="Content Strategy Agent", layout="wide")

# Sidebar branding
st.sidebar.title("🧠 Content Strategy Agent")
st.sidebar.markdown("AI for Brands. Built by Riwano Fariz.")

# Main title
st.title("📊 Content Strategy Dashboard")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["📋 Brand Profile", "📈 Trend Insights", "📅 Content Calendar", "🗣️ Voice Analyzer"])

# TAB 1: BRAND PROFILE
with tab1:
    st.header("🔧 Brand Profile Setup")
    
    # --- Brand Voice Analyzer ---
    
    with st.form("brand_form"):
        st.subheader("Brand Information")
        brand_name = st.text_input("Brand Name", placeholder="e.g. Scienza")
        niche = st.text_input("Brand Niche", placeholder="e.g. AI for Founders")
        platform = st.selectbox("Platform", ["Instagram", "LinkedIn", "Twitter"])
        tone = st.text_input("Tone", placeholder="e.g. witty, educational")
        frequency = st.slider("Posts per Week", 1, 7, 3)
        submitted = st.form_submit_button("💾 Save Brand Profile")

    if submitted:
        with st.spinner("Saving brand profile..."):
            payload = {
                "brand_name": brand_name,
                "niche": niche,
                "platform": platform,
                "tone": tone,
                "posting_frequency": frequency
            }
            
            # Store in session state
            st.session_state['brand_profile'] = payload
            
            # Mock save to backend (you can implement actual /save-brand endpoint)
            try:
                # For now, just show success message
                st.success("✅ Brand profile saved!")
                st.info("Brand information is now available for calendar generation.")
            except Exception as e:
                st.error(f"Failed to save brand profile: {e}")

# TAB 2: TREND INSIGHTS
with tab2:
    st.header("📈 Trend Analysis")
    
    with st.form("trend_form"):
        keyword = st.text_input("Enter keyword for trend analysis", placeholder="e.g. AI for Founders")
        submitted_trend = st.form_submit_button("🔍 Analyze Trends")

    if submitted_trend:
        with st.spinner("Analyzing trends from Google Trends and Reddit..."):
            try:
                res = requests.post(f"{BACKEND_URL}/analyze-trends", json={"keyword": keyword})
                if res.status_code == 200:
                    data = res.json()
                    
                    # Check for mock data note
                    if data.get("note"):
                        st.warning(f"⚠️ {data['note']}")
                        st.info("Showing sample data for demonstration purposes.")
                    
                    # Create two columns for better layout
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Google Trends Related Topics
                        st.markdown("### 🔍 Google Trends - Related Topics")
                        if data.get("related_topics") and len(data["related_topics"]) > 0:
                            for topic in data["related_topics"]:
                                st.write(f"• {topic}")
                        else:
                            st.info("No related topics found.")
                        
                        # Google Trends Rising Trends
                        st.markdown("### 🚀 Google Trends - Rising Trends")
                        if data.get("rising_trends") and len(data["rising_trends"]) > 0:
                            for trend in data["rising_trends"]:
                                st.write(f"• {trend}")
                        else:
                            st.info("No rising trends found.")
                    
                    with col2:
                        # Reddit Topics
                        st.markdown("### 📱 Reddit - Trending Topics")
                        if data.get("reddit_topics") and len(data["reddit_topics"]) > 0:
                            for topic in data["reddit_topics"]:
                                st.write(f"• {topic}")
                        else:
                            st.info("No Reddit topics found.")
                        
                        # Reddit Trends
                        st.markdown("### 🔥 Reddit - Hot Discussions")
                        if data.get("reddit_trends") and len(data["reddit_trends"]) > 0:
                            for trend in data["reddit_trends"]:
                                st.write(f"• {trend}")
                        else:
                            st.info("No Reddit trends found.")
                    
                    # Interest Over Time Chart (full width)
                    if data.get("interest_over_time") and len(data["interest_over_time"]) > 0:
                        st.markdown("### 📊 Interest Over Time (Google Trends)")
                        df = pd.DataFrame(data["interest_over_time"])
                        if not df.empty:
                            df['date'] = pd.to_datetime(df['date'])
                            df = df.set_index('date')
                            st.line_chart(df)
                        else:
                            st.info("No interest over time data available.")
                    else:
                        st.info("No interest over time data available for this keyword.")
                    
                    # Summary with data counts
                    topics_count = len(data.get("related_topics", []))
                    trends_count = len(data.get("rising_trends", []))
                    interest_count = len(data.get("interest_over_time", []))
                    reddit_topics_count = len(data.get("reddit_topics", []))
                    reddit_trends_count = len(data.get("reddit_trends", []))
                    
                    if data.get("note"):
                        st.success(f"✅ Analysis completed for '{keyword}' (using sample data)")
                    else:
                        st.success(f"✅ Analysis completed for '{keyword}'")
                    
                    # Show comprehensive data summary
                    st.info(f"📊 Found: {topics_count} Google topics, {trends_count} Google trends, {interest_count} interest points, {reddit_topics_count} Reddit topics, {reddit_trends_count} Reddit trends")
                else:
                    st.error(f"Error: {res.status_code} - {res.text}")
            except Exception as e:
                st.error(f"Connection failed: {e}")
                st.info(f"Make sure the backend server is running on {BACKEND_URL}")

# TAB 3: CONTENT CALENDAR
with tab3:
    st.header("📅 Content Calendar Generator")
    
    # Check if brand profile exists
    brand_profile = None
    if 'brand_profile' in st.session_state:
        brand_profile = st.session_state['brand_profile']
    
    with st.form("calendar_form"):
        st.subheader("Calendar Generation")
        
        if brand_profile:
            st.info("Using saved brand profile. You can modify values below.")
            brand_name = st.text_input("Brand Name", value=brand_profile.get("brand_name", ""))
            niche = st.text_input("Brand Niche", value=brand_profile.get("niche", ""))
            platform = st.selectbox("Platform", ["Instagram", "LinkedIn", "Twitter"], 
                                  index=["Instagram", "LinkedIn", "Twitter"].index(brand_profile.get("platform", "Instagram")))
            tone = st.text_input("Content Tone", value=brand_profile.get("tone", ""))
            frequency = st.slider("Posts per Week", 1, 7, value=brand_profile.get("posting_frequency", 3))
        else:
            brand_name = st.text_input("Brand Name", placeholder="e.g. Scienza")
            niche = st.text_input("Brand Niche", placeholder="e.g. AI for Founders")
            platform = st.selectbox("Platform", ["Instagram", "LinkedIn", "Twitter"])
            tone = st.text_input("Content Tone", placeholder="e.g. witty, educational, casual")
            frequency = st.slider("Posts per Week", 1, 7, 3)

        submitted_calendar = st.form_submit_button("🚀 Generate Calendar")

    if submitted_calendar:
        with st.spinner("Generating content calendar..."):
            payload = {
                "brand_name": brand_name,
                "niche": niche,
                "platform": platform,
                "tone": tone,
                "posting_frequency": frequency
            }
            try:
                res = requests.post(f"{BACKEND_URL}/generate-calendar", json=payload)
                if res.status_code == 200:
                    calendar = res.json()
                    st.session_state['calendar'] = calendar
                    # Display calendar (moved below)
                else:
                    st.error(f"Error: {res.status_code} - {res.text}")
            except Exception as e:
                st.error(f"Connection failed: {e}")

    # Always show calendar, download, and email UI if calendar exists
    calendar = st.session_state.get('calendar')
    if calendar:
        # Display calendar with improved formatting
        for week in calendar:
            st.markdown(f"### 📆 Week {week['week']}")
            
            # Debug information
            st.write(f"Displaying {len(week['posts'])} posts for Week {week['week']}")
            
            # Group posts into rows of 3
            posts = week["posts"]
            for i in range(0, len(posts), 3):
                # Create a new row of columns for every 3 posts
                cols = st.columns(3)
                
                # Get the posts for this row (up to 3)
                row_posts = posts[i:i+3]
                
                # Display each post in its column
                for j, post in enumerate(row_posts):
                    with cols[j]:
                        with st.container(border=True):
                            st.markdown(f"#### {post['day']} - {post['post_type']}")
                            st.markdown(f"**Theme:** {post['theme']}")
                            
                            # Display caption with proper formatting
                            st.markdown("**Caption:**")
                            st.markdown(f"{post['caption']}")
                            
                            # Display hashtags as chips
                            if post.get('hashtags'):
                                st.markdown("**Hashtags:**")
                                hashtags = ' '.join([f'#{tag}' for tag in post['hashtags']])
                                st.markdown(f"{hashtags}")
                            
                            # Add visual separator
                            st.divider()
                      

        # --- Export as CSV ---
        posts = []
        for week in calendar:
            for post in week["posts"]:
                posts.append({
                    "Week": week["week"],
                    "Day": post["day"],
                    "Post Type": post["post_type"],
                    "Theme": post["theme"],
                    "Caption": post["caption"],
                    "Hashtags": " ".join(post.get("hashtags", []))
                })
        df = pd.DataFrame(posts)
        csv_data = df.to_csv(index=False)
        st.download_button("⬇️ Download as CSV", data=csv_data, file_name="calendar.csv", mime="text/csv")

        # --- Email Form ---
        st.markdown("---")
        st.subheader("📤 Email this Calendar")
        email = st.text_input("📧 Enter email to send this calendar")
        if st.button("📤 Send Email"):
            print("Send Email button clicked")
            response = requests.post(f"{BACKEND_URL}/email-calendar", json={
                "email": email,
                "calendar": calendar
            })
            if response.status_code == 200:
                st.success("✅ Calendar emailed successfully!")
            else:
                st.error("❌ Failed to send email.")

# TAB 4: VOICE ANALYZER
with tab4:
    st.header("🗣️ Brand Voice Analyzer (Advanced)")
    st.markdown("Analyze your brand's voice from sample captions.")
    with st.form("voice_analyzer_form"):
        captions = st.text_area("Paste sample captions", placeholder="E.g.\n1. Build your future with AI 🚀\n2. Why founders need data science.\n3. Our new automation tool just dropped!")
        submitted_voice = st.form_submit_button("🔍 Analyze Voice")
    if submitted_voice:
        if captions.strip():
            payload = {"text": captions.strip()}
            try:
                with st.spinner("Analyzing brand voice..."):
                    res = requests.post(f"{BACKEND_URL}/analyze-tone", json=payload)
                if res.status_code == 200:
                    result = res.json()
                    description = result.get("brand_voice_description")
                    if description:
                        st.success("✅ Voice Analysis Complete!")
                        st.markdown(f"**Brand Voice Description:**\n\n{description}")
                    else:
                        st.warning("No description returned.")
                else:
                    st.error(f"Error: {res.status_code} - {res.text}")
            except Exception as e:
                st.error(f"Connection failed: {e}")
        else:
            st.warning("Please provide sample captions to analyze.")