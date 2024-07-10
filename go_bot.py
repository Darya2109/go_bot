import telebot
from telebot import types
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import csv
import os

# Укажите ваш токен здесь
TOKEN = 'your_token'
bot = telebot.TeleBot(TOKEN)

scheduler = BackgroundScheduler()
scheduler.start()

# Глобальная переменная для хранения идентификатора опроса
current_poll_message_id = None
current_poll_chat_id = None


# Команда для начала голосования
@bot.message_handler(commands=['go'])
def start_vote(message):
    global current_poll_message_id, current_poll_chat_id

    # Проверяем, что сообщение из группы
    if message.chat.type not in ['group', 'supergroup']:
        bot.send_message(message.chat.id, "Эту команду можно использовать только в группе.")
        return

    poll_options = ["Да", "Нет"]

    # Создаем опрос
    poll_message = bot.send_poll(
        chat_id=message.chat.id,
        question="Играем сегодня?",
        options=poll_options,
        is_anonymous=False
    )

    current_poll_message_id = poll_message.message_id
    current_poll_chat_id = poll_message.chat.id

    # Упоминаем всех участников
    mention_all_users(message.chat.id)

    # Запланировать закрытие опроса через 12 часов
    scheduler.add_job(close_poll, 'date', run_date=datetime.utcnow() + timedelta(hours=12),
                      args=[poll_message.chat.id, poll_message.message_id])


def close_poll(chat_id, message_id):
    bot.stop_poll(chat_id, message_id)


# Обработка команды для отображения результатов голосования
@bot.message_handler(commands=['results'])
def show_results(message):
    if current_poll_message_id is None or current_poll_chat_id is None:
        bot.send_message(message.chat.id, "Голосование еще не началось или уже завершено.")
        return

    # Телеграмм автоматически отображает результаты опроса, когда он завершен
    bot.send_message(message.chat.id, "Результаты опроса будут видны в сообщении с опросом.")


# Команда для упоминания всех участников
@bot.message_handler(commands=['all'])
def tag_all_users(message):
    mention_all_users(message.chat.id)


# обращение к файлу со списком участников
def mention_all_users(chat_id):
    users_file = 'users.csv'
    if not os.path.exists(users_file):
        bot.send_message(chat_id, "Файл users.csv не найден.")
        return

    with open(users_file, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        users = list(reader)

    # Разбиваем список пользователей на группы по 15 человек
    chunks = [users[i:i + 15] for i in range(0, len(users), 15)]

    for chunk in chunks:
        # Создаем множество для уникальных упоминаний
        mentions = set()
        for user in chunk:
            if user['username']:
                mentions.add(f"@{user['username']}")
            else:
                full_name = f"{user['first_name']} {user['last_name']}".strip()
                mentions.add(full_name)

        mention_message = "Господа:\n" + ' '.join(mentions)

        # Отправляем сообщение с упоминанием группы пользователей
        bot.send_message(chat_id, mention_message)


bot.polling(none_stop=True)
