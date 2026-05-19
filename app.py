from flask import Flask, request, jsonify
import logging
import random

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

cities = {
    'москва': ['1656841/f2329ae4dc28653995b5',
               '1521359/3cc798f059dced12cb7e'],
    'нью-йорк': ['13200873/a288322fb79711ee5ec5',
                 '1521359/dfdf933cd3e300d1a20d'],
    'париж': ['1533899/491e3e2c56f757fb022a',
              '13200873/b320615f453bb02e43ec']
}

sessionStorage = {}


@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(response, request.json)
    logging.info('Response: %r', response)
    return jsonify(response)


def handle_dialog(res, req):
    user_id = req['session']['user_id']

    if req['session']['new']:
        res['response']['text'] = 'Привет! Назови свое имя!'
        sessionStorage[user_id] = {
            'first_name': None,
            'city': None
        }
        return

    if sessionStorage[user_id]['first_name'] is None:
        first_name = get_first_name(req)
        if first_name is None:
            res['response']['text'] = \
                'Не расслышала имя. Повтори, пожалуйста!'
        else:
            sessionStorage[user_id]['first_name'] = first_name
            city = random.choice(list(cities.keys()))
            sessionStorage[user_id]['city'] = city
            res['response']['card'] = {
                'type': 'BigImage',
                'title': f'Приятно познакомиться, {first_name.title()}. '
                         f'Угадай, что это за город!',
                'image_id': random.choice(cities[city])
            }
            res['response']['text'] = 'Угадай город!'
            res['response']['buttons'] = [
                {
                    'title': c.title(),
                    'hide': True
                } for c in cities
            ]
    else:
        city = get_city(req)
        current_city = sessionStorage[user_id]['city']

        if city is not None and city == current_city:
            res['response']['text'] = \
                f'Правильно! Это {current_city.title()}. Сыграем еще?'
            sessionStorage[user_id]['city'] = None
            res['response']['buttons'] = [
                {'title': 'Да', 'hide': True},
                {'title': 'Нет', 'hide': True}
            ]
        elif city is not None:
            res['response']['text'] = \
                'Неправильно! Попробуй еще раз.'
            res['response']['buttons'] = [
                {
                    'title': c.title(),
                    'hide': True
                } for c in cities
            ]
        else:
            if req['request']['original_utterance'].lower() in ['да', 'давай', 'конечно', 'хочу']:
                city = random.choice(list(cities.keys()))
                sessionStorage[user_id]['city'] = city
                res['response']['card'] = {
                    'type': 'BigImage',
                    'title': 'Угадай, что это за город!',
                    'image_id': random.choice(cities[city])
                }
                res['response']['text'] = 'Угадай город!'
                res['response']['buttons'] = [
                    {
                        'title': c.title(),
                        'hide': True
                    } for c in cities
                ]
            elif req['request']['original_utterance'].lower() in ['нет', 'не', 'хватит', 'стоп']:
                res['response']['text'] = \
                    'До встречи!'
                res['response']['end_session'] = True
            else:
                res['response']['text'] = \
                    'Я не поняла. Сыграем еще?'
                res['response']['buttons'] = [
                    {'title': 'Да', 'hide': True},
                    {'title': 'Нет', 'hide': True}
                ]


def get_city(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.GEO':
            return entity['value'].get('city', None)
    return None


def get_first_name(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.FIO':
            return entity['value'].get('first_name', None)
    return None


if __name__ == '__main__':
    app.run()
