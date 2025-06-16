import openai

import os
openai.api_key = os.getenv("OPENAI_API_KEY")

SYSTEM_MESSAGE = {
    "role": "system",
    "content": (
        "You are Superfan, a mysterious but enthusiastic being who knows everything about music, "
        "history, and cultural trends. You are cryptic but charismatic, clever but concise. "
        "Always respond like you're talking to someone you *love* to share knowledge with."
    )
}

class OpenAiManager:
    def __init__(self):
        self.chat_history = [SYSTEM_MESSAGE]

    def get_response(self, user_input):
        self.chat_history.append({"role": "user", "content": user_input})

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=self.chat_history,
            temperature=0.9
        )

        ai_message = response.choices[0].message["content"]
        self.chat_history.append({"role": "assistant", "content": ai_message})
        return ai_message
