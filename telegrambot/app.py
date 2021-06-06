###Manages REST API ###
from flask import Flask, request
from telegram import ReplyKeyboardMarkup
import telegram
from datetime import datetime
import mysql.connector
import os

app = Flask(__name__)

#Telegram BOT API configuration - valid token hidden
app.config['BOT_TOKEN'] = os.environ.get('BOT_TOKEN')
app.config['BOT_USER_NAME'] = 'Car2SafeBot'
app.config['CHANNEL_CHAT'] = '@car2safe'
bot = telegram.Bot(token = app.config['BOT_TOKEN'])

#MySQL Database credential, hosted on freemysqlhosting.net - valid username and password hidden
config = {
  'user': os.environ.get('USER'),#<user>',
  'password': os.environ.get('PASSWORD'),#<password>',
  'host': 'sql11.freemysqlhosting.net',
  'database': os.environ.get('DATABASE'),#'<same_as_user>',
  'raise_on_warnings': True
}

@app.route('/contactChannel', methods = ['POST'])
def sendChannelMessage():
    """
        HTTP Post method: receives a message from the window monitoring microservices containg information about the accident.
        It decomposes the message and send a message to the telegram channel with the information on the car involved in the accident.
    """
    now = datetime.now()
    body = request.get_json(force=True);
    
    #Choose the photo to send according to which window has been broken
    if (body['data']['message'] == 'left window broken'):
        photo_url = './static/img/left.png'
    elif (body['data']['message'] == 'right window broken'):
        photo_url = './static/img/right.png'
    elif (body['data']['message'] == 'back window broken'):
        photo_url = './static/img/back.png'
    elif (body['data']['message'] == 'front window broken'):
        photo_url = './static/img/front.png'

    #Construct the message to be sent throught to the channel 
    message = '<b> &#x2757; ALARM &#x2757;</b>\
            \n ➡️ Vehicle: ' + body['data']['plate'] + '\
            \n ➡️ Message: ' + body['data']['message'] + '\
            \n ➡️ Date: ' + now.strftime("%d/%m/%Y %H:%M:%S")

    #Send the message
    bot.sendPhoto(chat_id= app.config['CHANNEL_CHAT'], photo = open(photo_url, "rb"), caption = message, parse_mode=telegram.ParseMode.HTML)
    return 'The message has been sent.'

@app.route('/alcoholTest', methods = ['POST'])
def sendUserMessage():
    """
        HTTP Post method: it receives a JSON with the result of the alcohol test sent by the 'car unlock' microservices.
        If the alcohol test is failed, hence the user cannot drive the car, the message is decomposed and a warning message is sent to the user
        chat with the bot. Furthermore, the booking status in the database is set to 'not valid'.
        If the alcohol test is not failed, hence the user can drive, the booking status in the database is set to 'valid' and the user can start its drive.
    """
    
    body = request.get_json();
    plate = body['plate']

    #Check if the user is already present in the db in order to fetch its telegram chat_id
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        cursor.execute(f"SELECT tg_chatid\
                        From User\
                        INNER JOIN ActiveBooking ON User.tg_username = ActiveBooking.tg_username\
                        WHERE ActiveBooking.plate = '{plate}'")
        data = cursor.fetchone()
    except Exception as e:
        return 'Problem accessing db: ' + str(e)
    
    #If the user exist, its chat id is extracted
    if len(data) != 0 and body["failed"] == True:
        chat_id = data[0]

        #If the alcohol test is failed, construct and sent the message to the user through the telegram bot
        reply_keyboard = [['/Taxi', '/EmergencyNumber']]
        message = '<b> &#x2757; Forbidden Unlock  &#x2757;</b>\
            \nYou tried to unlock a car, but you were stopped due to the high level of Alcohol in you blood:\
            \n <b>Alcohol level: ' + str(body["alcohol_value"]) + ' g/L!</b>\
            \n These are the risks you are facing: \
            \n ➡️ Fine: from ' + str(body["fine"][0]) + ' to '+ str(body["fine"][1]) + ' €; \
            \n ➡️ License suspension: from ' + str(body["license_suspension"][0]) + ' to '+ str(body["license_suspension"][1]) + ' months'

        if (body["impounding"] ==  True):
            message = message + ';\n ➡️ Prison: from ' + str(body["prisons"][0]) + ' to '+ str(body["prisons"][1]) + ' months.'

        bot.sendMessage(chat_id = chat_id , text = message, parse_mode=telegram.ParseMode.HTML)
        bot.sendMessage(chat_id = chat_id , text = "It's better for you not to drive.\
            \nWho do you want to contact?", reply_markup=ReplyKeyboardMarkup(reply_keyboard));
        
        #Set the booking not valid
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        cursor.execute(f"UPDATE ActiveBooking SET verified = 2 WHERE plate = '{plate}'")
        conn.commit()
        conn.close()

        return 'Booking not verified - alcohol test failed - message sent'

    elif len(data) != 0 and body["failed"] == False:
        #If the booking it's not failed, set it valid in the database'
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        cursor.execute(f"UPDATE ActiveBooking SET verified = 1 WHERE plate = '{plate}'")
        conn.commit()
        conn.close()
        return 'Booking verified'
    else:
        return 'No telegram user with this @username'
    
#Avvio dell'app flask
if __name__ == "__main__":
    app.run(host = '0.0.0.0', debug=True)
    
