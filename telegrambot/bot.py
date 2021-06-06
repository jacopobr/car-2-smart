###Manages BOT ###
from os import EX_CANTCREAT
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
import mysql.connector
import os

#Telegram BOT API configuration - valid token hidden
TOKEN =os.environ.get('BOT_TOKEN')

#MySQL Database credential, hosted on freemysqlhosting.net - valid username and password hidden
config = {
  'user': os.environ.get('USER'),
  'password': os.environ.get('PASSWORD'),
  'host': 'sql11.freemysqlhosting.net',
  'database': os.environ.get('DATABASE'),
  'raise_on_warnings': True
}

EMERGENCY = range(1) 


def start(update, context):
    """
        Bot '/start' command: at the start of the chat the bot extract from the message all the user information,
        check if the user is already registered to 'Car2Safe' platform and update the 'chat_id' field in the database.
    """
    
    name = update.message.from_user["first_name"]
    username = update.message.from_user["username"]
    chat_id = update.message.chat_id

    #Check if the user is already in the system db
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM User WHERE tg_username = '{username}'")
    data = cursor.fetchone()

    #If the user exists, update its 'chat_id'
    if data != None:
        try:
            cursor.execute(f"UPDATE User SET tg_chatid = {chat_id} WHERE tg_username = '{username}'")
            conn.commit()
            conn.close()

            welcome_message = '\
            <b> WELCOME! &#129302;</b>\
            \nHi, ' + name + '!\
            \nEverybody wants to have fun!&#x1F37B;&#128378;&#x1F37E;&#128131;\
            \nCar2Safe allows you to enjoy your party without worring about driving later.\
            \nIf you drank too much for driving, you will be put in contact with someone you trust, or a taxi will be called! &#128661;.\
            \nType /help to see the allowed commands..\
            \nBefore starting type /setnumber to set your emergency number.'
            update.message.reply_text(text = welcome_message, parse_mode = 'HTML')

        except Exception as e:
            update.message.reply_text(text = e)
    else:
        register_message = '\
            <b> You need to be registered!! &#129302;</b>\
            \nHi, ' + name + '!\
            \nBefore accessing the bot you should be registered to the Car2Safe carsharing platform! Come back as soon as you have done!'
        update.message.reply_text(text = register_message, parse_mode = 'HTML')


def setnumber(update,context):
    """
        Bot '/setnumber' command: starter of the conversation to set the emergency number
    """
    update.message.reply_text('Please insert the number of a person you trust. It can be your life saver!')
    return EMERGENCY


def save_emergency_number(update, context):
    """
        Second phase of the conversation with the user to save the emergency number.
        The number inserted by the user is saved in the mysql database. 
    """

    username = update.message.from_user["username"]
    emergency_number = update.message.text
    
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor() 
    cursor.execute(f"UPDATE User SET emergency_number = {emergency_number} WHERE tg_username = '{username}'")
    conn.commit()
    conn.close()
    update.message.reply_text(f'The emergency number you saved is {emergency_number}.\n')
    update_text = "<b> SAFETY FIRST </b>\
                \nYou have correctly set up this bot. You can now use our sharing service and take the alcohol test before starting the engine.\
                \nIf you excedees the limit, the car won't start and you will be prompeted to call someone to pick you up.\
                \nEnjoy!"
    bot.sendMessage(chat_id = update.message.chat_id, text = update_text, parse_mode = "HTML")
    return ConversationHandler.END


def seenumber(update, context):
    """
        Bot '/seenumber' command: shows the user's emergency number.
        It extract the username from the message received and then queries the database for its emergency number in order to print it.
    """
    
    username = update.message.from_user["username"]

    conn = mysql.connector.connect(**config)
    cursor = conn.cursor() 
    cursor.execute(f"SELECT emergency_number FROM User WHERE tg_username = '{username}'")
    data = cursor.fetchone()
    conn.close()

    message = 'The current emergency number you saved is:\n<b>' + data[0] +'</b>\
            \nUse the command /setnumber to change it.'
    update.message.reply_text(text = message, parse_mode = 'HTML')

def EmergencyNumber(update, context):
    """
        Bot '/EmergencyNumber' command: shows the user's emergency number.
        It extract the username from the message received and then queries the database for its emergency number.
    """

    username = update.message.from_user["username"]

    conn = mysql.connector.connect(**config)
    cursor = conn.cursor() 
    cursor.execute(f"SELECT emergency_number FROM User WHERE tg_username = '{username}'")
    data = cursor.fetchone()
    conn.close()

    message = '&#10071;&#10071;&#10071;&#10071;&#10071;\
            \n<b> CALL YOUR EMERGENCY NUMBER PLEASE:</b>\
            \n&#10071;&#10071;&#10071;&#10071;&#10071'
    update.message.reply_text(text = message, parse_mode = 'HTML')

    #Print more times the emergency number so there is more chance to call
    alarm_text = ''+data[0]+' \
                \n'+data[0]+' \
                \n'+data[0]+' \
                \n'+data[0]+' \
                \n'+data[0]+' \
                \n'+data[0]+' \
                \n'+data[0]+' \
                \n'+data[0]+' \
                \n'+data[0]+' '

    bot.sendMessage(chat_id = update.message.chat_id, text = alarm_text)


def Taxi(update, context):
    """
        Bot '/Taxi' command: shows the number of the taxi company.
    """

    message = '&#10071;&#10071;&#10071;&#10071;&#10071;\
            \n<b> CALL A TAXI PLEASE:</b>\
            \n&#10071;&#10071;&#10071;&#10071;&#10071'
    update.message.reply_text(text = message, parse_mode = 'HTML')

    #Print more times the taxi number so there is more chance to call
    alarm_text = '+390115730 \
                \n+390115730 \
                \n+390115730 \
                \n+390115730 \
                \n+390115730 \
                \n+390115730 \
                \n+390115730 \
                \n+390115730 \
                \n+390115730 \
                \n+390115730 '
    bot.sendMessage(chat_id = update.message.chat_id, text = alarm_text)




def help(update, context):
    """
        Bot '/help' command: shows to the user a list of the allowed command by the bot.
    """
    message = "➡️<b>List of commands: </b>\
        \n/seenumber: shows the currently saved emergency number;\
        \n/setnumber: set the emergency number.\
        \n➡️<b>When you are over the alcohol limit you can choose between:</b>\
        \n/Taxi: show taxi service mobile number;\
        \n/EmergencyNumber: show emergengy numeber."
    update.message.reply_text(text = message, parse_mode = 'HTML')


def main():
    """
        Main function exectued whent the bot starts. Contains the allows commands and their functions.
        Furthermore, a conversation handler is present: it asks the user for the number, wait for the reply and responds back to the user
        with the rusult of the funciton.
    """
    upd = Updater(TOKEN, use_context=True)
    disp=upd.dispatcher
    disp.add_handler(CommandHandler("start", start))
    disp.add_handler(CommandHandler("help", help))
    disp.add_handler(CommandHandler("seenumber", seenumber))
    disp.add_handler(CommandHandler("EmergencyNumber", EmergencyNumber))
    disp.add_handler(CommandHandler("Taxi", Taxi))

    conv_handler = ConversationHandler(
        entry_points = [CommandHandler('setnumber',setnumber)],
        fallbacks = [],
        states={
                EMERGENCY: [MessageHandler(Filters.text, save_emergency_number)],
            },
        )

    disp.add_handler(conv_handler)
    upd.start_polling()
    upd.idle()


if __name__=='__main__':
    bot = telegram.Bot(token = TOKEN)
    print('BOT RUNNING')
    main()