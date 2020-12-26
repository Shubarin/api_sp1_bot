import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
PRAKTIKUM_API_URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
headers = {
    'Authorization': f'OAuth {PRAKTIKUM_TOKEN}',
}
available_statuses_verdicts = {
    'reviewing': None,
    'approved': 'Ревьюеру всё понравилось, можно приступать к следующему уроку.',
    'rejected': 'К сожалению в работе нашлись ошибки.',
}

logging.basicConfig(format='%(asctime)s; %(levelname)s; %(message)s',
                    filename='log.log',
                    filemode='a')
logger = logging.getLogger('__name__')
logger.setLevel(logging.DEBUG)


class UndefinedStatusError(Exception):
    pass


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    status = homework.get('status')
    if status is None or status not in available_statuses_verdicts:
        raise UndefinedStatusError(
            f'В ответе пришел неизвестный статус {status}')
    verdict = available_statuses_verdicts[status]
    if not verdict:
        return f'Работа "{homework_name}" взята в ревью'
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    params = {
        'from_date': current_timestamp
    }
    homework_statuses = requests.get(PRAKTIKUM_API_URL,
                                     headers=headers,
                                     params=params)
    return homework_statuses.json()


def send_message(message, bot_client):
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
    logger.debug('Бот запущен')
    current_timestamp = int(time.time())

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(
                    parse_homework_status(new_homework.get('homeworks')[0]),
                    bot_client)
                logger.info('Отправлено сообщение')
            current_timestamp = new_homework.get('current_date',
                                                 current_timestamp)
            time.sleep(300)

        except Exception as e:
            logger.error(e, exc_info=True)
            send_message(
                f'Бот столкнулся с ошибкой: {e}',
                bot_client)
        time.sleep(5)


if __name__ == '__main__':
    main()
