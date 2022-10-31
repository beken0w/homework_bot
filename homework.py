import os
import time
import telegram
import requests
import logging

# Здравствуй Павел. Спасибо за рекомендации и советы. Я стараюсь исправлять их
# по максимуму, но в этот раз при построении логики check_response()
# столкнулся с проблемой. Если нужно валидировать словарь отдельной ДЗ, то
# могут быть две ситуации: либо запрос пройдет успешно и структура будет
# постоянной либо запрос неудачный и вообще ни о какой структуре речи быть не
# может. Поэтому я пока не смог реализовать проверку таких полей как:
# response['homeworks'][0]['homework_name'] и
# response['homeworks'][0]['status']. Сложность состояла в комбинации блоков
# try/except и if/else. Так еще и тесты очень сильно ограничивают.
# Есть как огромное желание довести данный проект до ума, так и выделить на это
# всё свободное время, т.е 24/7.

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=None)
logger.addHandler(handler)
formatter = logging.Formatter(
    '%(asctime)s - %(funcName)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправляет сообщение.
    bot - объект класса Bot,
    message - текст сообщения.
    """
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info('Сообщение успешно отправлено в Telegram.')
    except Exception as error:
        logger.exception(
            f'При отправке сообщения возникла ошибка: {error}.',
            exc_info=error
        )


def get_api_answer(current_timestamp):
    """Получение ответа API Yandex Practicum."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != 200:
            logger.error('Эндпоинт недоступен.')
            raise Exception('Эндпоинт недоступен.')
        return response.json()
    except Exception as error:
        logger.exception(
            f'При запросе API возникла ошибка: {error}.',
            exc_info=error
        )
        raise Exception


def check_response(response):
    """Проверка запроса."""
    check_set = {'homeworks', 'current_date'}
    res_resp = response['homeworks']
    if set(response.keys()).issubset(check_set):
        if not isinstance(res_resp, list):
            logger.error('Формат коллекции ДЗ не является списком')
            raise Exception('Формат коллекции ДЗ не является списком')
        else:
            logger.info('Запрос соответствует требованиям,'
                        ' передаю дальше')
            return res_resp
    else:
        logger.error('Формат запроса не соответствует требованиям')
        raise Exception('Формат запроса не соответствует требованиям')


def parse_status(homework):
    """Получение статуса домашней работы."""
    homework_name = homework['homework_name']
    homework_status = homework['status']
    try:
        verdict = HOMEWORK_STATUSES[homework_status]
        logger.debug('Статус домашней работы успешно получен.')
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    except Exception:
        logger.debug('Список домашних работ пуст.')
        raise Exception


def check_tokens():
    """Проверяет доступность постоянных окружения."""
    result = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    return all(result) or logger.critical(
        'Критическая ошибка. Не хватает постоянных окружения')


def main():
    """Основная логика работы бота."""
    checkpoint = ''
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    if not check_tokens:
        logger.critical('Не хватает постоянных окружения')
        raise Exception
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework_list = check_response(response)
            if homework_list:
                result = parse_status(homework_list[0])
                send_message(bot, result)
            else:
                logger.info('Список пуст. Ждем еще 10 минут.')
            current_timestamp = int(time.time())

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if checkpoint != message:
                send_message(bot, message)
            else:
                checkpoint = message
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
