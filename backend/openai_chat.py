import tiktoken
from config import OPENAI_API_KEY
from openai import OpenAI


def num_tokens_from_messages(messages, model='gpt-4o'):
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
        num_tokens = 0
        for message in messages:
            num_tokens += 4
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":
                    num_tokens += -1
        num_tokens += 2
        return num_tokens
    except Exception:
        raise NotImplementedError(
            f"num_tokens_from_messages() is not presently implemented for model {model}."
        )


class OpenAiManager:
    def __init__(self):
        self.chat_history = []
        if not OPENAI_API_KEY:
            raise EnvironmentError("OPENAI_API_KEY not found in environment variables!")
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def append_system_message(self, message):
        self.chat_history.append(message)

    def chat(self, prompt=""):
        if not prompt:
            print("Didn't receive input!")
            return
        chat_question = [{"role": "user", "content": prompt}]
        if num_tokens_from_messages(chat_question) > 8000:
            print("The length of this chat question is too large for the GPT model")
            return
        print("\nAsking ChatGPT a question...")
        completion = self.client.chat.completions.create(
            model="gpt-4o",
            messages=chat_question
        )
        return completion.choices[0].message.content

    def chat_with_history(self, prompt=""):
        if not prompt:
            print("Didn't receive input!")
            return
        self.chat_history.append({"role": "user", "content": prompt})
        while num_tokens_from_messages(self.chat_history) > 8000:
            self.chat_history.pop(1)
        completion = self.client.chat.completions.create(
            model="gpt-4o",
            messages=self.chat_history
        )
        response_text = completion.choices[0].message.content
        self.chat_history.append({"role": "assistant", "content": response_text})
        return response_text
