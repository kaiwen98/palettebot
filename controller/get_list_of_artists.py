import os
import re

from utils.commons import DIR_OUTPUT

def process_string_name(inp_str):
    output = inp_str
    if re.search(r'_[0-9]\.[0-9a-zA-Z]+', inp_str):
        output = os.path.splitext(output)[0][:output.rfind("_")]
    elif re.search(r'.[0-9a-zA-Z]+', inp_str):
        output = os.path.splitext(output)[0]
    else:
        output = inp_str
    return output.replace("[Instagram] ", "[Instagram] @").replace("[Twitter] ", "[Twitter] @")

def get_list_of_artists(path):
    result_text = ""
    output = {}

    _dir = os.listdir(path)
    output[dir] = set([process_string_name(i) for i in _dir])
    for i in output[dir]:
        result_text = result_text + i + "\n"
    with open(os.path.join(path, "artists.txt"), "w") as f:
        f.write(result_text)
    return result_text

