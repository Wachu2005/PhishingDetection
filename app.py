from flask import Flask, request, render_template, jsonify
import requests
import subprocess
import json
import re
import os
import pandas as pd
from io import StringIO
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

app = Flask(__name__)



def strings_not_in_first_list(list1, list2):
    set1 = set(list1)
    set2 = set(list2)

    difference = set2 - set1

    return list(difference)


url = "https://phishstats.info/phish_score.csv" # Get the latest 100 records

def get_phishing_data(api_url="https://phishstats.info/phish_score.csv"):
    response = requests.get(api_url)
    if response.status_code == 200:
        csv_data = StringIO(response.text)
        df = pd.read_csv(csv_data, comment='#', header=None)
        df.columns = ['Date', 'Score', 'URL', 'IP']
        return list(df['URL'])
    else:
        return 'Error with csv'


# def format_json_response(json_response):
#     if not isinstance(json_response, dict):
#         return "Invalid response format."

#     success = json_response.get('success', False)
#     message = json_response.get('message', 'No message provided.')
#     data = json_response.get('data', {})

#     response_str = f"Success: {'Yes' if success else 'No'}\n"
#     response_str += f"Message: {message}\n"

#     if data:


#         discovery_date = data.get('discovery_date', 'Unknown')
#         brand = data.get('brand', 'Unknown')
#         response_str += f"Discovery Date: {discovery_date}\n"
#         response_str += f"Brand: {brand}"

#     return response_str

def extract_url(user_input):
    # Enhanced Regular expression pattern for finding URLs
    url_pattern = r'(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})'
    urls = re.findall(url_pattern, user_input)
    if len(urls) > 0:
        return urls[0]
    else:
        return None





def convert_to_simple_text_class(model_response):
    if not model_response or not isinstance(model_response, list):
        return "Invalid response"

    highest_score_entry = max(model_response, key=lambda x: x['score'])
    label = highest_score_entry['label']
    score = highest_score_entry['score']

    # Create a formatted string with class and confidence score
    formatted_result = f"Class: {label}, Confidence Score: {score:.4f}"
    
    return formatted_result


def get_model_response(user_input):
    API_TOKEN = "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"
    api_url = "https://api-inference.huggingface.co/models/ealvaradob/bert-finetuned-phishing"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.post(api_url, headers=headers, json={"inputs": user_input})
    model_response = response.json()
    print(model_response)
    try:
        response = convert_to_simple_text_class(model_response[0])
    except:
        return model_response
    return response

# def run_pyopdb_script(url):

#     command = ['python', 'pyopdb.py', '--checkurl', url]

#     # Run the subprocess as before
#     process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
#     output, error = process.communicate()

#     if error:
#         return {'success': False, 'error': error.strip()}

#     try:
#         return json.loads(output)
#     except json.JSONDecodeError:
#         return {'success': False, 'error': 'Invalid JSON output'}


def check_in_database(data, url):
    print(url)
    if url in data:
        return "URL is Phishing"
    else:
        return "URL is Safe (Not Found in Database)"



global_data = None
path = "/Users/Wacha/Desktop/Phishing/phishing.csv"
data_check = pd.read_csv(path,  error_bad_lines=False, nrows=50000, warn_bad_lines=False) 
data_check = list(data_check['id'])

def get_phishing_data(api_url="https://phishstats.info/phish_score.csv"):
    global global_data
    global data_check
    response = requests.get(api_url)
    if response.status_code == 200:
        csv_data = StringIO(response.text)
        df = pd.read_csv(csv_data, comment='#', header=None)
        df.columns = ['Date', 'Score', 'URL', 'IP']
        if global_data is None:
            global_data = list(df['URL'])
            data_check = global_data + data_check
            print(type(data_check))
        else:
            difference = strings_not_in_first_list(global_data, list(df['URL']))
            print(len(difference))
            global_data = list(df['URL'])
            data_check = difference + data_check
    else:
        global_data = None



@app.route('/', methods=['GET', 'POST'])
def index():
    global data_check
    print(len(data_check))
    model_response = ''
    url_check_result = ''
    if request.method == 'POST':
        user_input = request.form.get('user_input')
        url = extract_url(user_input)

        if url:
            url_check_result = check_in_database(data_check, url)
        else:
            url_check_result = "No URL"


        if user_input:
            model_response = get_model_response(user_input)


        return render_template('index.html', model_response=model_response, url_check_result=url_check_result)
    return render_template('index.html', model_response=model_response, url_check_result=url_check_result)

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=get_phishing_data, trigger="interval", minutes=90)
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    get_phishing_data()  # Initial call at startup
    start_scheduler()    # Start the scheduler
    app.run(debug=True)