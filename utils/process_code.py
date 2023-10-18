import importlib
import io
import logging
import re
import sys
from code import InteractiveConsole as Console

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

sub_modules = [
    "Tf",
    "Gf",
    "Trace",
    "Work",
    "Plug",
    "Vt",
    "Ar",
    "Kind",
    "Sdf",
    "Ndr",
    "Sdr",
    "Pcp",
    "Usd",
    "UsdGeom",
    "UsdVol",
    "UsdMedia",
    "UsdShade",
    "UsdLux",
    "UsdProc",
    "UsdRender",
    "UsdHydra",
    "UsdRi",
    "UsdSkel",
    "UsdUI",
    "UsdUtils",
    "UsdPhysics",
    "UsdMtlx",
    "Garch",
    "CameraUtil",
    "PxOsd",
    "GeomUtil",
    "Glf",
    "UsdImagingGL",
    "UsdAppUtils",
    "Usdviewq",
    "UsdBakeMtlx",
]


def extract_python_code(text):
    logger.info("Extracting Python code blocks from the text.")
    python_code_blocks = re.findall(r"```python\n(.*?)```", text, re.DOTALL)
    logger.info(f"Extracted Python code blocks: {python_code_blocks}")
    return python_code_blocks


def process_chat_responses(messages, usdviewApi):
    logger.info("Processing chat responses.")

    if not isinstance(messages, list):
        messages = [messages]

    accumulated_text = ""
    all_code_blocks = []

    for message in messages:
        logger.info(f"Processing message: {message}")
        accumulated_text += message

    python_code_snippets = extract_python_code(accumulated_text)
    if python_code_snippets:
        all_code_blocks.extend(python_code_snippets)
        final_code = "\n".join(all_code_blocks)
        logger.info(f"Final code to be executed: {final_code}")
        code_to_run = f'''exec("""\n{final_code}\n""")'''

        logger.info(f"Processed code: {code_to_run}")

        output, success = execute_python_code(final_code, usdviewApi)

        return output, success

    return (
        accumulated_text,
        True,
    )


def execute_python_code(code_to_run, usdviewApi):
    logger.info(
        "Attempting to execute Python code in usdview's Python environment.")

    old_stdout, old_stderr = sys.stdout, sys.stderr
    new_stdout, new_stderr = io.StringIO(), io.StringIO()
    sys.stdout, sys.stderr = new_stdout, new_stderr

    python_console = Console()
    python_console.locals["usdviewApi"] = usdviewApi

    # Dynamically import modules and add them to python_console.locals
    for sub_module in sub_modules:
        try:
            module = importlib.import_module(f"pxr.{sub_module}")
            python_console.locals[sub_module] = module
        except ImportError:
            logger.warning(f"Failed to import {sub_module}")

    logger.info(f"Code being passed to interpreter: {code_to_run}")

    python_console.runcode(code_to_run)

    sys.stdout, sys.stderr = old_stdout, old_stderr

    stdout_content = new_stdout.getvalue()
    stderr_content = new_stderr.getvalue()

    new_stdout.close()
    new_stderr.close()

    if stderr_content:
        logger.error(f"Error in code execution: {stderr_content}")
        return f"Error: {stderr_content}", False
    else:
        logger.info("Code executed successfully.")
        return stdout_content, True
