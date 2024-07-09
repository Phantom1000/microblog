import requests
from flask import current_app as app


def translate(text, source_language, dest_language):
    error: str = 'При переводе произошла ошибка'
    if 'TRANSLATOR_KEY' not in app.config or not app.config['TRANSLATOR_KEY']:
        return error
    auth = {
        'Ocp-Apim-Subscription-Key': app.config['TRANSLATOR_KEY'],
        'Ocp-Apim-Subscription-Region': 'westus',
    }
    r = requests.post('https://api.cognitive.microsofttranslator.com/translate?api-version=3.0&from={}&to={}'.format(
            source_language, dest_language), headers=auth, json=[{'Text': text}])
    if r.status_code != 200:
        return error
    return r.json()[0]['translations'][0]['text']
