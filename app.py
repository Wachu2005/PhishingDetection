from flask import Flask, request, render_template, jsonify
import requests
import subprocess
import json
import re
import os

app = Flask(__name__)

def format_json_response(json_response):
    if not isinstance(json_response, dict):
        return "Invalid response format."

    success = json_response.get('success', False)
    message = json_response.get('message', 'No message provided.')
    data = json_response.get('data', {})

    response_str = f"Success: {'Yes' if success else 'No'}\n"
    response_str += f"Message: {message}\n"

    if data:
        discovery_date = data.get('discovery_date', 'Unknown')
        brand = data.get('brand', 'Unknown')
        response_str += f"Discovery Date: {discovery_date}\n"
        response_str += f"Brand: {brand}"

    return response_str

def extract_url(user_input):
    # Regular expression pattern for finding URLs
    url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
    urls = re.findall(url_pattern, user_input)

    # Return the first found URL or None if no URL is found
    return urls[0] if urls else None



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

def run_pyopdb_script(url):

    command = ['python', 'pyopdb.py', '--checkurl', url]

    # Run the subprocess as before
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output, error = process.communicate()

    if error:
        return {'success': False, 'error': error.strip()}

    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return {'success': False, 'error': 'Invalid JSON output'}

@app.route('/', methods=['GET', 'POST'])
def index():
    model_response = ''
    url_check_result = ''
    if request.method == 'POST':
        user_input = request.form.get('user_input')
        url = extract_url(user_input)


        # Get model response
        if user_input:
            model_response = get_model_response(user_input)

        # Check URL
        if url:
            url_json = run_pyopdb_script(url)
            url_check_result = format_json_response(url_json)
        else:
            url_check_result = "No URL"

        return render_template('index.html', model_response=model_response, url_check_result=url_check_result)
    return render_template('index.html', model_response=model_response, url_check_result=url_check_result)

if __name__ == '__main__':
    app.run(debug=True)
