# --- Gradio implementation replacing Streamlit frontend ---
import gradio as gr
import requests
import pandas as pd
import os

# Get backend URL from environment variable or use default for local development
raw_backend_url = os.environ.get("BACKEND_URL", "http://localhost:8000")
if not raw_backend_url.startswith("http"):
    BACKEND_URL = f"http://{raw_backend_url}"
else:
    BACKEND_URL = raw_backend_url

brand_profile_state = {}
calendar_state = {}

def save_brand_profile(brand_name, niche, platform, tone, frequency):
    payload = {
        "brand_name": brand_name,
        "niche": niche,
        "platform": platform,
        "tone": tone,
        "posting_frequency": frequency
    }
    # Try to persist to backend first
    try:
        res = requests.post(f"{BACKEND_URL}/brands", json={
            "name": brand_name,
            "niche": niche,
            "tone": tone,
            "platform": platform,
            "posting_frequency": frequency
        })
        if res.status_code in (200, 201):
            data = res.json()
            # Keep an in-memory copy too
            brand_profile_state.clear()
            # normalize keys to match previous in-memory shape
            brand_profile_state.update({
                "brand_name": data.get("name", brand_name),
                "niche": data.get("niche", niche),
                "platform": data.get("platform", platform),
                "tone": data.get("tone", tone),
                "posting_frequency": data.get("posting_frequency", frequency),
                "id": data.get("id")
            })
            return f"✅ Brand persisted: {brand_profile_state['brand_name']}"
        else:
            # fallback to in-memory only
            brand_profile_state.clear()
            brand_profile_state.update({
                "brand_name": brand_name,
                "niche": niche,
                "platform": platform,
                "tone": tone,
                "posting_frequency": frequency
            })
            return f"Saved locally but failed to persist: {res.status_code} - {res.text}"
    except Exception as e:
        # On connection error, save locally and inform user
        brand_profile_state.clear()
        brand_profile_state.update({
            "brand_name": brand_name,
            "niche": niche,
            "platform": platform,
            "tone": tone,
            "posting_frequency": frequency
        })
        return f"Saved locally, backend unavailable: {e}"

def analyze_trends(keyword):
    try:
        res = requests.post(f"{BACKEND_URL}/analyze-trends", json={"keyword": keyword})
        if res.status_code == 200:
            data = res.json()
            info_msgs = []
            if data.get("note"):
                info_msgs.append(f"⚠️ {data['note']}")
                info_msgs.append("Showing sample data for demonstration purposes.")
            
            google_topics = "\n".join([f"• {t}" for t in data.get("related_topics", [])]) or "No related topics found."
            google_trends = "\n".join([f"• {t}" for t in data.get("rising_trends", [])]) or "No rising trends found."
            reddit_topics = "\n".join([f"• {t}" for t in data.get("reddit_topics", [])]) or "No Reddit topics found."
            reddit_trends = "\n".join([f"• {t}" for t in data.get("reddit_trends", [])]) or "No Reddit trends found."
            
            chart = None
            if data.get("interest_over_time") and len(data["interest_over_time"]) > 0:
                df = pd.DataFrame(data["interest_over_time"])
                if not df.empty:
                    df['date'] = pd.to_datetime(df['date'])
                    df = df.set_index('date')
                    chart = df
            # Use backend-provided summary when available, otherwise fall back to a simple counts summary
            counts_summary = f"📊 Found: {len(data.get('related_topics', []))} Google topics, {len(data.get('rising_trends', []))} Google trends, {len(data.get('interest_over_time', []))} interest points, {len(data.get('reddit_topics', []))} Reddit topics, {len(data.get('reddit_trends', []))} Reddit trends"
            backend_summary = data.get('summary') if data.get('summary') else counts_summary
            status = f"✅ Analysis completed for '{keyword}'" + (" (using sample data)" if data.get("note") else "")

            # info contains any notes or warnings; summary is the highlights returned separately
            info_text = "\n".join(info_msgs) if info_msgs else ""

            return google_topics, google_trends, reddit_topics, reddit_trends, chart, status, info_text, backend_summary
        else:
            return "", "", "", "", None, f"Error: {res.status_code} - {res.text}", ""
    except Exception as e:
        return "", "", "", "", None, f"Connection failed: {e}", f"Make sure the backend server is running on {BACKEND_URL}", ""

def generate_calendar(brand_name, niche, platform, tone, frequency):
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
            calendar_state.clear()
            calendar_state.update({"calendar": calendar})
            
            weeks = []
            for week in calendar:
                week_str = f"### 📆 Week {week['week']}\nDisplaying {len(week['posts'])} posts for Week {week['week']}\n"
                for post in week["posts"]:
                    hashtags = ' '.join([f'#{tag}' for tag in post.get('hashtags', [])])
                    week_str += f"#### {post['day']} - {post['post_type']}\n**Theme:** {post['theme']}\n**Caption:** {post['caption']}\n**Hashtags:** {hashtags}\n---\n"
                weeks.append(week_str)
            
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
            return weeks, csv_data, ""
        else:
            return [], "", f"Error: {res.status_code} - {res.text}"
    except Exception as e:
        return [], "", f"Connection failed: {e}"

def send_email(email):
    calendar = calendar_state.get("calendar")
    if not calendar:
        return "No calendar to send. Generate calendar first."
    response = requests.post(f"{BACKEND_URL}/email-calendar", json={
        "email": email,
        "calendar": calendar
    })
    if response.status_code == 200:
        return "✅ Calendar emailed successfully!"
    else:
        return "❌ Failed to send email."

def analyze_voice(captions):
    if not captions.strip():
        return "Please provide sample captions to analyze.", ""
    payload = {"text": captions.strip()}
    try:
        res = requests.post(f"{BACKEND_URL}/analyze-tone", json=payload)
        if res.status_code == 200:
            result = res.json()
            description = result.get("brand_voice_description")
            if description:
                return "✅ Voice Analysis Complete!", description
            else:
                return "No description returned.", ""
        else:
            return f"Error: {res.status_code} - {res.text}", ""
    except Exception as e:
        return f"Connection failed: {e}", ""

with gr.Blocks(title="Content Strategy Agent") as demo:
    gr.Markdown("# 🧠 Content Strategy Agent\nAI for Brands. Built by Influcrafters.")
    gr.Markdown("## 📊 Content Strategy Dashboard")

    with gr.Tab("📋 Brand Profile"):
        gr.Markdown("### 🔧 Brand Profile Setup")
        with gr.Row():
            with gr.Column():
                brand_name = gr.Textbox(label="Brand Name", placeholder="e.g. Influcrafters")
                niche = gr.Textbox(label="Brand Niche", placeholder="e.g. AI for Founders")
                platform = gr.Dropdown(label="Platform", choices=["Instagram", "LinkedIn"], value="Instagram")
                tone = gr.Textbox(label="Tone", placeholder="e.g. witty, educational")
                frequency = gr.Slider(label="Posts per Week", minimum=1, maximum=7, value=3, step=1)
                save_btn = gr.Button("💾 Save Brand Profile")
                save_status = gr.Textbox(label="Status", interactive=False)

    # ...existing code...
    # Move save_and_update_dropdown and save_btn.click wiring here, after all components are defined

    with gr.Tab("📈 Trend Insights"): 
        gr.Markdown("### 📈 Trend Analysis") 
        keyword = gr.Textbox(label="Enter keyword for trend analysis", placeholder="e.g. AI for Founders") 
        analyze_btn = gr.Button("🔍 Analyze Trends") 
        google_topics = gr.Markdown() 
        google_trends = gr.Markdown() 
        reddit_topics = gr.Markdown() 
        reddit_trends = gr.Markdown() 
        chart = gr.LinePlot(label="Interest Over Time (Google Trends)", x="date") 
        status = gr.Textbox(label="Status", interactive=False) 
        info = gr.Markdown() 
        # New: summary area to display model or synthesized highlights
        summary = gr.Markdown()
        # analyzer now returns an extra `summary` field (uses backend summary when available)
        analyze_btn.click(analyze_trends, [keyword], [google_topics, google_trends, reddit_topics, reddit_trends, chart, status, info, summary])

    with gr.Tab("📅 Content Calendar"):
        gr.Markdown("### 📅 Content Calendar Generator")
        # Saved brands selector
        with gr.Row():
            with gr.Column(scale=2):
                saved_brand_dropdown = gr.Dropdown(label="Saved brand profiles", choices=[], value=None)
            with gr.Column(scale=1):
                refresh_brands_btn = gr.Button("Refresh brands")
                apply_brand_btn = gr.Button("Load brand")

        with gr.Row():
            with gr.Column():
                new_cal_brand_name = gr.Textbox(label="Brand Name", placeholder="e.g. Influcrafters", value=brand_profile_state.get("brand_name", ""))
                new_cal_niche = gr.Textbox(label="Brand Niche", placeholder="e.g. AI for marketing", value=brand_profile_state.get("niche", ""))
                new_cal_platform = gr.Dropdown(label="Platform", choices=["Instagram", "LinkedIn"], value=brand_profile_state.get("platform", "Instagram"))
                new_cal_tone = gr.Textbox(label="Content Tone", placeholder="e.g. witty, educational", value=brand_profile_state.get("tone", ""))
                new_cal_frequency = gr.Slider(label="Posts per Week", minimum=1, maximum=7, value=brand_profile_state.get("posting_frequency", 3), step=1)
                gen_btn = gr.Button("🚀 Generate Calendar")
                cal_status = gr.Textbox(label="Status", interactive=False)
                
        weeks = gr.Markdown()
        csv_download = gr.File(label="⬇️ Download as CSV")
        
        def gen_and_update(brand_name, niche, platform, tone, frequency):
            if not any([brand_name, niche, platform, tone, frequency]):
                if not brand_profile_state:
                    return "", "", "Please fill in brand information or save a brand profile first."
                brand_name = brand_profile_state.get("brand_name")
                niche = brand_profile_state.get("niche")
                platform = brand_profile_state.get("platform", "Instagram")
                tone = brand_profile_state.get("tone")
                frequency = brand_profile_state.get("posting_frequency", 3)
            
            weeks_list, csv_data, status = generate_calendar(brand_name, niche, platform, tone, frequency)
            weeks_md = "\n".join(weeks_list)
            
            if csv_data:
                with open("calendar.csv", "w", encoding="utf-8") as f:
                    f.write(csv_data)
            
            return weeks_md, "calendar.csv" if csv_data else None, status
            
        gen_btn.click(
            gen_and_update,
            [new_cal_brand_name, new_cal_niche, new_cal_platform, new_cal_tone, new_cal_frequency],
            [weeks, csv_download, cal_status]
        )

        # Backend integration: load saved brands into dropdown
        def load_saved_brands():
            try:
                res = requests.get(f"{BACKEND_URL}/brands")
                if res.status_code == 200:
                    items = res.json()
                    # choices format: "id|name" to carry id through the dropdown
                    choices = [f"{b['id']}|{b['name']}" for b in items]
                    return gr.update(choices=choices, value=None), "Loaded brands."
                return [], f"Failed to load brands: {res.status_code}"
            except Exception as e:
                return gr.update(choices=[]), f"Connection error: {e}"

        def apply_selected_brand(selection):
            if not selection:
                return gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), "No brand selected"
            try:
                brand_id, _ = selection.split("|", 1)
                res = requests.get(f"{BACKEND_URL}/brands")
                if res.status_code == 200:
                    for b in res.json():
                        if b['id'] == brand_id:
                            return b.get('name',''), b.get('niche',''), b.get('platform','Instagram'), b.get('tone',''), b.get('posting_frequency',3), "Brand loaded"
                return gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), "Brand not found"
            except Exception as e:
                return gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), f"Error: {e}"

        # Wire refresh and apply buttons
        refresh_brands_btn.click(load_saved_brands, [], [saved_brand_dropdown, cal_status])
        apply_brand_btn.click(apply_selected_brand, [saved_brand_dropdown], [new_cal_brand_name, new_cal_niche, new_cal_platform, new_cal_tone, new_cal_frequency, cal_status])

        gr.Markdown("---")
        gr.Markdown("#### 📤 Email this Calendar")
        email = gr.Textbox(label="📧 Enter email to send this calendar")
        email_btn = gr.Button("📤 Send Email")
        email_status = gr.Textbox(label="Email Status", interactive=False)
        email_btn.click(send_email, [email], email_status)

    with gr.Tab("🗣️ Voice Analyzer"):
        gr.Markdown("### 🗣️ Brand Voice Analyzer")
        gr.Markdown("Analyze your brand's voice from sample captions.")
        captions = gr.Textbox(label="Paste sample captions", lines=5, placeholder="E.g.\n1. Build your future with AI 🚀\n2. Why founders need data science.\n3. Our new automation tool just dropped!")
        analyze_voice_btn = gr.Button("🔍 Analyze Voice")
        voice_status = gr.Textbox(label="Status", interactive=False)
        voice_desc = gr.Markdown()
        analyze_voice_btn.click(analyze_voice, [captions], [voice_status, voice_desc])

    # Define save handler after all components are created so they are in scope
    def save_and_update_dropdown(brand_name, niche, platform, tone, frequency):
        # Persist via backend and then refresh dropdown + populate calendar form
        status_msg = save_brand_profile(brand_name, niche, platform, tone, frequency)
        print(f"[frontend] save_brand_profile returned: {status_msg}")
        try:
            res = requests.get(f"{BACKEND_URL}/brands")
            print(f"[frontend] GET /brands status: {res.status_code}")
            if res.status_code == 200:
                items = res.json()
                print(f"[frontend] GET /brands returned {len(items)} items")
                choices = [f"{b['id']}|{b['name']}" for b in items]
                selected = choices[-1] if choices else None
                print(f"[frontend] Latest choice: {selected}")
                dropdown_update = gr.update(choices=choices, value=selected)
                if selected:
                    # find selected brand details
                    brand_id, _ = selected.split("|", 1)
                    for b in items:
                        if b['id'] == brand_id:
                            return status_msg, dropdown_update, b.get('name',''), b.get('niche',''), b.get('platform','Instagram'), b.get('tone',''), b.get('posting_frequency',3)
                return status_msg, dropdown_update, '', '', 'Instagram', '', 3
            return f"{status_msg} (failed to refresh brands: {res.status_code})", gr.update(choices=[]), '', '', 'Instagram', '', 3
        except Exception as e:
            return f"{status_msg} (refresh error: {e})", gr.update(choices=[]), '', '', 'Instagram', '', 3

    # Wire save button to handler (components are in scope)
    save_btn.click(
        save_and_update_dropdown,
        [brand_name, niche, platform, tone, frequency],
        [save_status, saved_brand_dropdown, new_cal_brand_name, new_cal_niche, new_cal_platform, new_cal_tone, new_cal_frequency]
    )

if __name__ == "__main__":
    demo.launch(share=True)
