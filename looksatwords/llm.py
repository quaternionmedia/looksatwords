import os

import ollama

# WHERE OLLAMA ANSWERS, AND WHY ONLY HALF OF THIS IS A SETTING.
#
# THE MODEL IS A SETTING. Which model a machine has pulled is that machine's
# business, and a hardcoded name fails with a 404 naming the model rather than
# the fix -- `llama3.1` against a box holding only `qwen2.5-coder:7b` is the
# run that established this.
#
# THE HOST IS NOT A SETTING. It is loopback. A client that could be pointed at
# another machine is how "generated on this machine only" stops being true, and
# every corpus this project sits beside makes the same split: the port moves,
# the host does not. Here not even the port moves, because Ollama publishes one.
HOST = "http://localhost:11434"
MODEL = os.environ.get("LOOKSATWORDS_OLLAMA_MODEL", "llama3.1")

host_url = HOST
publisher = "Made by Ollama"

news_bot = ollama.Client(host=host_url)
headline_bot_init = [
    {
        "role": "system",
        "content": "You are a journalist writing a news headline. Include only content, no explanation. Include subltle random biases and opinions. Do not ask follow-up questions or include annotations or parenthases.",
    },
]
description_bot_init = [
    {
        "role": "system",
        "content": "You are a journalist writing a news description based off of a headline. Include only content, no explanation. Include subltle random biases and opinions. Do not ask follow-up questions or include annotations or parenthases.",
    },
]


def ask(
    question,
    context=[{"role": "system", "content": "You are a helpful knowledge sharer"}],
):
    """
    Sends a question to the Ollama chat model using the specified context.

    Parameters:
        question (str): The user question or prompt to send to the model.
        context (list, optional): A list of context messages in the form of dicts with 'role' and 'content'.
                                  Defaults to a generic helpful assistant context.

    Returns:
        str: The content of the model's response message.
    """
    response = news_bot.chat(
        model=MODEL,
        messages=[
            *context,
            {
                "role": "user",
                "content": question,
            },
        ],
    )

    return response["message"]["content"]


def generate_news_headline(seed: str = ""):
    """
    Generates a single, random news headline based on an optional seed prompt.

    Parameters:
        seed (str, optional): A seed or topic to inspire the headline. Defaults to an empty string.

    Returns:
        str: A generated news headline.
    """
    return ask("generate a single random {seed} news headline?", headline_bot_init)


def generate_news_description(headline: str):
    """
    Generates a news description based on a provided headline.

    Parameters:
        headline (str): The news headline to base the description on.

    Returns:
        str: A generated news story description.
    """
    return ask(
        f'generate a single random news story based on the headline "{headline}"?',
        description_bot_init,
    )
