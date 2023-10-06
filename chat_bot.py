import json
import os
import time
from datetime import datetime

import openai
from text_to_speech import text_to_speech

from services.document_embedding import doc_agent
from services.google_interface import google_agent
from USDChat.utils.speech_thread import SpeechThread

openai.api_key = os.getenv("OPENAI_API_KEY")


# Chat agent
class Chat:
    def __init__(
        self,
        model,
        system="You are USDChat helpful expert in Pixar OpenUSD and an advanced Computer Graphics AI assistant!\
                USDChat is an expert Pixar OpenUSD and an advanced Computer Graphics AI assistant.\
                You can code, chat, edit 3D scenes, get stage information and interact with usdview. \
                Above all you enjoy solving problmes, having interesting, intellectually stimulating \
                conversations.",
        max_tokens=500,
        speech=False,
        temp=0.7,
    ):
        self.model = model
        self.speech = speech
        self.system = system
        self.max_tokens = max_tokens
        self.temp = temp
        self.message_history = []

    def __str__(self):
        name = "Chat Agent [" + self.model + "]"
        return name

    def reinsert_system_message(self, messages):
        if len(messages) == 0 or (
            len(messages) > 0 and messages[0].get("role") != "system"
        ):
            messages.insert(0, {"role": "system", "content": self.system})
        return messages

    def chat(self, messages):
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        completion = openai.ChatCompletion.create(
            model=self.model,
            temperature=self.temp,
            max_tokens=self.max_tokens,
            messages=messages,
        )
        reply_content = completion.choices[0].message.content
        return reply_content

    def stream_chat(self, messages, delay_time=0.1):
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        response = openai.ChatCompletion.create(
            model=self.model,
            temperature=self.temp,
            max_tokens=self.max_tokens,
            messages=messages,
            stream=True,
        )
        reply_content = ""
        for event in response:
            event_text = event["choices"][0]["delta"]
            new_text = event_text.get("content", "")
            reply_content += new_text
            if self.speech:
                speech_thread = SpeechThread(new_text)
                speech_thread.start()
            yield new_text
            time.sleep(delay_time)

        return reply_content


# Allows saving of message history to file for later retrival
def write_message_history_to_file(full_message_history, directory):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"message_history_{timestamp}.json"
    # Create the directory if it doesn't exist
    if not os.path.exists(directory):
        os.makedirs(directory)
    file_path = os.path.join(directory, filename)
    with open(file_path, "w") as outfile:
        json.dump(full_message_history, outfile, indent=2)


def is_exec_needed(prompt):
    keywords = [
        "play",
        "spotify",
        "volume",
        "next",
        "next song",
        "pause",
        "resume",
        "unpause",
        "playing",
        "music",
        "song",
        "send an email",
        "email",
        "sms",
        "text",
        "message",
        "analyze",
        "summarize",
        "folder",
        "directory",
    ]
    prompt = prompt.lower().strip()
    for keyword in keywords:
        if keyword in prompt:
            return True
    return False


class Executive:
    def __init__(self, model):
        self.model = model

    def __str__(self):
        name = "Executive Agent [" + self.model + "]"
        return name

    def identify_task(self, prompt):
        # Dictionary used to call functions depending on output of executive
        agent_dict = {
            "send_email": send_email,
            "spotify_agent": spotify_agent,
            "send_sms": sms_agent,
            "analyze_documents": doc_agent,
        }
        completion = openai.ChatCompletion.create(
            model=self.model,
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": "You analyze user input, and output the names of functions to fullfil a user's needs.\
                      The spotify_agent can search for music or artists, play and pause songs, or go to the next song. \
                     If the user just says, 'pause' or 'next song' or 'volume to x' that means the spotify_agent is needed. \
                     You can output: ['send_email', 'spotify_agent', 'send_sms', 'analyze_documents'] to fulfill a request, otherwise reply: 'chat'",
                },
                {"role": "user", "content": prompt},
            ],
        )
        reply_content = completion.choices[0].message.content
        if any(
            command in reply_content
            for command in [
                "send_email",
                "spotify_agent",
                "send_sms",
                "analyze_documents",
            ]
        ):
            agent_response = agent_dict[reply_content](prompt)
            # Response is status recieved from agent attempting to a complete
            # task.
            return agent_response
        else:
            return False  # False means default to chat


def gpt4_exec(user_input):
    completion = openai.ChatCompletion.create(
        model="gpt-4",
        temperature=0,
        max_tokens=10,
        messages=[
            {
                "role": "system",
                "content": "Analyze user input, and output the name of function to fullfil a user's needs.\
                    # The spotify_agent command can play and pause songs on the user's computer, or go to the next song. \
                    # If the user just says, 'pause' or 'next song' or 'volume to x' that means the spotify_agent is needed. \
                    # Only call the spotify_agent if the user actually want to play music, not just talk about it. \
                    # The send_email command will let a user send an email. The send_sms command will let a user send an SMS message.\
                    The analyze_documents command will let a user analyze a document or the contents of a folder. \
                    If none of these commands are needed, reply only with 'chat'. If it is unclear, reply with 'chat'\
                    You are only allowed to output one command.\
                    The only commands you are allowed to output are: \
                    'analyze_documents', or 'chat'. Do not reply with any other output.",
            },
            {"role": "user", "content": user_input},
        ],
    )
    reply_content = completion.choices[0].message.content

    if "analyze_documents" in reply_content:
        agent_response = doc_agent(user_input)
        return agent_response
    else:
        google_search_result = google_agent(user_input)
        return google_search_result


def main():
    try:
        print("Welcome to USDChat interface!")
        print("Type 'quit' to exit the chat.\n")
        speech = True
        message_history = []
        full_message_history = []
        system_message = "You are USDChat. USDChat is an expert Pixar OpenUSD and an advanced Computer Graphics AI assistant.\
                        You can code, chat, edit 3D scenes, get stage information and interact with usdview. \
                        Above all you enjoy solving problmes, having interesting, intellectually stimulating \
                        conversations."
        max_history = (
            100  # Adjust this value to limit the number of messages considered
        )

        while True:
            user_input = input("You: ")
            if user_input.lower() == "quit":
                write_message_history_to_file(
                    full_message_history, "./message_logs")
                break
            else:
                message_history.append({"role": "user", "content": user_input})
                full_message_history.append(
                    {"role": "user", "content": user_input})
                # reduces messages when max history exceeded
                if len(message_history) > max_history:
                    message_history = [message_history[0]] + message_history[
                        -(max_history - 1):
                    ]  # Keep the system message and remove the second message
                # Check user input, if executive is needed, call executive on
                # user input and return result.
                agent_response = gpt4_exec(message_history[-1].get("content"))
                if not agent_response:
                    print("\nUSDChat: ", end="", flush=True)
                    gpt4_chat = Chat(
                        "gpt-4", system=system_message, speech=speech)
                    response = gpt4_chat.stream_chat(message_history)
                    message_history.append(
                        {"role": "assistant", "content": response})
                    full_message_history.append(
                        {"role": "assistant", "content": response}
                    )
                    print(f"\n")
                else:
                    if isinstance(
                        agent_response, list
                    ):  # Handling the case when the agent returns a list of responses
                        for i, response in enumerate(agent_response):
                            message_history.append(response)
                            full_message_history.append(response)
                            # Print only the most recent answer
                            if i == len(agent_response) - 1:
                                print(response["content"])
                                if speech:
                                    text_to_speech(response["content"])
                    # Handling the case when the agent returns a single
                    # response (string)
                    else:
                        message_history.append(
                            {"role": "assistant", "content": agent_response}
                        )
                        full_message_history.append(
                            {"role": "assistant", "content": agent_response}
                        )
                        agent_response
                        print(f"\n")
                        if speech:
                            text_to_speech(response["content"])

    except KeyboardInterrupt:
        print("\nDetected KeyboardInterrupt. Saving message history and exiting.")
    except Exception as e:
        print(f"\nAn error occurred: {e}. Saving message history and exiting.")
    finally:
        write_message_history_to_file(full_message_history, "./message_logs")
        print("Message history saved.")


if __name__ == "__main__":
    main()
