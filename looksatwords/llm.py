import ollama




host_url = 'http://localhost:11434'
publisher = 'Made by Ollama'

news_bot = ollama.Client(host=host_url)
headline_bot_init = [
        {
            'role': 'system',
            'content': 'You are a journalist writing a news headline. Include only content, no explanation. Include subltle random biases and opinions. Do not ask follow-up questions or include annotations or parenthases.',
        },
]
description_bot_init = [
        {
            'role': 'system',
            'content': 'You are a journalist writing a news description based off of a headline. Include only content, no explanation. Include subltle random biases and opinions. Do not ask follow-up questions or include annotations or parenthases.',
        },
]

def ask(question, context=[{'role':'system', 'content':'You are a helpful knowledge sharer'}]):
    response = news_bot.chat(model='llama3.1', messages=[
        *context,
        {
            'role': 'user',
            'content': question,
        },
        ])
    
    return response['message']['content']

def generate_news_headline(seed: str = ''):
    return ask('generate a single random {seed} news headline?', headline_bot_init)

def generate_news_description(headline:str):
    return ask(f'generate a single random news story based on the headline "{headline}"?', description_bot_init)

