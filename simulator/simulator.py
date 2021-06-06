import random, requests, mysql.connector
from threading import Timer
from kivymd.app import MDApp
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import IconLeftWidget, ThreeLineIconListItem, IconRightWidget
from kivymd.uix.button import MDFlatButton
import os

#MySQL Database credential, hosted on freemysqlhosting.net - valid username and password hidden
config = {
  'user': os.environ.get('USER'),
  'password': os.environ.get('PASSWORD'),
  'host': 'sql11.freemysqlhosting.net',
  'database': os.environ.get('DATABASE'),
  'raise_on_warnings': True
}



catalog_url = 'http://localhost:9090/'

TELEGRAM_NAME = ''

CARS_LIST = []
Window.size = (375,667)


class Booking(ThreeLineIconListItem):
    """Booking Screen"""

    def on_press(self):
        dialog_text = "Do you confirm booking this car?"
        self.dialog = MDDialog(title = "Book this car", text = dialog_text, size_hint=(0.8, 1),
                                        buttons=[MDFlatButton(text='Close', on_release=self.close_dialog),
                                        MDFlatButton(text='Start Booking', on_release=self.start_booking)]
                               )
        self.dialog.open()
    
    def close_dialog(self,obj):
        self.dialog.dismiss()

    def start_booking(self,obj):
        """
            When a booking starts, the related username and car plate are stored in the Active Booking table.
            The car will aviability of the car will change in the car.
        """
        global TELEGRAM_NAME
        self.dialog.dismiss()
        dialog_text = 'Your booking will start as soon as the security test is done!'
        self.dialog = MDDialog(title = "Safety first!", text = dialog_text, size_hint=(0.8, 1),
                                        buttons=[MDFlatButton(text='Cancel Booking', on_release=self.cancel_booking)]
                               )
        self.dialog.open()
        requests.post(catalog_url + 'booking', json={'plate': self.text}) #set busy the car in the catalogue

        try:
            conn = mysql.connector.connect(**config)
            cursor = conn.cursor()
            query = "INSERT INTO ActiveBooking (plate, tg_username) VALUES (%s,%s)"
            cursor.execute(query,(self.text,TELEGRAM_NAME))
            conn.commit()
            conn.close()
            timer = Timer(3.0, self.check_booking_validity)
            timer.start()

        except Exception as e:
            print('Error' + str(e))

    def cancel_booking(self,obj):
        """
            When a booking end, the related record in Active Booking is deleted.
        """
        self.dialog.dismiss()
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        query = "DELETE From ActiveBooking where plate = %s and tg_username = %s"
        cursor.execute(query,(self.text,TELEGRAM_NAME))
        conn.commit()
        conn.close()

        requests.post(catalog_url + 'deletebooking', json={'plate': self.text}) #make the car available again in the catalogue


    def check_booking_validity(self):
        """
            Check the booking record in Active Booking untie the 'Validity' fields changes.
            - if validity = 0 the booking has not been processed yet;
            - if validity = 1 the alcohol test is done with a negative result, user can drive; 
            - if validity = 2 the alcohol test is done with a positive result, user can't drive; 
        """
        while True:
            conn = mysql.connector.connect(**config)
            cursor = conn.cursor()
            query = "SELECT * From ActiveBooking where plate = %s and tg_username = %s"
            cursor.execute(query,(self.text,TELEGRAM_NAME))
            booking_record = cursor.fetchone()
            conn.close()
            if booking_record[3] == 0:
                print('Not valid')
            elif booking_record[3] == 1:
                timer = Timer(1.0, self.valid_booking)
                timer.start()
                break

            elif booking_record[3] == 2:
                timer = Timer(1.0, self.invalid_booking)
                timer.start()
                break

    def valid_booking(self):
        """
            Show successful booking dialog
        """
        self.dialog.dismiss()
        dialog_text = 'Your booking is running, press cancel to stop it!'
        self.dialog = MDDialog(title = "Your Booking is running!", text = dialog_text, size_hint=(0.8, 1),
                                        buttons=[MDFlatButton(text='Cancel Booking', on_release=self.cancel_booking)]
                               )
        self.dialog.open()


    def invalid_booking(self):
        """
            Show unsuccessful booking dialog
        """
        self.dialog.dismiss()
        dialog_text = 'It seems like you drank too much!'
        self.dialog = MDDialog(title = "You are not allowed to drive!", text = dialog_text, size_hint=(0.8, 1),
                                        buttons=[MDFlatButton(text='Cancel Booking', on_release=self.cancel_booking)]
                               )
        self.dialog.open()


class LoginScreen(Screen):

    def login(self):
        """
            Fetch username and password from input box and compare them with the one stored in the db
            for user login.
        """

        global TELEGRAM_NAME

        email = self.ids.email.text
        password = self.ids.password.text

        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM User where email = '{email}'")
        user_record = cursor.fetchone()

        if user_record != None and user_record[3] == password:
            TELEGRAM_NAME = user_record[1]
            self.manager.current = "carlist"
        else:
            self.show_alert_dialog()
    
    def show_alert_dialog(self):
        text_error = "Username or password wrong"
        dialog = MDDialog(title = "Error", text = text_error, size_hint=(0.8, 1))
        dialog.open()


class RegisterScreen(Screen):
    """Allows user registration"""
    
    def register(self):
        """
            Simple registration method. Need to acquire user telegram name.
            Fetch data from input box and store them in db.
        """
        email = self.ids.email.text
        telegram_username = self.ids.telegram.text
        password = self.ids.password.text
        password_two = self.ids.password_two.text

        try:
            if password == password_two:
                conn = mysql.connector.connect(**config)
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM User where email = '{email}'")
                data = cursor.fetchall()
                if len(data) == 0:
                    query = "INSERT INTO User(email,tg_username,password) VALUES (%s,%s,%s)"
                    cursor.execute(query,(email,telegram_username,password))
                    conn.commit()           
                    conn.close()

                    confirm_text = "You have been successfully registered! Now open telegram and start a chat with @Car2SafeBot. Follow the instructions to have your emergency number saved!"
                    self.dialog = MDDialog(title = "Success" , text = confirm_text,size_hint=(0.8, 1),
                    buttons=[MDFlatButton(text='Close', on_release=self.close_dialog)])
                    self.dialog.open()
                    self.manager.current = "login"

                else:
                    self.dialog = MDDialog(title = "Error" , text = "User already exists!",size_hint=(0.8, 1),
                    buttons=[MDFlatButton(text='Close', on_release=self.close_dialog)])
                    self.dialog.open()
            else:
                self.dialog = MDDialog(title = "Error" , text = "Passwords do not match!",size_hint=(0.8, 1),
                buttons=[MDFlatButton(text='Close', on_release=self.close_dialog)])
                self.dialog.open()

        except Exception as e:
            print('problem' + str(e))
        
    def close_dialog(self,obj):
        self.dialog.dismiss()


class CarListScreen(Screen):

    def on_pre_enter(self):
        """
            For each car of the list create a dummy element in the listview
        """
        distance = 10
        for plate in CARS_LIST:

            fuel = random.randint(20,100)
            icon = IconLeftWidget(icon = "car")
            item = Booking(text = plate,secondary_text = f"Fuel: {fuel}%", tertiary_text= f"Distance: {distance}m")
            item.add_widget(icon)
            self.ids.container.add_widget(item)
            distance += 15


class Simulator(MDApp):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(CarListScreen(name='carlist'))
        sm.add_widget(RegisterScreen(name='register'))
        return 

    def on_start(self):
        """
            Fetch the list of the available cars from the catalog
        """
        global CARS_LIST
        CARS_LIST = (requests.get(catalog_url+'carlist')).json()
        



if __name__ == "__main__":
    Simulator().run()