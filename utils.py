import re

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
    f = open(f"{app_name}/templates/index.html", "r")
    current_code = f.read()
    f.close()
    current_code = "```html\n" + current_code + "\n```"
    return current_code

def read_backend(app_name):
    f = open(f"{app_name}/app.py", "r")
    current_code = f.read()
    f.close()
    current_code = "```python\n" + current_code + "\n```"
    return current_code

def create_frontend_from_response(response_text, app_name):
    output_html = response_text['choices'][0]['message']['content']
    parsed_output_html = get_code_from_text(output_html)
    write_code_to_file(parsed_output_html, f"{app_name}/templates/index.html")
    return parsed_output_html

    
def create_backend_from_response(response_text_backend, app_name):
    output_python = response_text_backend['choices'][0]['message']['content']
    parsed_output_python = get_code_from_text(output_python)
    write_code_to_file(parsed_output_python, f"{app_name}/app.py")
    return parsed_output_python