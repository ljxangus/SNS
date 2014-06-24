#-*- coding:utf-8 -*-

'''
This is the app for the SNSDroid Application

Windows version

ignoring the time and the conversion of timezone

'''

__version__ = '1.2'

import json
import time
import kivy
from kivy.config import Config
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
from kivy.uix.listview import ListView
from kivy.adapters.listadapter import ListAdapter
from kivy.factory import Factory

from snsapi.snspocket import SNSPocket
from snsapi.utils import utc2str

from sns import SNSView, SNSListItem, SNSPopup, UpdateStatus, ForwardStatus, ReplyStatus, MSSPopup
from channel import ChannelListItem, Channel,  ChannelView
from accessories import SaveConfigBubble,  PickPlatformView,  StatusBar,  GeneralOptions
from extract_keywords import extractKeywords

kivy.require('1.8.0')
Config.set('graphics', 'width', '640')
Config.set('graphics', 'height', '320')

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

class MutableTextInput(FloatLayout):

    text = StringProperty()
    multiline = BooleanProperty(True)

    def __init__(self, **kwargs):
        super(MutableTextInput, self).__init__(**kwargs)
        Clock.schedule_once(self.prepare, 0)
        
    def prepare(self,*args):
        self.w_textinput = self.ids.w_textinput.__self__
        self.w_label = self.ids.w_label.__self__
        self.view()

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and touch.is_double_tap:
            self.edit()
            return True
        return super(MutableTextInput, self).on_touch_down(touch)

    def edit(self):
        self.clear_widgets()
        self.add_widget(self.w_textinput)
        self.w_textinput.focus = True

    def view(self):
        self.clear_widgets()
        self.add_widget(self.w_label)

    def check_focus_and_view(self, textinput):
        if not textinput.focus:
            self.text = textinput.text
            self.view()

class SNS(Screen):
    original_sns_data = dict()
    keywordDict = dict()
    snsdata = ListProperty()
    channeldata = ListProperty()
    all_status = []
    first_status = None
    
    def __init__(self, **kwargs):
        super(SNS, self).__init__(**kwargs)
        self.ch = list(sp.keys())
        self.current_channel_intext = 'All Platform'
        self.current_channel=None
        self.ids._channel_spinner.bind(text=self.change_channel)
        self.ch.sort()
        self.ch.insert(0, 'All Platform')
        self.ids._channel_spinner.values = self.ch

    def change_channel(self, spinner, text):
        channel = spinner.text
        if not channel or channel == self.current_channel: return
        self.current_channel = channel != 'All Platform' and channel or None
        self.current_channel_intext = channel != 'All Platform' and channel or 'All Platform'
        print 'self.current_channel_intext is ' + self.current_channel_intext
        print 'self.current_channel is ' 
        print self.current_channel
        return True
        
    def insert_status(self,status,status_index = None):
        if status in self.all_status:
            return False

        if status_index is None:status_index = len(self.all_status)

        self.all_status.insert(status_index,status)
        self.__insert_status(status,status_index)
		
        self.getKeywords(status)
        return True

    def __insert_status(self,status,index):
        data = status.parsed
        try: text = data.title
        except: text = data.text
        title_text = '%s said,' % (data.username)
        content_text = text
        self.snsdata.append({'title':title_text, 'content':content_text})

    def getKeywords(self,status):
        tags = extractKeywords(status)
        for tag in tags:
            if keywordDict[tag]:
                keywordDict[tag]
            else:
                keywordDict = 1

    def sns_args_converter(self, row_index, item):
        return {
            'sns_index': row_index,
            'sns_content': item['content'],
            'sns_title': item['title']}

    def refresh_status(self):
        temp_length = len(self.snsdata)
        del self.all_status[0:len(self.all_status)]
        del self.snsdata[0:len(self.snsdata)]
        if not self.current_channel == None:
            if temp_length>0:
                hl = sp.home_timeline(temp_length, self.current_channel)
            else:
                hl = sp.home_timeline(10, self.current_channel)
        else:
            hl = sp.home_timeline(10, self.current_channel)

        i = 0
        global first_status
        if len(hl)>0:
            first_status = hl[0]
        for s in hl:
            if self.insert_status(s, i):
                i += 1
                
        print "length of sns data "+ str(len(self.snsdata))
        print 'the type of snsdata is '+str(type(self.snsdata))
        print 'the type of all_status is '+str(type(self.all_status))
        return True
        
    def more_status(self):
        n  = len(self.all_status) + len(sp) * 5
        more_home_timeline = sp.home_timeline(n)
        first_in_more = len(more_home_timeline)
        global first_status
        i = 0
        for sta in more_home_timeline:
            if sta == first_status:
                first_in_more = i
                print 'first status in more status ' + str(i)
                break
            i+=1
        print first_status
        
        i=0
        j=0
        for sta in more_home_timeline:
            if i >= first_in_more+10:
                if self.insert_status(sta, j):
                    j+=1
                    print i, j
                    #print sta
            i += 1
        print "length of snsdata "+ str(len(self.snsdata))
        return True
        
class SNSApp(App):
    
    def build(self):
        
        #load kv file
        Builder.load_file('layout/sns.kv')
        Builder.load_file('layout/sns_popup.kv')
        Builder.load_file('layout/channel_view.kv')
        Builder.load_file('layout/sns_list_layout.kv')
        Builder.load_file('layout/channel_list_layout.kv')
        Builder.load_file('layout/post_status.kv')
        
        self.sns = SNS(name='sns')
        #self.channel = Channel(name='channel')
        #self.sns.snsdata.append({'content':"Hi", 'title':'Testing1'})
        
        self.load_channel()
        self.transition = SlideTransition(duration=.35)
        root = ScreenManager(transition=self.transition)
        root.add_widget(self.sns)
        
        self.choose_status_index = 0

        #for s in sp.home_timeline(10):
            #self.sns.insert_status(s)
        
        return root

    def load_channel(self):
        if not exists(self.channel_fn):
            return
        with open(self.channel_fn,'rb') as fd:
            channeldata = json.load(fd)
        self.sns.channeldata = channeldata
        
        
    def save_channel(self):
        with open(self.channel_fn, 'wb') as fd:
            json.dump(self.sns.channeldata, fd)
        sp.save_config()
            
    def del_channel(self,channel_index):
        if sp[self.sns.channeldata[channel_index]['name']]:
            del sp[self.sns.channeldata[channel_index]['name']]
        del self.sns.channeldata[channel_index]
        self.save_channel() #include save_config()
        self.refresh_channel()
        self.go_channel()
        
    def edit_channel(self,channel_index, channel_platform='', is_create=False):
        channel = self.sns.channeldata[channel_index]
        
        if not channel_platform == '':
            channel['platform'] = channel_platform
        name = 'channel{}'.format(channel_index)
        
        if self.root.has_screen(name):
            self.root.remove_widget(self.root.get_screen(name))
            
        view = ChannelView(
            name=name,
            channel_index=channel_index,
            channel_title=channel.get('title'),
            channel_platform=channel.get('platform'),
            channel_name=channel.get('name'),
            channel_app_secret=channel.get('app_secret'),
            channel_app_key=channel.get('app_key'),
            channel_access_key=channel.get('access_key'),
            channel_access_secret=channel.get('access_secret'),
            channel_url=channel.get('url'), 
            channel_callback_url=channel.get('callback_url'), 
            is_create = is_create, 
            former_channel_name = channel.get('name'))
        
        self.root.add_widget(view)
        self.transition.direction = 'left'
        self.root.current = view.name
        view.check_all()

    def edit_channel_in_pocket(self, channel_index, former_channel_name):
        # edit the existing channel in the snspocket
        channel = self.sns.channeldata[channel_index]
        temp_channel_platform = channel.get('platform')
        temp_channel_name = former_channel_name
        temp_channel = sp[temp_channel_name].jsonconf
        
        temp_channel['platform'] = channel.get('platform')
        temp_channel['channel_name'] = channel.get('name')
        
        if temp_channel_platform in ('RenrenBlog', 'RenrenShare', 'RenrenStatus', 'SinaWeiboStatus', 'TencentWeiboStatus', 'TwitterStatus', ) :
            temp_channel['app_secret'] = channel.get('app_secret')
            temp_channel['app_key'] = channel.get('app_key')
        
        if temp_channel_platform in ('TwitterStatus', ):
            temp_channel['access_secret'] = channel.get('access_secret')
            temp_channel['access_key'] = channel.get('access_key')
         
        if temp_channel_platform in ('RSS', ):
            temp_channel['url'] = channel.get('url')

        if temp_channel_platform in ('RenrenBlog', 'RenrenShare', 'RenrenStatus', 'SinaWeiboStatus', 'TencentWeiboStatus', ) :
            temp_channel['auth_info']['callback_url'] = channel.get('callback_url')
         
        print temp_channel
         
        self.save_channel()
        sp.auth()
        
    def add_channel_to_pocket(self,channel_index, is_create, former_channel_name=''):
        #add to the snspocket
        channel = self.sns.channeldata[channel_index]
        temp_channel_platform = channel.get('platform')
        
        if is_create:
            SNSChannel = sp.new_channel()
        
            SNSChannel['platform'] = channel.get('platform')
            SNSChannel['channel_name'] = channel.get('name')
        
            if temp_channel_platform in ('RenrenBlog', 'RenrenShare', 'RenrenStatus', 'SinaWeiboStatus', 'TencentWeiboStatus', 'TwitterStatus', ) :
                SNSChannel['app_secret'] = channel.get('app_secret')
                SNSChannel['app_key'] = channel.get('app_key')
        
            if temp_channel_platform in ('TwitterStatus', ):
                SNSChannel['access_secret'] = channel.get('access_secret')
                SNSChannel['access_key'] = channel.get('access_key')
         
            if temp_channel_platform in ('RSS', ):
                SNSChannel['url'] = channel.get('url')
                print 'channel get url is: ' + channel.get('url')

            if temp_channel_platform in ('RenrenBlog', 'RenrenShare', 'RenrenStatus', 'SinaWeiboStatus', 'TencentWeiboStatus', ) :
                SNSChannel['auth_info']['callback_url'] = channel.get('callback_url')
        
            print SNSChannel

            sp.add_channel(SNSChannel)
            sp.auth(SNSChannel['channel_name'])
            
        else:
            self.edit_channel_in_pocket(channel_index, former_channel_name)
        
        self.save_channel()
        self.go_channel()

    def add_channel(self):
        #self.pick_platform()
        self.sns.channeldata.append({'title': 'New Channel',
                                     'content': '',
                                     'platform':'',
                                     'name':'',
                                     'app_secret':'',
                                     'app_key':'',
                                     'access_key':'', 
                                     'access_secret':'', 
                                     'url':'', 
                                     'callback_url':''})
        channel_index = len(self.sns.channeldata) - 1
        self.edit_channel(channel_index,'', True)

    def view_channel(self):
        name = 'channel'
        if self.root.has_screen(name):
            self.root.remove_widget(self.root.get_screen(name))
        view = Channel(
            name = name,
            channeldata=self.sns.channeldata)

        self.root.add_widget(view)
        self.transition.direction = 'left'
        self.root.current = view.name
        
    
    def set_channel_content(self, channel_index, channel_content, content):
        self.sns.channeldata[channel_index][content] = channel_content
        channeldata = self.sns.channeldata
        self.sns.channeldata = []
        self.sns.channeldata = channeldata
        #self.save_channel()
        self.refresh_channel_data()
    

    def set_channel_title(self, channel_index, channel_title):
        self.sns.channeldata[channel_index]['title'] = channel_title
        #self.save_channel()
        self.refresh_channel_data()

    def refresh_status_sns(self):
        self.choose_status_index = None
        self.sns.refresh_status()
        snsdata = self.sns.snsdata
        self.sns.snsdata = []
        self.sns.snsdata = snsdata
        
    def more_status_sns(self):
        self.sns.more_status()
        #self.sns.remove_widget(self.sns.ids._list_status)
        snsdata = self.sns.snsdata
        self.sns.snsdata = []
        self.sns.snsdata = snsdata
        #list_adapter = ListAdapter(data=self.sns.snsdata, cls=Factory.SNSListItem, args_converter=self.sns.sns_args_converter)
        #new_list_view = ListView(id = '_list_status', adapter = list_adapter)
        #self.sns.add_widget(new_list_view)
        
    def refresh_channel(self):
        self.sns.refresh_status()
        channeldata = self.sns.channeldata
        self.sns.channeldata = []
        self.sns.channeldata = channeldata
        
    def refresh_channel_data(self):
        channeldata = self.sns.channeldata
        self.sns.channeldata = []
        self.sns.channeldata = channeldata

    def go_sns(self):
        sp.clear_channel()
        sp.load_config()
        name = 'sns'
        if self.root.has_screen(name):
            self.root.remove_widget(self.root.get_screen(name))
        view = SNS(
            name = name,
            channeldata=self.sns.channeldata)

        self.root.add_widget(view)
        self.transition.direction = 'right'
        self.root.current = view.name

    def go_channel(self):
        name = 'channel'
        if self.root.has_screen(name):
            self.root.remove_widget(self.root.get_screen(name))
        view = Channel(
            name = name,
            channeldata=self.sns.channeldata)

        self.root.add_widget(view)
        self.transition.direction = 'right'
        self.root.current = view.name
    
    def save_config(self):
        sp.save_config()

    def auth_channel(self):
        sp.auth()
        
    def click_sns(self, snsindex):
        print snsindex
        new_sns_popup = SNSPopup()
        new_sns_popup.change_index(snsindex)
        print 'popup has index ' + str(new_sns_popup.sns_index)
        new_sns_popup.open()
        
    def show_status(self, snsindex):
        self.choose_status_index = snsindex
        new_content_popup = MSSPopup(sns_index=snsindex)
        new_content_popup.change_index(snsindex, 
                                       self.sns.snsdata[snsindex]['title'], 
                                       self.sns.snsdata[snsindex]['content'])
        print 'StatusMSSPopup has index ' + str(new_content_popup.sns_index)
        new_content_popup.open()
        print self.sns.snsdata[new_content_popup.sns_index]['content']
        
    def forward_status(self, message, text):
        print 'forward_status to ' + self.sns.current_channel_intext 
        sp.forward(message, text, self.sns.current_channel)
        
    def reply_status(self, message, text):
        print 'reply_status to ' + message.ID.channel
        sp.reply(message, text)
        
    def update_status(self, post_content):
        print 'update_status to ' + self.sns.current_channel_intext
        print post_content
        if sp.update(post_content, self.sns.current_channel):
            return True
        else:
            return False
        
    def go_update_status(self):
        name = 'update_status'
        if self.root.has_screen(name):
            self.root.remove_widget(self.root.get_screen(name))
        view = UpdateStatus(
            name = name)

        self.root.add_widget(view)
        self.transition.direction = 'left'
        self.root.current = view.name
        
    def go_forward_status(self, sns_index):
        name = 'forward_status'
        if self.root.has_screen(name):
            self.root.remove_widget(self.root.get_screen(name))
        view = ForwardStatus(
            name = name,
            message = self.sns.snsdata[sns_index]['content'], 
            text='')
        view.change_original_message(self.sns.all_status[sns_index])

        self.root.add_widget(view)
        self.transition.direction = 'left'
        self.root.current = view.name
        
    def go_reply_status(self, sns_index):
        name = 'reply_status'
        if self.root.has_screen(name):
            self.root.remove_widget(self.root.get_screen(name))
        view = ReplyStatus(
            name = name,
            message = self.sns.snsdata[sns_index]['content'], 
            text='')
        view.change_original_message(self.sns.all_status[sns_index])

        self.root.add_widget(view)
        self.transition.direction = 'left'
        self.root.current = view.name
    
    def go_sns_quietly(self):
        self.transition.direction = 'right'
        self.root.current = 'sns'
        
    @property
    def channel_fn(self):
        channel_fn = 'conf/sns.json'
        return channel_fn
        #return join(self.user_data_dir, 'sns.json')
        
if __name__=="__main__":
    sp = SNSPocket()
    sp.load_config()
    sp.auth()
    SNSApp().run()
    sp.save_config()

#-----------helper function-------------#
def channel_exist(channel, channel_list):
    for ch in channel_list:
        if ch['channel_name'] == channel['channel_name']:
            return True
    return False
    
