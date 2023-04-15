from utils import extract_code_blocks, generate_chat_completion
from constants import VERBOSE
import os
from prompts import SYSTEM_PROMPT_DIRECTORY
from constants import BASE_DIRECTORY

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

    response = generate_chat_completion(messages, model='gpt-3.5-turbo')
    app_name, bash_commands =  parse_app_name_and_directories(response)
    if VERBOSE:
        print(app_name)
        print(bash_commands)
    # create the directories
    os.system(f"cd {BASE_DIRECTORY} &&" + bash_commands)
    return app_name