# smartmirror.py
# requirements
# requests, traceback, Pillow

from tkinter import *
from lxml import etree
import locale
import threading
import time
import requests
import json
import traceback
import re

from PIL import Image, ImageTk
from contextlib import contextmanager

LOCALE_LOCK = threading.Lock()

ui_locale = '' # e.g. 'fr_FR' fro French, '' as default
time_format = 12 # 12 or 24
date_format = "%b %d, %Y" # check python doc for strftime() for options
weather_lang = 'en' # see https://darksky.net/dev/docs/forecast for full list of language parameters values
weather_unit = 'us' # see https://darksky.net/dev/docs/forecast for full list of unit parameters values
latitude = None # Set this if IP location lookup does not work for you (must be a string)
longitude = None # Set this if IP location lookup does not work for you (must be a string)
xlarge_text_size = 94
large_text_size = 48
medium_text_size = 28
small_text_size = 18
hefeng_api = '473adb5d75cb44c196c7d2a2babf6455'

@contextmanager
def setlocale(name): #thread proof function to work with locale
    with LOCALE_LOCK:
        saved = locale.setlocale(locale.LC_ALL)
        try:
            yield locale.setlocale(locale.LC_ALL, name)
        finally:
            locale.setlocale(locale.LC_ALL, saved)

# maps open weather icons to
# icon reading is not impacted by the 'lang' parameter
icon_lookup = {
    '晴日': "assets/Sun.png",  # clear sky day
    '风': "assets/Wind.png",   #wind
    '阴': "assets/Cloud.png",  # cloudy day
    '多云日': "assets/PartlySunny.png",  # partly cloudy day
    '雨': "assets/Rain.png",  # rain day
    '雪': "assets/Snow.png",  # snow day
    'snow-thin': "assets/Snow.png",  # sleet day
    '雾': "assets/Haze.png",  # fog day
    '晴月': "assets/Moon.png",  # clear sky night
    '多云月': "assets/PartlyMoon.png",  # scattered clouds night
    '雷雨': "assets/Storm.png",  # thunderstorm
    '龙卷风': "assests/Tornado.png",    # tornado
    '冰雹': "assests/Hail.png"  # hail
}


class Clock(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, bg='black')
        # initialize time label
        self.time1 = ''
        self.timeLbl = Label(self, font=('Helvetica', large_text_size), fg="white", bg="black")
        self.timeLbl.pack(side=TOP, anchor=E)
        # initialize day of week
        self.day_of_week1 = ''
        self.dayOWLbl = Label(self, text=self.day_of_week1, font=('Helvetica', small_text_size), fg="white", bg="black")
        self.dayOWLbl.pack(side=TOP, anchor=E)
        # initialize date label
        self.date1 = ''
        self.dateLbl = Label(self, text=self.date1, font=('Helvetica', small_text_size), fg="white", bg="black")
        self.dateLbl.pack(side=TOP, anchor=E)
        self.tick()

    def tick(self):
        with setlocale(ui_locale):
            if time_format == 12:
                time2 = time.strftime('%I:%M %p') #hour in 12h format
            else:
                time2 = time.strftime('%H:%M') #hour in 24h format

            day_of_week2 = time.strftime('%A')
            date2 = time.strftime(date_format)
            # if time string has changed, update it
            if time2 != self.time1:
                self.time1 = time2
                self.timeLbl.config(text=time2)
            if day_of_week2 != self.day_of_week1:
                self.day_of_week1 = day_of_week2
                self.dayOWLbl.config(text=day_of_week2)
            if date2 != self.date1:
                self.date1 = date2
                self.dateLbl.config(text=date2)
            # calls itself every 200 milliseconds
            # to update the time display as needed
            # could use >200 ms, but display gets jerky
            self.timeLbl.after(200, self.tick)


class Weather(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, bg='black')
        self.temperature = ''
        self.forecast = ''
        self.location = ''
        self.currently = ''
        self.icon = ''
        self.degreeFrm = Frame(self, bg="black")
        self.degreeFrm.pack(side=TOP, anchor=W)
        self.temperatureLbl = Label(self.degreeFrm, font=('Helvetica', xlarge_text_size), fg="white", bg="black")
        self.temperatureLbl.pack(side=LEFT, anchor=N)
        self.iconLbl = Label(self.degreeFrm, bg="black")
        self.iconLbl.pack(side=LEFT, anchor=N, padx=20)
        self.currentlyLbl = Label(self, font=('Helvetica', small_text_size), fg="white", bg="black")
        self.currentlyLbl.pack(side=TOP, anchor=W)
        self.forecastLbl = Label(self, font=('Helvetica', small_text_size), fg="white", bg="black")
        self.forecastLbl.pack(side=TOP, anchor=W)
        self.locationLbl = Label(self, font=('Helvetica', medium_text_size), fg="white", bg="black")
        self.locationLbl.pack(side=TOP, anchor=W)
        self.get_weather()

    def get_ip(self):
        try:
            ip_url = "https://ifconfig.co/"
            req = requests.get(ip_url).text
            tree = etree.HTML(req)
            result = tree.xpath('/html/body/div/div[1]/div[1]/div/p[1]/code/text()')[0]
            print(result)
            return result
        except Exception as e:
            traceback.print_exc()
            return "Error: %s. Cannot get ip." % e

    def get_weather(self):
        global weather_req_url2, weather_forecast
        try:

            if latitude is None and longitude is None:
                # get location
                location_req_url = "http://ip-api.com/json/%s?lang=zh-CN" % self.get_ip()
                r = requests.get(location_req_url)
                location_obj = json.loads(r.text)

                lat = location_obj['lat']
                lon = location_obj['lon']

                location2 = "%s" % (location_obj['city'])

                # get weather

                location2_id_url = "https://geoapi.qweather.com/v2/city/lookup?location=%s&key=%s" % (location2, hefeng_api)
                r = requests.get(location2_id_url)
                location_id_obj = json.loads(r.text)
                # print(location_id_obj)
                location2_id = location_id_obj['location'][0]['id']
                weather_req_url1 = "https://devapi.qweather.com/v7/weather/now?location=%s&key=%s" % (location2_id, hefeng_api)
                weather_req_url2 = "https://www.qweather.com/weather/%s.html" % location2_id
                weather_forecast = "https://www.qweather.com/pcpn/%s.html" % location2_id
            else:
                location2 = ""
                # get weather
                weather_req_url1 = "https://api.darksky.net/forecast/%s/%s,%s?lang=%s&units=%s" % (weather_api_token, latitude, longitude, weather_lang, weather_unit)

            r = requests.get(weather_req_url1)
            weather_obj = json.loads(r.text)
            response = requests.get(weather_req_url2)
            page_text = response.text
            tree = etree.HTML(page_text)
            result = tree.xpath('/html/body/div[3]/div[3]/div[1]/div[1]/div/div/div[3]/div/p/text()')[0]
            result = re.findall(r'\S+', result)
            b = ""
            for a in result:
                b += " "
                b += a
            result = b
            print(result)
            icon_id = tree.xpath('/html/body/div[3]/div[3]/div[1]/div[1]/div/div/div[2]/div[2]/div/div[2]/text()')[0]
            degree_sign = u'\N{DEGREE SIGN}'    # 度数符号
            temperature2 = "%s%sC" % (str(int(weather_obj['now']['temp'])), degree_sign)
            currently2 = result
            response = requests.get(weather_forecast)
            page_text = response.text
            tree = etree.HTML(page_text)
            result = tree.xpath('/html/body/div[3]/div[3]/div/div[1]/div[1]/div/h3/text()')[0]
            forecast2 = result
            # print(result)
            tm = int(re.findall(r'(\d+):', time.strftime('%H:%M'))[0])
            icon2 = None
            if 18 > tm >= 6:
                if icon_id == '晴':
                    icon_id = '晴日'
                elif icon_id == '多云':
                    icon_id = '多云日'
            else:
                if icon_id == '晴':
                    icon_id = '晴月'
                elif icon_id == '多云':
                    icon_id = '多云月'

            if icon_id in icon_lookup:
                icon2 = icon_lookup[icon_id]

            if icon2 is not None:
                if self.icon != icon2:
                    self.icon = icon2
                    image = Image.open(icon2)
                    image = image.resize((100, 100), Image.ANTIALIAS)
                    image = image.convert('RGB')
                    photo = ImageTk.PhotoImage(image)

                    self.iconLbl.config(image=photo)
                    self.iconLbl.image = photo
            else:
                # remove image
                self.iconLbl.config(image='')

            if self.currently != currently2:
                self.currently = currently2
                self.currentlyLbl.config(text=currently2)
            if self.forecast != forecast2:
                self.forecast = forecast2
                self.forecastLbl.config(text=forecast2)
            if self.temperature != temperature2:
                self.temperature = temperature2
                self.temperatureLbl.config(text=temperature2)
            if self.location != location2:
                if location2 == ", ":
                    self.location = "Cannot Pinpoint Location"
                    self.locationLbl.config(text="Cannot Pinpoint Location")
                else:
                    self.location = location2
                    self.locationLbl.config(text=location2)
        except Exception as e:
            traceback.print_exc()
            print("Error: %s. Cannot get weather." % e)

        self.after(600000, self.get_weather)

    @staticmethod
    def convert_kelvin_to_fahrenheit(kelvin_temp):
        return 1.8 * (kelvin_temp - 273) + 32


class News(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, *args, **kwargs)
        self.config(bg='black')
        self.title = 'News' # 'News' is more internationally generic
        self.newsLbl = Label(self, text=self.title, font=('Helvetica', medium_text_size), fg="white", bg="black")
        self.newsLbl.pack(side=TOP, anchor=W)
        self.headlinesContainer = Frame(self, bg="black")
        self.headlinesContainer.pack(side=TOP)
        self.get_headlines()

    def get_headlines(self):
        try:
            # remove all children
            for widget in self.headlinesContainer.winfo_children():
                widget.destroy()
                
            headlines_url = "https://s.weibo.com/top/summary"
            page_text = requests.get(headlines_url).text
            tree = etree.HTML(page_text)
            result = tree.xpath('//*[@id="pl_top_realtimehot"]/table/tbody/tr')

            for post in result[1:6]:
                headline = post.xpath('./td[2]/a/text()')[0]
                self.newsLbl1 = Label(self.headlinesContainer, text=headline, font=('Helvetica', small_text_size), fg="white", bg="black")
                self.newsLbl1.pack(side=TOP, anchor=W)
        except Exception as e:
            traceback.print_exc()
            print("Error: %s. Cannot get news." % e)

        self.after(600000, self.get_headlines)


class FullscreenWindow:

    def __init__(self):
        self.tk = Tk()
        self.tk.configure(background='black')
        self.topFrame = Frame(self.tk, background = 'black')
        self.bottomFrame = Frame(self.tk, background = 'black')
        self.topFrame.pack(side = TOP, fill=BOTH, expand = YES)
        self.bottomFrame.pack(side = BOTTOM, fill=BOTH, expand = YES)
        self.state = False
        self.tk.bind("<Return>", self.toggle_fullscreen)
        self.tk.bind("<Escape>", self.end_fullscreen)
        # clock
        self.clock = Clock(self.topFrame)
        self.clock.pack(side=RIGHT, anchor=N, padx=100, pady=60)
        # weather
        self.weather = Weather(self.topFrame)
        self.weather.pack(side=LEFT, anchor=N, padx=100, pady=60)
        # news
        self.news = News(self.bottomFrame)
        self.news.pack(side=LEFT, anchor=S, padx=100, pady=60)

    def toggle_fullscreen(self, event=None):
        self.state = not self.state  # Just toggling the boolean
        self.tk.attributes("-fullscreen", self.state)
        return "break"

    def end_fullscreen(self, event=None):
        self.state = False
        self.tk.attributes("-fullscreen", False)
        return "break"

if __name__ == '__main__':
    w = FullscreenWindow()
    w.tk.mainloop()
