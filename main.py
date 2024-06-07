import os
import requests
from bs4 import BeautifulSoup
from firebase_functions import https_fn
from firebase_functions.params import StringParam
from firebase_admin import initialize_app

OPENAI_KEY = StringParam("OPENAI_KEY")
INOREADER_KEY = StringParam("INOREADER_KEY")
TRELLO_KEY = StringParam("TRELLO_KEY")
TRELLO_TOKEN = StringParam("TRELLO_TOKEN")

initialize_app()

@https_fn.on_request()
def inoreader_summarizer(req: https_fn.Request) -> https_fn.Response:
    inoreader_token = req.args.get('token')
    if inoreader_token != INOREADER_KEY.value:
        return https_fn.Response("Error")

    data = req.get_json()
    article_url = data.get('items')[0].get('canonical')[0].get('href')
    
    response = get_article_text(article_url)
    summary = summarize_text(response)
    save_to_trello(summary)
    return https_fn.Response("OK")

def get_article_text(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    paragraphs = soup.find_all('p')
    article_text = ' '.join([para.get_text() for para in paragraphs])
    return article_text

def summarize_text(text):
    url = "https://api.openai.com/v1/chat/completions";
    headers = {"Authorization": f"Bearer {OPENAI_KEY.value}"}
    body = {
      "messages": [{
            "role": "user",
            "content": "Streść podany artykuł. Używaj języka polskiego w odpowiedzi. Bądź zwięzły. " + text,
      }],
      "temperature": 0.1,
      "model": "gpt-3.5-turbo",
    }

    completion = requests.post(url, headers=headers, json=body).json()
    return completion['choices'][0]['message']['content']

def save_to_trello(text):
    url = f"https://api.trello.com/1/cards?idList=66624c915a7259fde06db7bf&key={TRELLO_KEY.value}&token={TRELLO_TOKEN.value}&name={text}"
    response = requests.post(url).json()