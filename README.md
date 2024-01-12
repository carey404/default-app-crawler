# Default Apps Data Collection Script

## Overview
This Python script is designed to parse a specified RSS feed containing links to blog posts where authors list their preferred or 'default' applications for various categories. It automates the process of extracting these preferences and compiling them into a structured CSV file. The script uses OpenAI’s GPT model to interpret and categorize the data from each blog post.

## Prerequisites
- Python 3.x
- Libraries: requests, beautifulsoup4, openai, csv, dotenv
- An OpenAI API key

## Setup
1. Install Python Dependencies: Run pip install requests beautifulsoup4 openai python-dotenv to install the necessary Python packages.
2. Environment Variables: Place your OpenAI API key in a .env file at the root of the project with the variable name OPENAI_API_KEY.

## Usage
1. Specify RSS Feed URL: Modify the rss_url variable in the main() function to the desired RSS feed URL.
2. Run the Script: Execute the script with python script_name.py. The script will read the RSS feed, visit each blog post, extract the content, and send it to the OpenAI API for processing.
3. Output: The script will generate a CSV file named default_apps_results.csv with the structured data.

## Features
- RSS Feed Parsing: Extracts links and titles from the given RSS feed.
- Content Extraction: Visits each blog post and extracts relevant content.
- Data Analysis with OpenAI: Utilizes OpenAI's GPT model to analyze and categorize the content of each blog post.
- CSV File Generation: Produces a well-structured CSV file containing the default applications mentioned in each blog post, categorized by the author.

## Limitations and Considerations
- Token Limits: The script is designed to manage token limits set by the OpenAI API.
- Error Handling: Includes robust error handling for network issues and API limits.
- Customizable Categories: Users can modify the common_categories list to focus on specific categories of interest.
