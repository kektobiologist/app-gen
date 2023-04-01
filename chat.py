import requests
import json
import re
import os
import time
import sys
from multiprocessing.pool import ThreadPool

API_ENDPOINT = "https://api.openai.com/v1/chat/completions"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
from prompts import SYSTEM_PROMPT_BE_FE_EDIT_SELECTOR, SYSTEM_PROMPT_FRONTEND, SYSTEM_PROMPT_BACKEND, SYSTEM_PROMPT_DIRECTORY

def extract_code_blocks(text, suffix=None):
    # if no suffix, then we can do any pattern matching. otherwise, we need to match the suffix
    if suffix is None:
        code_blocks = re.findall(r'```(?:[a-zA-Z]+\s)?(.*?)```', text, flags=re.MULTILINE | re.DOTALL)
    else:
        # match ```<suffix> (code block)```
        code_blocks = re.findall(r'```' + suffix + r'\s(.*?)```', text, flags=re.MULTILINE | re.DOTALL)
    return code_blocks


def generate_chat_completion(messages, model="gpt-4", temperature=1, max_tokens=2048):
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

    response = requests.post(API_ENDPOINT, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        return response.json()
#         return response.json()["choices"][0]["message"]["content"]
    else:
        raise Exception(f"Error {response.status_code}: {response.text}")

def create_frontend_from_response(response_text, app_name):
    output_html = response_text['choices'][0]['message']['content']
    parsed_output_html = extract_code_blocks(output_html)[0]
    write_code_to_file(parsed_output_html, f"{app_name}/templates/index.html")
    return parsed_output_html

def read_frontend(app_name):
    f = open(f"{app_name}/templates/index.html", "r")
    current_code = f.read()
    f.close()
    current_code = "```html\n" + current_code + "\n```"
    return current_code

def write_code_to_file(code, filename):
    f = open(filename, "w")
    f.write(code)
    f.close()
    
def create_backend_from_response(response_text_backend, app_name):
    output_python = response_text_backend['choices'][0]['message']['content']
    parsed_output_python = extract_code_blocks(output_python)[0]
    write_code_to_file(parsed_output_python, f"{app_name}/app.py")
    return parsed_output_python


VERBOSE = 0
def generate_frontend_from_scratch(MASTER_PROMPT, app_name):
    USER_PROMPT = f"""
    {MASTER_PROMPT}
    """

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_FRONTEND},
        {"role": "user", "content": USER_PROMPT}
    ]

    response_text = generate_chat_completion(messages)
    out = create_frontend_from_response(response_text, app_name)
    if VERBOSE:
        print ("Parsed Frontend code: \n")
        print (out)
    return response_text

def generate_frontend_from_iteration(MASTER_PROMPT, app_name, EDIT_MESSAGE):
    USER_PROMPT = f"""
    {MASTER_PROMPT}
    """
    
    current_code = read_frontend(app_name)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_FRONTEND},
        {"role": "user", "content": USER_PROMPT},
        {"role": "assistant", "content": current_code},
        {"role": "user", "content": EDIT_MESSAGE},
    ]

    response_text = generate_chat_completion(messages)
    out = create_frontend_from_response(response_text, app_name)
    if VERBOSE:
        print ("Parsed Frontend code: \n")
        print (out)
    return response_text

def generate_backend_from_frontend(MASTER_PROMPT, app_name):
    ## This takes input as the frontend code and generate the corresponding flask app for it

    USER_PROMPT_BACKEND = f"""
    {MASTER_PROMPT}
    The corresponding frontend code is:
    """

    messages_backend = [
        {"role": "system", "content": SYSTEM_PROMPT_BACKEND},
        {"role": "user", "content": USER_PROMPT_BACKEND + read_frontend(app_name)}
    ]

    response_text_backend = generate_chat_completion(messages_backend)
    out = create_backend_from_response(response_text_backend, app_name)
    if VERBOSE:
        print ("Parsed Backend code: \n")
        print (out)
    return response_text_backend

def parse_app_name_and_directories(response):
    response_text = response['choices'][0]['message']['content']
    # get the first codeblock that is between ```bash and ```
    app_name_blocks = extract_code_blocks(response_text, 'app')
    app_name = app_name_blocks[0]
    bash_commands_blocks = extract_code_blocks(response_text, 'bash')
    bash_commands = bash_commands_blocks[0]
   
    return app_name, bash_commands

def generate_app_name_and_directories(MASTER_PROMPT):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_DIRECTORY},
        {"role": "user", "content": MASTER_PROMPT}
    ]

    response = generate_chat_completion(messages)
    app_name, bash_commands =  parse_app_name_and_directories(response)
    if VERBOSE:
        print(app_name)
        print(bash_commands)
    # create the directories
    os.system(bash_commands)
    return app_name

# MASTER_PROMPT = """
# Create a Text tokenizing app. Use NLTK tokenizers.
# We will need routes to upload text, process it and show it back on the frontend.
# """

keep_animating = True

def show_loading_animation():
    start_time = time.time()
    while keep_animating:
        # show time elapsed in seconds, one decimal point
        sys.stdout.flush()
        # print in grey
        print("\033[90mThinking ... " + str(round(time.time() - start_time, 1)) + "s", end="\r\033[0m")
        time.sleep(0.1)

def print_grey_message(msg):
    print (f"\033[90m{msg}\033[0m")

def thinking_start():
    global keep_animating
    keep_animating = True
    async_result = pool.apply_async(show_loading_animation)
def thinking_stop():
    global keep_animating
    keep_animating = False
    

# main
pool = ThreadPool(1)
# get master prompt from user
# print a greeting to terminal, in greyed text
GREETING = "Hi, what would you like to create?"
print_grey_message(GREETING)
MASTER_PROMPT = input("==> ")
thinking_start()
app_name = generate_app_name_and_directories(MASTER_PROMPT).strip()
thinking_stop()
print_grey_message(f"Cool I'll generate the {app_name} app for you.")
thinking_start()
# generate frontend
response_text = generate_frontend_from_scratch(MASTER_PROMPT, app_name)
# generate backend
response_text_backend = generate_backend_from_frontend(MASTER_PROMPT, app_name)
# sleep 2 seconds
# time.sleep(2)
thinking_stop()
DONE_MESSAGE = "\nDone. What next?"
# print in grey again
print_grey_message(DONE_MESSAGE)
# enter editing loop
while True:
    EDIT_MESSAGE = input("==> ")
    if EDIT_MESSAGE == "exit":
        break
    thinking_start()
    response_text = generate_frontend_from_iteration(MASTER_PROMPT, app_name, EDIT_MESSAGE)
    response_text_backend = generate_backend_from_frontend(MASTER_PROMPT, app_name)
    thinking_stop()
    print_grey_message(DONE_MESSAGE)
