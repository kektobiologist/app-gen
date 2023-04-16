import requests
import json
import re
import os
import time
import sys
from multiprocessing.pool import ThreadPool
from utils import get_code_from_text, extract_code_blocks, write_code_to_file, create_frontend_from_response, create_backend_from_response, read_frontend, read_backend, generate_chat_completion
import time
from utils_generation import (generate_frontend_from_scratch, generate_frontend_from_iteration,
    generate_backend_from_frontend, generate_backend_from_iteration)
import fire
from prompts import SYSTEM_PROMPT_BE_FE_EDIT_SELECTOR, SYSTEM_PROMPT_DIRECTORY
from constants import VERBOSE, BASE_DIRECTORY
from generate_directory import generate_app_name_and_directories
import logging

logging.basicConfig(
    filename='deployment.log',
    format='%(asctime)s %(levelname)-8s %(filename)s:%(lineno)s - %(funcName)20s() : %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

def get_edit_prompt_is_frontend_or_backend(MASTER_PROMPT, EDIT_PROMPT):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_BE_FE_EDIT_SELECTOR},
        {"role": "user", "content": f"Initial Prompt: {MASTER_PROMPT}\n Edit Prompt: {EDIT_PROMPT}"},
    ]
    response = generate_chat_completion(messages, model= 'gpt-3.5-turbo')
    response_text = response['choices'][0]['message']['content']
    # get the first codeblock that is between ``` and ```
    code_blocks = extract_code_blocks(response_text)
    # check if first codeblock contains substring 'frontend'
    if len(code_blocks) == 0:
        return None
    if 'frontend' in code_blocks[0]:
        return 'frontend'
    elif 'backend' in code_blocks[0]:
        return 'backend'
    else:
        return None

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

def get_multiline_input():
    lines = []
    while True:
        user_input = input('==> ')

        # 👇️ if user pressed Enter without a value, break out of loop
        if user_input == '':
            break
        else:
            lines.append(user_input + '\n')
    return ''.join(lines)

def generate_both_from_scratch(MASTER_PROMPT, app_name):
    # generate frontend
    response_text = generate_frontend_from_scratch(MASTER_PROMPT, app_name)
    # generate backend
    response_text_backend = generate_backend_from_frontend(MASTER_PROMPT, app_name)
    return response_text, response_text_backend

def generate_both_from_iteration(MASTER_PROMPT, app_name, to_send_edit_message):
    response_text = generate_frontend_from_iteration(MASTER_PROMPT, app_name, to_send_edit_message)
    response_text_backend = generate_backend_from_frontend(MASTER_PROMPT + "\n" + to_send_edit_message, app_name)

def save_history(history):
    json.dump(history, open('last_run.json', 'w'))
    json.dump(history, open(f'{BASE_DIRECTORY}/{history["APP_NAME"]}/last_run.json', 'w'))


pool = ThreadPool(1)

if len(sys.argv) == 1: # Running normally
    # main
    history = {}
    
    # get master prompt from user
    # print a greeting to terminal, in greyed text
    GREETING = "Hi, what would you like to create?"
    print_grey_message(GREETING)
    MASTER_PROMPT = get_multiline_input()
    
    thinking_start()
    app_name = generate_app_name_and_directories(MASTER_PROMPT).strip()
    thinking_stop()
    print_grey_message(f"Cool I'll generate the {app_name} app for you.")
    thinking_start()
    
    response_text, response_text_backend = generate_both_from_scratch(MASTER_PROMPT, app_name)
    # sleep 2 seconds
    # time.sleep(2)
    history["EDIT_MESSAGE"] = []
    history["MASTER_PROMPT"] = MASTER_PROMPT
    history["APP_NAME"] = app_name
    save_history(history)
    logging.info(f"New prompt: {history}")
    thinking_stop()

else: # resuming from checkpoint
    if sys.argv[1] == 'resume':
        history = json.load(open('last_run.json', 'r'))
        MASTER_PROMPT = history["MASTER_PROMPT"]
        app_name = history["APP_NAME"]
        logging.info(f"Loaded prompt: {history}")
    else:
        raise ValueError('First argument can only be "resume"')


DONE_MESSAGE = "\nDone. What next?"
# print in grey again
print_grey_message(DONE_MESSAGE)
all_edit_message = []

# enter editing loop
while True:
    EDIT_MESSAGE = get_multiline_input()
    logging.info("Edit message: " + EDIT_MESSAGE)
    if EDIT_MESSAGE == "exit":
        break
    elif EDIT_MESSAGE.strip() == "":
        continue
    elif EDIT_MESSAGE == "show":
        print (to_send_edit_message)
        continue
    elif EDIT_MESSAGE == "clear":
        print ("Clearing edit history")
        history["EDIT_MESSAGE"] = []
        to_send_edit_message = ""
        continue
    elif EDIT_MESSAGE == "pop":
        print ("Clearing last history")
        history["EDIT_MESSAGE"] = history["EDIT_MESSAGE"][:-1]
        to_send_edit_message = "\n".join(history["EDIT_MESSAGE"])
        continue
    
    thinking_start()
    
    # edit_type = get_edit_prompt_is_frontend_or_backend(MASTER_PROMPT, EDIT_MESSAGE)
    edit_type = EDIT_MESSAGE.split(" ")[0]
    if not (edit_type in ['frontend', 'backend', 'both', 'error']):
        print_grey_message("Looks like you have not mentioned the type of change. Please re-enter your request\n")
        continue
    EDIT_MESSAGE = " ".join(EDIT_MESSAGE.split(" ")[1:])
    thinking_stop()
    history["EDIT_MESSAGE"].append(EDIT_MESSAGE)
    to_send_edit_message = "\n".join(history["EDIT_MESSAGE"])
    
    # We need to decide whether we want to add the edit message to the MASTER_PROMPT

    save_history(history)
    
    if edit_type in ['both']:
        print_grey_message("Looks like you want to edit the whole app.\n")
        thinking_start()
        generate_both_from_iteration(MASTER_PROMPT, app_name, to_send_edit_message)
    elif edit_type in ['frontend']:
        print_grey_message("Looks like you want a frontend edit.\n")
        thinking_start()
        generate_frontend_from_iteration(MASTER_PROMPT, app_name, to_send_edit_message)
    elif edit_type in ['backend', 'error']:
        print_grey_message("Looks like you want a backend edit.\n")
        thinking_start()
        response_text_backend = generate_backend_from_iteration(MASTER_PROMPT, app_name, to_send_edit_message)
    thinking_stop()
    print_grey_message(DONE_MESSAGE)
