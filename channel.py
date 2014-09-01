#-*- coding:utf-8 -*-

'''
snspocket: the container class for snsapi's

'''

__version__ = '1.1'

import json
import time
import kivy.resources
from os.path import join, exists
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, SwapTransition, \
     SlideTransition
from kivy.properties import ListProperty, StringProperty, \
        NumericProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.bubble import Bubble
from kivy.uix.spinner import Spinner
from kivy.clock import Clock

from sns import SNSView, SNSListItem, SNSPopup

from snsapi.snspocket import SNSPocket
from snsapi.utils import utc2str
# supported platform
EMAIL = 'Email'
RSS = 'RSS'
RSS_RW = 'RSS2RW'
RSS_SUMMARY = 'RSSSummary'
RENREN_BLOG = 'RenrenBlog'
RENREN_SHARE = 'RenrenShare'
RENREN_STATUS = 'RenrenStatus'
SQLITE = 'SQLite'
SINA_WEIBO = 'SinaWeiboStatus'
TENCENT_WEIBO = 'TencentWeiboStatus'
TWITTER = 'TwitterStatus'

APP = 'SNSReader'

class ChannelListItem(BoxLayout):

    channel_title = StringProperty()
    channel_name = StringProperty()
    channel_index = NumericProperty()
    channel_platform = StringProperty()

class Channel(Screen):
    channeldata = ListProperty()

    def channel_args_converter(self, row_index, item):
        return {
            'channel_index': row_index,
            'channel_title': item['title'],
            'channel_platform': item['platform'],
            'channel_name': item['name'],
            'channel_app_secret': item['app_secret'],
            'channel_app_key': item['app_key'],
            'channel_access_key':item['access_key'], 
            'channel_access_secret':item['access_secret'], 
            'channel_url': item['url'], 
            'channel_callback_url': item['callback_url']}
            
#the class for the channel setting screen	
class ChannelView(Screen):

    channel_index = NumericProperty()
    channel_title = StringProperty()
    is_create = BooleanProperty()
    
    channel_url = StringProperty()
    channel_platform = StringProperty()
    channel_name = StringProperty()
    channel_app_secret = StringProperty()
    channel_app_key = StringProperty()
    channel_callback_url = StringProperty()
    channel_access_key = StringProperty()
    channel_access_secret = StringProperty()
    former_channel_name = StringProperty()
    
    def check_all(self):
        self.platform_key_check()
        self.platform_callback_check()
        self.access_check()
        self.url_check()
    
    def platform_key_check(self):
        temp_platform = self.ids.w_platform.text
        if temp_platform in ('RenrenBlog', 'RenrenShare', 'RenrenStatus', 'SinaWeiboStatus', 'TencentWeiboStatus', 'TwitterStatus') :
            self.ids.w_app_secret.disabled = False
            self.ids.w_app_key.disabled = False
            if temp_platform in ('RenrenBlog', 'RenrenShare', 'RenrenStatus'):
                self.ids.w_app_key.text = 'e891bb00caac4a999a13b9bee7f5c835'
                self.ids.w_app_secret.text = '1729fea9bd784d27bd192cead2f90b45'
            elif temp_platform == 'SinaWeiboStatus':
                self.ids.w_app_key.text = '3102874688'
                self.ids.w_app_secret.text = 'b47a651d1b5be0127690f017965bd343'
            elif temp_platform == 'TencentWeiboStatus':
                self.ids.w_app_key.text = '801389477'
                self.ids.w_app_secret.text = 'bd002edff5670f64be610c7e143b3b18'
            elif temp_platform == 'TwitterStatus':
                self.ids.w_app_key.text = 'jNeenbpkNvGnGgR09AbXRQ'
                self.ids.w_app_secret.text = 'xOl31NQFrO9mn99tvvf5wmYBjeJT2V50gJNrPNHs6c'
        else:
            self.ids.w_app_secret.disabled = True
            self.ids.w_app_key.disabled = True
            
    def platform_callback_check(self):
        temp_platform = self.ids.w_platform.text
        if temp_platform in ('RenrenBlog', 'RenrenShare', 'RenrenStatus', 'SinaWeiboStatus', 'TencentWeiboStatus') :
            self.ids.w_callback_url.disabled = False
            self.ids.w_callback_url.text = 'http://snsapi.sinaapp.com/auth.php'
        else:
            self.ids.w_callback_url.disabled = True
            
    def access_check(self):
        temp_platform = self.ids.w_platform.text
        if temp_platform == 'TwitterStatus':
            self.ids.w_access_secret.disabled = False
            self.ids.w_access_key.disabled = False
            self.ids.w_access_secret.text = '4fk0WmEos6bTEMuA7cjYAjGNkmLqusQAzAkrbFgq3M'
            self.ids.w_access_key.text = '1599990409-keJcjxyibqjHkEdEeZ1LkvcIiw809I0N9HCvRRH'
        else:
            self.ids.w_access_secret.disabled = True
            self.ids.w_access_key.disabled = True
            
    def url_check(self):
        temp_platform = self.ids.w_platform.text
        if temp_platform in ('RSS') :
            self.ids.w_channel_url.disabled = False
        else:
            self.ids.w_channel_url.disabled = True


