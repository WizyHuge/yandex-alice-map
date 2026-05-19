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


def add_help_button(res):
    res['response']['buttons'].append({'title': 'Помощь', 'hide': True})


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

    if user_id not in sessionStorage:
        sessionStorage[user_id] = {
            'first_name': None,
            'city': None,
            'image_id': None,
            'last_city': None
        }

    if req['session']['new']:
        res['response']['text'] = 'Привет! Назови свое имя!'
        sessionStorage[user_id] = {
            'first_name': None,
            'city': None,
            'image_id': None,
            'last_city': None
        }
        return

    if 'на карте' in req['request']['original_utterance'].lower():
        res['response']['text'] = 'Сыграем еще?'
        res['response']['buttons'] = [
            {'title': 'Да', 'hide': True},
            {'title': 'Нет', 'hide': True}
        ]
        add_help_button(res)
        return

    if is_help(req):
        current_city = sessionStorage[user_id]['city']
        res['response']['text'] = \
            'Я показываю фотографию города, а ты должен угадать его название. Выбирай из кнопок или пиши название города.'
        if current_city is not None:
            res['response']['card'] = {
                'type': 'BigImage',
                'title': 'Правила: я показываю фото города, а ты угадываешь. '
                         'Угадай, что это за город!',
                'image_id': sessionStorage[user_id]['image_id']
            }
            res['response']['buttons'] = [
                {'title': c.title(), 'hide': True} for c in cities
            ]
            add_help_button(res)
        elif sessionStorage[user_id]['first_name'] is not None:
            res['response']['buttons'] = [
                {'title': 'Да', 'hide': True},
                {'title': 'Нет', 'hide': True}
            ]
            add_help_button(res)
        return

    if sessionStorage[user_id]['first_name'] is None:
        first_name = get_first_name(req)
        if first_name is None:
            res['response']['text'] = \
                'Не расслышала имя. Повтори, пожалуйста!'
        else:
            sessionStorage[user_id]['first_name'] = first_name
            city = random.choice(list(cities.keys()))
            image_id = random.choice(cities[city])
            sessionStorage[user_id]['city'] = city
            sessionStorage[user_id]['image_id'] = image_id
            res['response']['card'] = {
                'type': 'BigImage',
                'title': f'Приятно познакомиться, {first_name.title()}. '
                         f'Угадай, что это за город!',
                'image_id': image_id
            }
            res['response']['text'] = 'Угадай город!'
            res['response']['buttons'] = [
                {'title': c.title(), 'hide': True} for c in cities
            ]
            add_help_button(res)
    else:
        city = get_city(req)
        current_city = sessionStorage[user_id]['city']

        if city is not None and city == current_city:
            res['response']['text'] = \
                f'Правильно! Это {current_city.title()}. Сыграем еще?'
            sessionStorage[user_id]['last_city'] = current_city
            sessionStorage[user_id]['city'] = None
            res['response']['buttons'] = [
                {
                    'title': current_city.title() + ' на карте',
                    'url': 'https://yandex.ru/maps/?mode=search&text=' + current_city.title(),
                    'hide': False
                },
                {'title': 'Да', 'hide': True},
                {'title': 'Нет', 'hide': True}
            ]
            add_help_button(res)
        elif city is not None:
            res['response']['text'] = \
                'Неправильно! Попробуй еще раз.'
            res['response']['buttons'] = [
                {'title': c.title(), 'hide': True} for c in cities
            ]
            add_help_button(res)
        else:
            if req['request']['original_utterance'].lower() in ['да', 'давай', 'конечно', 'хочу']:
                city = random.choice(list(cities.keys()))
                image_id = random.choice(cities[city])
                sessionStorage[user_id]['city'] = city
                sessionStorage[user_id]['image_id'] = image_id
                res['response']['card'] = {
                    'type': 'BigImage',
                    'title': 'Угадай, что это за город!',
                    'image_id': image_id
                }
                res['response']['text'] = 'Угадай город!'
                res['response']['buttons'] = [
                    {'title': c.title(), 'hide': True} for c in cities
                ]
                add_help_button(res)
            elif req['request']['original_utterance'].lower() in ['нет', 'не', 'хватит', 'стоп']:
                res['response']['text'] = 'До встречи!'
                res['response']['end_session'] = True
            else:
                res['response']['text'] = \
                    'Я не поняла. Сыграем еще?'
                res['response']['buttons'] = [
                    {'title': 'Да', 'hide': True},
                    {'title': 'Нет', 'hide': True}
                ]
                add_help_button(res)


def is_help(req):
    text = req['request']['original_utterance'].lower()
    return text in ['помощь', 'помоги', 'помогите', 'что делать', 'как играть', 'правила']


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
