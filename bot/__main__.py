from signal import signal, SIGINT
from os import path as ospath, remove as osremove, execl as osexecl
from subprocess import run as srun, check_output
from psutil import disk_usage, cpu_percent, swap_memory, cpu_count, virtual_memory, net_io_counters, boot_time
from time import time
from datetime import datetime
import pytz
from sys import executable
from telegram import InlineKeyboardMarkup
from telegram.ext import CommandHandler

from bot import bot, dispatcher, updater, botStartTime, IGNORE_PENDING_REQUESTS, LOGGER, Interval, INCOMPLETE_TASK_NOTIFIER, DB_URI, alive, app, main_loop
from .helper.ext_utils.fs_utils import start_cleanup, clean_all, exit_clean_up
from .helper.ext_utils.telegraph_helper import telegraph
from .helper.ext_utils.bot_utils import get_readable_file_size, get_readable_time
from .helper.ext_utils.db_handler import DbManger
from .helper.telegram_helper.bot_commands import BotCommands
from .helper.telegram_helper.message_utils import sendMessage, sendMarkup, editMessage, sendLogFile
from .helper.telegram_helper.filters import CustomFilters
from .helper.telegram_helper.button_build import ButtonMaker

from .modules import authorize, cancel_mirror, mirror_status, mirror, watch, shell, eval, leech_settings


def stats(update, context):
    currentTime = get_readable_time(time() - botStartTime)
    osUptime = get_readable_time(time() - boot_time())
    total, used, free, disk= disk_usage('/')
    total = get_readable_file_size(total)
    used = get_readable_file_size(used)
    free = get_readable_file_size(free)
    sent = get_readable_file_size(net_io_counters().bytes_sent)
    recv = get_readable_file_size(net_io_counters().bytes_recv)
    cpuUsage = cpu_percent(interval=0.5)
    p_core = cpu_count(logical=False)
    t_core = cpu_count(logical=True)
    swap = swap_memory()
    swap_p = swap.percent
    swap_t = get_readable_file_size(swap.total)
    memory = virtual_memory()
    mem_p = memory.percent
    mem_t = get_readable_file_size(memory.total)
    mem_a = get_readable_file_size(memory.available)
    mem_u = get_readable_file_size(memory.used)
    stats = f'<b>???????????????? ?????????? ??????????????????????????????? ???????</b>\n' \
            f'<b>???</b>\n' \
            f'<b>|--???????????? ????????????????????????:</b> {currentTime}\n'\
            f'<b>|--???????? ????????????????????????:</b> {osUptime}\n\n'\
            f'<b>|--???????????????????? ???????????????? ????????????????????:</b> {total}\n'\
            f'<b>|--????????????????:</b> {used} | <b>????????????????:</b> {free}\n\n'\
            f'<b>|--????????????????????????:</b> {sent}\n'\
            f'<b>|--????????????????????????????????:</b> {recv}\n\n'\
            f'<b>|--????????????:</b> {cpuUsage}%\n'\
            f'<b>|--????????????:</b> {mem_p}%\n'\
            f'<b>|--????????????????:</b> {disk}%\n\n'\
            f'<b>|--???????????????????????????????? ????????????????????:</b> {p_core}\n'\
            f'<b>|--???????????????????? ????????????????????:</b> {t_core}\n\n'\
            f'<b>|--????????????????:</b> {swap_t} | <b>????????????????:</b> {swap_p}%\n'\
            f'<b>|--???????????????????????? ????????????????????:</b> {mem_t}\n'\
            f'<b>|--???????????????????????? ????????????????:</b> {mem_a}\n'\
            f'<b>|--???????????????????????? ????????????????:</b> {mem_u}\n'
    sendMessage(stats, context.bot, update.message)

def start(update, context):
    buttons = ButtonMaker()
    buttons.buildbutton("PublicLeechCloneGroup", "t.me/PublicLeechCloneGroup")
    reply_markup = InlineKeyboardMarkup(buttons.build_menu(2))
    if CustomFilters.authorized_user(update) or CustomFilters.authorized_chat(update):
        start_string = f'''
This bot can be used only in group!
Type /{BotCommands.HelpCommand} to get a list of available commands
'''
        sendMarkup(start_string, context.bot, update.message, reply_markup)
    else:
        sendMarkup('???????????? ???????????????????????????????????????? ????????????????', context.bot, update.message, reply_markup)

def restart(update, context):
    restart_message = sendMessage("Restarting...", context.bot, update.message)
    if Interval:
        Interval[0].cancel()
        Interval.clear()
    alive.kill()
    clean_all()
    srun(["pkill", "-9", "-f", "gunicorn|extra-api|last-api|megasdkrest|new-api"])
    srun(["python3", "update.py"])
    with open(".restartmsg", "w") as f: 
        f.truncate(0)
        f.write(f"{restart_message.chat.id}\n{restart_message.message_id}\n")
    osexecl(executable, executable, "-m", "bot")


def log(update, context):
    sendLogFile(context.bot, update.message)


help_string_telegraph = f'''<br>
<br><br>
<b>/{BotCommands.LeechZipWatchCommand}</b> ???????????????????? ???????????????????????????? ????????-???????????? ???????????? ???????????? ???????????????????????? ????????????????????????????????????
<br><br>
<b>/{BotCommands.LeechSetCommand}</b> ???????? ???????????????????? ???????????????? ???????????????????????????? ???????????????????? ????????????????????????????????
<br><br>
<b>/{BotCommands.SetThumbCommand}</b> ???????????????????? ???????? ???????????????????? ???????? ???????????? ???????? ???????? ???????????????????????????????????? ???????????? ???????????????? ????????????????????????????
<br><br>
<b>/{BotCommands.StatusCommand}</b>: ???????????????????? ???? ???????????????????????? ???????? ???????????? ???????????? ????????????????????????????????????
<br><br>
<b>/{BotCommands.StatsCommand}</b>: ???????????????? ???????????????????? ???????? ???????????? ???????????????????????????? ???????????? ???????????? ???????? ???????????????????????? ????????
'''

help = telegraph.create_page(
        title='???????????????????????????????????????????????????????????????????????????????????? ????????????????',
        content=help_string_telegraph,
    )["path"]

help_string = f'''
/{BotCommands.LeechCommand}: ???????????????????? ????????????????????????????/???????????????????????? ????????????????

/{BotCommands.ZipLeechCommand}: ???????????????????? ????????????????????????????/???????????????????????? ???????????????? ???????????? ???????????????????????? ???????? .????????????

/{BotCommands.UnzipLeechCommand}: ???????????????????? ????????????????????????????/???????????????????????? ???????????????? ???????????? ????????????????????????????

/{BotCommands.QbLeechCommand}: ????????????????????  ????????????????????????????/???????????????????????? ???????????????????? ????????????????????????????????????????????

/{BotCommands.QbZipLeechCommand}: ???????????????????? ????????????????????????????/???????????????????????? ???????????? ???????????????????????? ???????? .???????????? ???????????????????? ????????????????????????????????????

/{BotCommands.QbUnzipLeechCommand}: ???????????????????? ????????????????????????????/???????????????????????? ???????????????? ???????????? ???????????????????????????? ???????????????????? ????????????????????????????????????

/{BotCommands.LeechWatchCommand}: ???????????????????? ???????????????????????????? ????????-???????????? ???????????????????????????????????? ???????????????? ???????????? ???????????????????????? ???????? ????????????????????????????????

/{BotCommands.CancelMirror}: ???????????????????? ???????? ???????????? ???????????????????????????? ???????? ???????????????????? ???????????? ???????????????????????????????? ???????????? ???????????????????????????????????? ???????????? ???????????????? ???????????????????????????????? ???????????????? ???????? ????????????????????????????????????
'''

def bot_help(update, context):
    button = ButtonMaker()
    button.buildbutton("???????????????????? ???????????????? ???????????? ???????????????????? ????????????????????????????????", f"https://telegra.ph/{help}")
    reply_markup = InlineKeyboardMarkup(button.build_menu(1))
    sendMarkup(help_string, context.bot, update.message, reply_markup)

def main():
    start_cleanup()
    if INCOMPLETE_TASK_NOTIFIER and DB_URI is not None:
        notifier_dict = DbManger().get_incomplete_tasks()
        if notifier_dict:
            for cid, data in notifier_dict.items():
                if ospath.isfile(".restartmsg"):
                    with open(".restartmsg") as f:
                        chat_id, msg_id = map(int, f)
                    msg = '???????????????????????????????????? ????????????????????????????????????????????????!'
                else:
                    kek = datetime.now(pytz.timezone(f'Asia/Kolkata'))
                    vro = kek.strftime('\n ???????????????? : %d/%m/%Y\n ????????????????: %I:%M%P')
                    msg = f" ???????????? ???????????????????????????????????? \n{vro}\n\n#Restarted"
                for tag, links in data.items():
                     msg += f"\n\n???? {tag}: "
                     for index, link in enumerate(links, start=1):
                         msg += f" <a href='{link}'>{index}</a> |"
                         if len(msg.encode()) > 4000:
                             if '???????????????????????????????????? ????????????????????????????????????????????????!' in msg and cid == chat_id:
                                 bot.editMessageText(msg, chat_id, msg_id, parse_mode='HTMl', disable_web_page_preview=True)
                                 osremove(".restartmsg")
                             else:
                                 bot.sendMessage(cid, msg, 'HTML')
                             msg = ''
                if '???????????????????????????????????? ????????????????????????????????????????????????!' in msg and cid == chat_id:
                     bot.editMessageText(msg, chat_id, msg_id, parse_mode='HTMl', disable_web_page_preview=True)
                     osremove(".restartmsg")
                else:
                    bot.sendMessage(cid, msg, 'HTML')

    if ospath.isfile(".restartmsg"):
        with open(".restartmsg") as f:
            chat_id, msg_id = map(int, f)
        bot.edit_message_text("???????????????????????????????????? ????????????????????????????????????????????????!", chat_id, msg_id)
        osremove(".restartmsg")

    start_handler = CommandHandler(BotCommands.StartCommand, start, run_async=True)
    restart_handler = CommandHandler(BotCommands.RestartCommand, restart,
                                     filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True)
    help_handler = CommandHandler(BotCommands.HelpCommand,
                                  bot_help, filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    stats_handler = CommandHandler(BotCommands.StatsCommand,
                                   stats, filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    log_handler = CommandHandler(BotCommands.LogCommand, log, filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(restart_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(stats_handler)
    dispatcher.add_handler(log_handler)
    updater.start_polling(drop_pending_updates=IGNORE_PENDING_REQUESTS)
    LOGGER.info("????????????????????Bot Started!????????????????????")
    signal(SIGINT, exit_clean_up)

main()
app.start()

main_loop.run_forever()
