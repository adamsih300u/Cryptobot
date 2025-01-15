import telegram
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)

def seconds(time_list):
    time_in_seconds = 0
    for time in time_list:
        if 'w' in time:
            time_in_seconds += (int(time[:len(time) - 1]) * 604800)
        elif 'd' in time:
            time_in_seconds += (int(time[:len(time) - 1]) * 86400)
        elif 'h' in time:
            time_in_seconds += (int(time[:len(time) - 1]) * 3600)
        elif 'm' in time:
            time_in_seconds += (int(time[:len(time) - 1]) * 60)
        else:
            time_in_seconds += int(time[:len(time) - 1])
    return time_in_seconds

def isValid(time_list):
    for time in time_list:
        if len(time) > 1:
            unit = time[len(time) - 1]
            number = time[:len(time) - 1]
            if unit == 'w' or unit == 'd' or unit == 'h' or unit == 'm' or unit == 's':
                if str.isdigit(number):
                    return True
    return False


def call_back_time(context: telegram.ext.CallbackContext):
    context.bot.send_message(chat_id=context.job.context, text=data["key"])
