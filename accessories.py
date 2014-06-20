#-*- coding:utf-8 -*-

'''
This is the app for the SnSDroid Application

'''

__version__ = '1.1'

import json
import time
import kivy.resources
from kivy.uix.screenmanager import ScreenManager, Screen, SwapTransition, \
     SlideTransition
from kivy.properties import ListProperty, StringProperty, \
        NumericProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.bubble import Bubble
from kivy.clock import Clock


class SaveConfigBubble(Bubble):
    pass

class PickPlatformView(Screen):
    channel_platform = StringProperty()
    channel_index = NumericProperty()

class StatusBar(BoxLayout):
    time_str = StringProperty()
    connection_status = StringProperty()

    def __init__(self, **kwargs):
        super(StatusBar, self).__init__(**kwargs)
        Clock.schedule_interval(self.update, 0.5)

    def update(self,*args):
        self.time_str = time.strftime("%b %d %H:%M:%S")
        self.connection_status = 'Yes'

class GeneralOptions(BoxLayout):
	channel_index = NumericProperty()
	channel_info = ListProperty()
	
