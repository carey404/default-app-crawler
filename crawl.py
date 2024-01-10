import os
import time
import csv
import requests
from requests.exceptions import RequestException, SSLError
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve API key from environment variable
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

class OpenAIClient:
    def __init__(self, model_name):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = model_name

    def chat_completion(self, user_message, retries=3, delay=60):
        for attempt in range(retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": user_message}
                    ]
                )
                return response.choices[0].message.content
            except Exception as e:
                if 'rate_limit_exceeded' in str(e) and attempt < retries - 1:
                    print(f"Rate limit exceeded, retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    print(f"OpenAI API error: {e}")
                    return ""
        return ""

def parse_rss_feed(rss_url):
    try:
        response = requests.get(rss_url)
        soup = BeautifulSoup(response.content, features='xml')
        entries = soup.find_all('entry')
        links = [(entry.find('title').text, entry.find('link')['href']) for entry in entries]
        return links
    except RequestException as e:
        print(f"Error parsing RSS feed: {e}")
        return []

def extract_post_content(url):
    if "https://www.wyrd.systems/defaults/" in url:
        print(f"Skipping URL due to known issues: {url}")
        return ""

    try:
        response = requests.get(url, verify=True)
        soup = BeautifulSoup(response.content, 'html.parser')
        content = soup.find('body') or soup.find('article') or soup.find('div')  # Fallbacks
        if content:
            return content.get_text()
        else:
            print(f"Failed to find content in {url}")
            return ""
    except SSLError as e:
        print(f"SSL Error fetching {url}: {e}")
        return ""
    except RequestException as e:
        print(f"Error fetching {url}: {e}")
        return ""

def estimate_token_count(text):
    return len(text.split())

def analyze_post_with_openai(client, content):
    token_limit = 4000
    estimated_tokens = estimate_token_count(content)

    if estimated_tokens > token_limit:
        print(f"Content too large ({estimated_tokens} tokens), trimming to fit token limits.")
        words = content.split()[:token_limit]
        content = ' '.join(words)

    prompt = ("Provided is a blog post where the author lists their most used, or 'default', applications for various categories of software. "
            "Identify the software applications and assign each to one of the following common categories: "
            "Mail, Calendar, Browser, Password Manager, Messaging, Notes, Cloud File Storage, To-Do, Code Editor, Terminal, Blogging, Launcher. "
            "Format the response as 'category_name : application_name'. "
            "If an application does not fit any of the provided categories, do not include it. "
            "Only include the name of the application in the response. "
            "If multiple applications are listed for a category, include only the first application. For example, if 'Slack and Discord' are listed, return 'Slack'. "
            "Exclude any OS-specific information, leaving only the application name. "
            "If the author does not clearly list an application but provides an explanation, leave the application blank. "
            "Focus solely on the software applications mentioned, excluding any hardware-related items or personal opinions. "
            "Double check your work before replying. Ensure that only the category and app name is listed. No other text should be included. "
            "It is very important that you get this right, so take your time and think it through stpe by step >>>" + content)

    try:
        return client.chat_completion(prompt)
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return ""

def write_to_csv(filename, author, link, defaults_dict, common_categories):
    with open(filename, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        row = [author, link] + [defaults_dict.get(category, "") for category in common_categories]
        writer.writerow(row)


def main():
    rss_url = 'https://defaults.rknight.me/feed.xml'
    blog_links = parse_rss_feed(rss_url)
    ai_client = OpenAIClient("gpt-3.5-turbo")
    output_filename = "default_apps_results.csv"

    common_categories = [
        "Mail", "Calendar", "Browser", "Password Manager", "Messaging", "Notes",
        "Cloud File Storage", "To-Do", "Code Editor", "Terminal", "Blogging", "Launcher"
    ]

    with open(output_filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        header = ["Author", "Webpage"] + common_categories
        writer.writerow(header)

    for author, link in blog_links:
        print(f"Processing: {link}")
        post_content = extract_post_content(link)
        if post_content:
            defaults_analysis = analyze_post_with_openai(ai_client, post_content)
            defaults_dict = {}
        for author, link in blog_links:
                print(f"Processing: {link}")
                post_content = extract_post_content(link)
                if post_content:
                    defaults_analysis = analyze_post_with_openai(ai_client, post_content)
                    defaults_dict = {}
                    for item in defaults_analysis.splitlines():
                        print(item)
                        if ":" in item:
                            parts = item.split(":", 1)
                            category = parts[0].strip()
                            apps = parts[1].strip() if len(parts) > 1 else ""
                            if category in common_categories and category not in defaults_dict:
                                defaults_dict[category] = apps.split(",")[0].strip()
                    write_to_csv(output_filename, author, link, defaults_dict, common_categories)

  

if __name__ == "__main__":
    main()
