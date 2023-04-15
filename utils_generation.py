from constants import *
from utils import (generate_chat_completion,
    create_backend_from_response, create_frontend_from_response,
    read_frontend, read_backend)

from prompts import SYSTEM_PROMPT_FRONTEND, SYSTEM_PROMPT_BACKEND

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

def generate_backend_from_iteration(MASTER_PROMPT, app_name, EDIT_MESSAGE):
    USER_PROMPT = f"""
    {MASTER_PROMPT}
    """
    
    current_code = read_backend(app_name)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_BACKEND},
        {"role": "user", "content": USER_PROMPT},
        {"role": "assistant", "content": current_code},
        {"role": "user", "content": EDIT_MESSAGE},
    ]

    response_text = generate_chat_completion(messages)
    out = create_backend_from_response(response_text, app_name)
    if VERBOSE:
        print ("Parsed Backend code: \n")
        print (out)
    return response_text
