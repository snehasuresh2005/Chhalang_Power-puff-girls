import streamlit as st
from datetime import datetime, timezone
import base64
import requests
import google.generativeai as genai
import json

GEMINI_API_KEY = "GOOGLE-API-KEY"
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

GITHUB_USERNAME = "username"
GITHUB_TOKEN = "github_token"
GITHUB_API_URL = "https://api.github.com"

def get_repos():
    url = f"{GITHUB_API_URL}/user/repos"
    response = requests.get(url, auth=(GITHUB_USERNAME, GITHUB_TOKEN))
    if response.status_code != 200:
        return [f"Error: {response.status_code} - {response.text}"]
    return [repo['name'] for repo in response.json()]

def get_repo_details(repo_name):
    details = {}
    pr_url = f"{GITHUB_API_URL}/repos/{GITHUB_USERNAME}/{repo_name}/pulls?state=all"
    prs = requests.get(pr_url, auth=(GITHUB_USERNAME, GITHUB_TOKEN)).json()
    details['pr_count'] = len(prs) if isinstance(prs, list) else 0

    branches_url = f"{GITHUB_API_URL}/repos/{GITHUB_USERNAME}/{repo_name}/branches"
    branches = requests.get(branches_url, auth=(GITHUB_USERNAME, GITHUB_TOKEN)).json()
    details['branches'] = [b['name'] for b in branches] if isinstance(branches, list) else []

    readme_url = f"{GITHUB_API_URL}/repos/{GITHUB_USERNAME}/{repo_name}/readme"
    readme_resp = requests.get(readme_url, auth=(GITHUB_USERNAME, GITHUB_TOKEN))
    if readme_resp.status_code == 200:
        content_encoded = readme_resp.json().get('content', '')
        try:
            content_bytes = base64.b64decode(content_encoded)
            readme_content = content_bytes.decode('utf-8', errors='ignore')
        except Exception:
            readme_content = "Error decoding README"
        details['readme'] = readme_content[:200]
    else:
        details['readme'] = "No README found"

    repo_url = f"{GITHUB_API_URL}/repos/{GITHUB_USERNAME}/{repo_name}"
    repo_info = requests.get(repo_url, auth=(GITHUB_USERNAME, GITHUB_TOKEN)).json()
    details['description'] = repo_info.get('description', '')
    details['stars'] = repo_info.get('stargazers_count', 0)
    details['forks'] = repo_info.get('forks_count', 0)

    return details

def get_prs_by_user(username):
    repos = get_repos()
    all_prs = []
    for repo in repos:
        if repo.startswith("Error:"):
            continue
        pr_url = f"{GITHUB_API_URL}/repos/{GITHUB_USERNAME}/{repo}/pulls?state=all"
        prs = requests.get(pr_url, auth=(GITHUB_USERNAME, GITHUB_TOKEN)).json()
        if not isinstance(prs, list):
            continue
        for pr in prs:
            if pr['user']['login'].lower() == username.lower():
                created_date = datetime.strptime(pr['created_at'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')
                state = "MERGED" if pr.get('merged_at') else pr['state'].upper()
                all_prs.append({
                    'pr_id': pr['number'],
                    'title': pr['title'],
                    'author': username,
                    'state': state,
                    'date': created_date,
                    'repo': repo
                })
    return all_prs

def get_pr_reviews_by_reviewer(reviewer_name):
    repos = get_repos()
    all_prs_with_reviews = []
    for repo in repos:
        if repo.startswith("Error:"):
            continue
        pr_url = f"{GITHUB_API_URL}/repos/{GITHUB_USERNAME}/{repo}/pulls?state=all"
        prs = requests.get(pr_url, auth=(GITHUB_USERNAME, GITHUB_TOKEN)).json()
        if not isinstance(prs, list):
            continue
        for pr in prs:
            pr_number = pr['number']
            pr_title = pr['title']
            reviews_url = f"{GITHUB_API_URL}/repos/{GITHUB_USERNAME}/{repo}/pulls/{pr_number}/reviews"
            reviews = requests.get(reviews_url, auth=(GITHUB_USERNAME, GITHUB_TOKEN)).json()
            if not isinstance(reviews, list):
                continue
            for review in reviews:
                if review['user']['login'].lower() == reviewer_name.lower():
                    review_date = datetime.strptime(review['submitted_at'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')
                    decision = "APPROVED" if review['state'] == 'APPROVED' else "CHANGES_REQUESTED" if review['state'] == 'CHANGES_REQUESTED' else review['state']
                    all_prs_with_reviews.append({
                        'pr_id': pr_number,
                        'title': pr_title,
                        'reviewer': reviewer_name,
                        'decision': decision,
                        'date': review_date,
                        'repo': repo
                    })
    return all_prs_with_reviews

def get_prs_merged_without_approval():
    repos = get_repos()
    prs_without_approval = []
    for repo in repos:
        if repo.startswith("Error:"):
            continue
        pr_url = f"{GITHUB_API_URL}/repos/{GITHUB_USERNAME}/{repo}/pulls?state=all"
        prs = requests.get(pr_url, auth=(GITHUB_USERNAME, GITHUB_TOKEN)).json()
        if not isinstance(prs, list):
            continue
        for pr in prs:
            if pr.get('merged_at'):
                pr_number = pr['number']
                pr_title = pr['title']
                merged_by = pr.get('merged_by', {}).get('login', 'Unknown') if pr.get('merged_by') else "Unknown"
                reviews_url = f"{GITHUB_API_URL}/repos/{GITHUB_USERNAME}/{repo}/pulls/{pr_number}/reviews"
                reviews = requests.get(reviews_url, auth=(GITHUB_USERNAME, GITHUB_TOKEN)).json()
                has_approval = False
                if isinstance(reviews, list):
                    for review in reviews:
                        if review.get('state') == 'APPROVED':
                            has_approval = True
                            break
                if not has_approval:
                    merged_date = datetime.strptime(pr['merged_at'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')
                    prs_without_approval.append({
                        'pr_id': pr_number,
                        'title': pr_title,
                        'merged_by': merged_by,
                        'merged_date': merged_date,
                        'reviews': [],
                        'repo': repo
                    })
    return prs_without_approval

def get_recent_prs(repo_name, hours=24):
    url = f"{GITHUB_API_URL}/repos/{GITHUB_USERNAME}/{repo_name}/pulls?state=open"
    response = requests.get(url, auth=(GITHUB_USERNAME, GITHUB_TOKEN))
    if response.status_code != 200:
        return [f"Error: {response.status_code} - {response.text}"]
    prs = response.json()
    recent_prs = []
    now = datetime.now(timezone.utc)
    for pr in prs:
        created_at = datetime.strptime(pr['created_at'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        waiting_time = (now - created_at).total_seconds() / 3600
        if waiting_time <= hours:
            recent_prs.append({
                "id": pr["id"],
                "title": pr["title"],
                "created_at": pr["created_at"],
                "review_requested": [r['login'] for r in pr.get("requested_reviewers", [])],
                "waiting_time_hours": round(waiting_time, 2)
            })
    return recent_prs

def handle_query(user_query):
    prompt = f"""
    You are an assistant that helps with GitHub queries.
    Classify the user's intent as one of:
    - list_repos
    - repo_details
    - pr_reviews
    - prs_by_user
    - prs_no_approval
    - recent_prs
    Extract parameters accordingly.
    User query: "{user_query}"
    Respond ONLY in strict JSON format:
    {{
        "intent": "list_repos" or "repo_details" or "pr_reviews" or "prs_by_user" or "prs_no_approval" or "recent_prs",
        "repo_name": "<repo_name>" or null,
        "reviewer_name": "<reviewer_name>" or null,
        "username": "<username>" or null
    }}
    """
    gemini_resp = gemini_model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
    try:
        parsed = json.loads(gemini_resp.text)
        intent = parsed.get("intent")
        repo_name = parsed.get("repo_name")
        reviewer_name = parsed.get("reviewer_name")
        username = parsed.get("username")
    except Exception as e:
        return f"Parsing failed: {e}\nRaw response: {gemini_resp.text}"

    if intent == "list_repos":
        repos = get_repos()
        return f"Your GitHub repositories:\n- " + "\n- ".join(repos)
    elif intent == "repo_details":
        if not repo_name:
            return "Please specify the repository name."
        details = get_repo_details(repo_name)
        response = f"Repository '{repo_name}' details:\n"
        response += f"- Description: {details['description']}\n"
        response += f"- PR count: {details['pr_count']}\n"
        response += f"- Branches: {', '.join(details['branches'])}\n"
        response += f"- Stars: {details['stars']}\n"
        response += f"- Forks: {details['forks']}\n"
        response += f"- README (first 200 chars): {details['readme']}"
        return response
    elif intent == "pr_reviews":
        if not reviewer_name:
            return "Please specify the reviewer name."
        reviews = get_pr_reviews_by_reviewer(reviewer_name)
        if not reviews:
            return f"No PR reviews found for {reviewer_name}."
        response = f"PRs reviewed by {reviewer_name}:\n\nPR ID | Title | Reviewer | Decision | Date | Repo\n------|-------|----------|----------|------|-----\n"
        for review in reviews:
            response += f"{review['pr_id']} | {review['title']} | {review['reviewer']} | {review['decision']} | {review['date']} | {review['repo']}\n"
        return response
    elif intent == "prs_by_user":
        if not username:
            return "Please specify the username."
        prs = get_prs_by_user(username)
        if not prs:
            return f"No PRs found created by {username}."
        response = f"PRs created by {username}:\n\nPR ID | Title | Author | State | Date | Repo\n------|-------|--------|-------|------|-----\n"
        for pr in prs:
            response += f"{pr['pr_id']} | {pr['title']} | {pr['author']} | {pr['state']} | {pr['date']} | {pr['repo']}\n"
        return response
    elif intent == "prs_no_approval":
        prs = get_prs_merged_without_approval()
        if not prs:
            return "No PRs found that were merged without approval."
        response = f"Found {len(prs)} PR(s) merged without approval:\n\nPR ID | Title | Merged By | Merged Date | Reviews | Repo\n------|-------|-----------|-------------|---------|-----\n"
        for pr in prs:
            response += f"{pr['pr_id']} | {pr['title']} | {pr['merged_by']} | {pr['merged_date']} | {pr['reviews']} | {pr['repo']}\n"
        return response
    elif intent == "recent_prs":
        if not repo_name:
            return "Please specify the repository name."
        prs = get_recent_prs(repo_name, hours=24)
        if not prs:
            return f"No PRs in '{repo_name}' waiting less than 24h."
        response = f"Recent PRs in '{repo_name}' (<24h):\n"
        for pr in prs:
            response += f"- ID: {pr['id']}, Title: {pr['title']}, Created: {pr['created_at']}, Reviewers: {pr['review_requested']}, Waiting: {pr['waiting_time_hours']}h\n"
        return response
    else:
        return f"Sorry, I couldn't understand your query.\nRaw: {gemini_resp.text}"

st.set_page_config(page_title="GitHub Evidence Bot", page_icon="🛠️", layout="wide")
st.title("🛠️ AI-Powered GitHub Evidence Bot")
st.markdown("Ask questions about your GitHub repositories in natural language.")

user_query = st.text_input("Enter your query:")

if st.button("Submit") and user_query:
    with st.spinner("Processing your query..."):
        try:
            result = handle_query(user_query)
            st.success("Query executed successfully!")
            st.text_area("Result", value=result, height=400)
        except Exception as e:
            st.error(f"Error occurred: {e}")

st.markdown("---")
st.markdown("**Sample Queries:**")
st.markdown("""
- List all my GitHub repositories  
- Give me details for repo juice-shop-hackathon  
- Show me all PRs created by anishasatishrao  
- How many PRs were merged without approval?  
- Show me PRs waiting for review less than 24 hours in juice-shop-hackathon  
- Show me PRs reviewed by Alice  
""")


# def handle_excel_laptops():
#     import pandas as pd

#     st.markdown("### 💻 Laptop Inventory Analysis")
#     st.markdown("Upload Excel sheets containing laptop data. Make sure the sheets have columns like 'Laptop' and 'Owner'.")

#     uploaded_files = st.file_uploader("Upload Excel files", type=["xlsx"], accept_multiple_files=True)

#     if uploaded_files:
#         # Read all uploaded Excel files into a single DataFrame
#         df_list = []
#         for file in uploaded_files:
#             try:
#                 df = pd.read_excel(file)
#                 df_list.append(df)
#             except Exception as e:
#                 st.error(f"Error reading {file.name}: {e}")

#         if df_list:
#             all_data = pd.concat(df_list, ignore_index=True)

#             # Ensure required columns exist
#             if 'Laptop' not in all_data.columns or 'Owner' not in all_data.columns:
#                 st.error("Excel sheets must contain 'Laptop' and 'Owner' columns.")
#             else:
#                 # Button: Total laptop count
#                 if st.button("Get total laptop count"):
#                     total_laptops = all_data['Laptop'].nunique()
#                     st.success(f"Total laptops: {total_laptops}")

#                 # Button: Laptop to owner mapping
#                 if st.button("Show laptop-owner mapping"):
#                     mapping = all_data.groupby('Laptop')['Owner'].apply(list).to_dict()
#                     st.success("Laptop-Owner mapping:")
#                     for laptop, owners in mapping.items():
#                         st.write(f"- {laptop}: {', '.join(owners)}")


# handle_excel_laptops()