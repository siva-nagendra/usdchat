import os
import inspect


def get_file_from_current_path(filename):
    current_file_path = os.path.abspath(__file__)
    current_dir_path = os.path.dirname(current_file_path)
    req_path = os.path.join(current_dir_path, filename)
    return req_path


def get_model():
    return "gpt-4"
