import csv
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import os
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
            return ""x
    except SSLError as e:
        print(f"SSL Error fetching {url}: {e}")
        return ""
    except RequestException as e:
        print(f"Error fetching {url}: {e}")
        return ""

def estimate_token_count(text):
    return len(text.split())

def validate_with_openai(client, content, csv_data):
    # Explicitly list all categories for the response format
    categories_example = {
        "Mail": "MailApp",
        "Calendar": "CalendarApp",
        "Browser": "BrowserApp",
        "Password Manager": "PasswordManagerApp",
        "Messaging": "MessagingApp",
        "Notes": "NotesApp",
        "Cloud File Storage": "CloudStorageApp",
        "To-Do": "ToDoApp",
        "Code Editor": "CodeEditorApp",
        "Terminal": "TerminalApp",
        "Blogging": "BloggingApp",
        "Launcher": "LauncherApp"
    }

    # Construct a detailed prompt
    prompt = ("Below is a list of categories and applications from a blog post, and the content of the blog post. "
              "Create a JSON object that validates each category and application against the blog post content. "
              "If a category and application match the content, include them as-is in the JSON object. "
              "If they do not match, prefix the application name with 'XXX'. "
              "Ensure that every category is listed in the response, even if the application name is left blank. "
              "Example response format: "
              f"{categories_example} "
              "Here are the categories and applications: "
              f"{csv_data} "
              "And here is the content of the blog post: "
              f"{content} >>>")

    try:
        response = client.chat_completion(prompt)
        # Parse the JSON-formatted response
        # Depending on how OpenAI formats the response, you may need a json.loads() here
        validation_results = eval(response)  # Be cautious with eval, ensure the response is safe
        return validation_results
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return {}



def read_csv(filename):
    with open(filename, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        return list(reader)

def write_to_csv(filename, data):
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

def main():
    input_filename = "default_apps_results.csv"
    output_filename = "validated_apps_results.csv"
    ai_client = OpenAIClient("gpt-3.5-turbo")
    rows = read_csv(input_filename)
    validated_rows = []

    for row in rows:
        url = row['Webpage']
        print(f"Validating: {url}")
        post_content = extract_post_content(url)
        if post_content:
            validation_results = validate_with_openai(ai_client, post_content, row)
            # Update the row based on validation results
            # This step needs to be customized based on the structure of the validation results
            for category in row.keys():
                if category not in ['Author', 'Webpage']:
                    if validation_results[category] != row[category]:
                        row[category] = f"XXX{row[category]}"
            validated_rows.append(row)

    write_to_csv(output_filename, validated_rows)

if __name__ == "__main__":
    main()
