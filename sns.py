#-*- coding:utf-8 -*-

'''
snspocket: the container class for snsapi's

'''

__version__ = '1.1'

from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ListProperty, StringProperty, \
        NumericProperty, BooleanProperty, DictProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
        
class SNSView(Screen):

    sns_index = NumericProperty()
    sns_title = StringProperty()
    sns_content = StringProperty()

#class for the sns list view in the main screen
class SNSListItem(BoxLayout):

    sns_title = StringProperty()
    sns_content = StringProperty()
    sns_index = NumericProperty()
    
class SNSPopup(Popup):
    #channel_data = ListProperty()
    #sns_data = ListProperty()
    sns_index = 0
    channelID = ''
    def change_index(self, index):
        self.sns_index = index
        
class MSSPopup(Popup):
    sns_index = 0
    channelID = ''
    title_data = StringProperty()
    content_data= StringProperty()
    def change_index(self, index, title, content):
        self.sns_index = index
        self.title_data = title #app.sns.snsdata[index]['title']
        self.content_data = content #app.sns.snsdata[index]['content']
        
class UpdateStatus(Screen):
    post_content = StringProperty()
    
class ForwardStatus(Screen):
    original_message = dict()
    message = StringProperty()
    text = StringProperty()
    def change_original_message(self, message):
        self.original_message = message
    
class ReplyStatus(Screen):
    original_message = dict()
    message = StringProperty()
    text = StringProperty()
    def change_original_message(self, message):
        self.original_message = message
