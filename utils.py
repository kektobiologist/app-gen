import re
from constants import *
import time
import requests
import json
import logging

def extract_code_blocks(text, suffix=None):
    # if no suffix, then we can do any pattern matching. otherwise, we need to match the suffix
    if suffix is None:
        code_blocks = re.findall(r'```(?:[a-zA-Z]+\s)?(.*?)```', text, flags=re.MULTILINE | re.DOTALL)
    else:
        # match ```<suffix> (code block)```
        code_blocks = re.findall(r'```' + suffix + r'\s(.*?)```', text, flags=re.MULTILINE | re.DOTALL)
    return code_blocks

def get_code_from_text(text):
    code_blocks = extract_code_blocks(text)
    if len(code_blocks) > 0:
        return code_blocks[0]
    else:
        return text

def write_code_to_file(code, filename):
    f = open(filename, "w")
    f.write(code)
    f.close()


def read_frontend(app_name):
    f = open(f"{BASE_DIRECTORY}/{app_name}/templates/index.html", "r")
    current_code = f.read()
    f.close()
    current_code = "```html\n" + current_code + "\n```"
    return current_code

def read_backend(app_name):
    f = open(f"{BASE_DIRECTORY}/{app_name}/app.py", "r")
    current_code = f.read()
    f.close()
    current_code = "```python\n" + current_code + "\n```"
    return current_code

def create_frontend_from_response(response_text, app_name):
    output_html = response_text['choices'][0]['message']['content']
    parsed_output_html = get_code_from_text(output_html)
    write_code_to_file(parsed_output_html, f"{BASE_DIRECTORY}/{app_name}/templates/index.html")
    return parsed_output_html

    
def create_backend_from_response(response_text_backend, app_name):
    output_python = response_text_backend['choices'][0]['message']['content']
    parsed_output_python = get_code_from_text(output_python)
    write_code_to_file(parsed_output_python, f"{BASE_DIRECTORY}/{app_name}/app.py")
    return parsed_output_python


def generate_chat_completion(messages, model="gpt-4", temperature=0, max_tokens=2048):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }

    data = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }

    if max_tokens is not None:
        data["max_tokens"] = max_tokens

    try:
        logging.info(f"Sending request to {API_ENDPOINT} with data {data}")
        response = requests.post(API_ENDPOINT, headers=headers, data=json.dumps(data))

    except Exception as e:
        print (e)
        logging.info(f"Error: {e}")
        print ("Retrying in 10 seconds...")
        time.sleep(10)
        return generate_chat_completion(messages, model, temperature, max_tokens) # hack TODO: fix this

    if response.status_code == 200:
        logging.info(f"Response: {response.json()}")
        return response.json()
    else:
        print (Exception(f"Error {response.status_code}: {response.text}"))
        logging.info(f"Error {response.status_code}: {response.text}")
        print ("Retrying in 10 seconds...")
        time.sleep(10)
        return generate_chat_completion(messages, model, temperature, max_tokens) # hack TODO: fix this
