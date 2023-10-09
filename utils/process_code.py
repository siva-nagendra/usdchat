import io
import logging
import re
import sys
from code import InteractiveConsole as Console


def extract_python_code(text):
    logging.info("Extracting Python code blocks from the text.")
    python_code_blocks = re.findall(r"```python\n(.*?)```", text, re.DOTALL)
    logging.info(f"Extracted Python code blocks: {python_code_blocks}")
    return python_code_blocks


def process_chat_responses(messages, usdviewApi):
    logging.info("Processing chat responses.")

    if not isinstance(messages, list):
        messages = [messages]

    accumulated_text = ""
    all_code_blocks = []

    for message in messages:
        logging.info(f"Processing message: {message}")
        accumulated_text += message

    python_code_snippets = extract_python_code(accumulated_text)
    if python_code_snippets:
        all_code_blocks.extend(python_code_snippets)
        final_code = "\n".join(all_code_blocks)
        logging.info(f"Final code to be executed: {final_code}")
        code_to_run = f'''exec("""\n{final_code}\n""")'''

        logging.info(f"Processed code: {code_to_run}")
        print("code_to_run", code_to_run)

        output, success = execute_python_code(
            final_code, usdviewApi
        )  # Capture both output and success flag

        return output, success  # Return both output and success flag

    return (
        accumulated_text,
        True,
    )  # No code was executed, so technically, it's a "success"


def execute_python_code(code_to_run, usdviewApi):
    logging.info(
        "Attempting to execute Python code in usdview's Python environment.")

    # Initialize a StringIO buffer to capture stdout and stderr
    old_stdout, old_stderr = sys.stdout, sys.stderr
    new_stdout, new_stderr = io.StringIO(), io.StringIO()
    sys.stdout, sys.stderr = new_stdout, new_stderr

    python_console = Console()
    python_console.locals["usdviewApi"] = usdviewApi

    logging.info(f"Code being passed to interpreter: {code_to_run}")

    # Execute the code
    python_console.runcode(code_to_run)

    # Restore original stdout and stderr
    sys.stdout, sys.stderr = old_stdout, old_stderr

    # Get the content of the redirected stdout and stderr
    stdout_content = new_stdout.getvalue()
    stderr_content = new_stderr.getvalue()

    # Close the StringIO objects
    new_stdout.close()
    new_stderr.close()

    if stderr_content:
        logging.error(f"Error in code execution: {stderr_content}")
        return f"Error: {stderr_content}", False
    else:
        logging.info("Code executed successfully.")
        return stdout_content, True