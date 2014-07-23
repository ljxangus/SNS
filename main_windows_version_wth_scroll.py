#-*- coding:utf-8 -*-
'''
This is the app for the SNSDroid Application

Windows version

ignoring the time and the conversion of timezone

'''

__version__ = '1.4'

import json
import time
import kivy
from kivy.logger import Logger
from kivy.config import Config
import kivy.resources
import kivy.clock
import webbrowser

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
from kivy.uix.gridlayout import GridLayout
from kivy.uix.bubble import Bubble
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from kivy.uix.listview import ListView
from kivy.adapters.listadapter import ListAdapter
from kivy.factory import Factory
from kivy.core.window import Window
from kivy.uix.image import AsyncImage, Image

from snsapi.snspocket import SNSPocket
from snsapi.utils import utc2str

from sns import SNSView, SNSListItem, SNSPopup, UpdateStatus, ForwardStatus, ReplyStatus, MSSPopup, DividingUnicode
from channel import ChannelListItem, Channel,  ChannelView
from accessories import SaveConfigBubble,  PickPlatformView,  StatusBar,  GeneralOptions, DropDownMenu, AboutPopup, HelpPopup
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
    statusList = ListProperty()
    snsdata = ListProperty()
    channeldata = ListProperty()
    all_status = []
    
    
    def __init__(self, **kwargs):
        super(SNS, self).__init__(**kwargs)
        self.ch = list(sp.keys())
        self.current_channel_intext = 'All Platform'
        self.current_channel=None
        self.ids._channel_spinner.bind(text=self.change_channel)
        self.ch.sort()
        self.ch.insert(0, 'All Platform')
        
        self.STATUS_SIZE = 20
        self.SHOW_ON_SCREEN_FREQUENCE = 0.5
        
        self.moreClickTimes = 0
        self.first_status = None
        self.ids._channel_spinner.values = self.ch
        self.dropdownmenu = DropDownMenu()
        
        self.statusGridLayout = GridLayout(cols=1, padding=5,size_hint=(1, None))
        self.statusGridLayout.bind(minimum_height=self.statusGridLayout.setter('height'))
        
        self.StatusListview = self.ids._scroll_view_status
        
        self.StatusListview.add_widget(self.statusGridLayout)
        
        if exists('conf/status.json'):
            with open('conf/status.json','rb') as fd:
                statusdata = json.load(fd)
            self.statusList = statusdata
            
        #binding test
        #self.StatusListview.bind(scroll_y=self.my_y_callback)
        Logger.debug ('The device window size is ' + str(Window.size))
        #for status in self.statusList:
         #   print status['status_content']

    def change_channel(self, spinner, text):
        channel = spinner.text
        if not channel or channel == self.current_channel: return
        self.current_channel = channel != 'All Platform' and channel or None
        self.current_channel_intext = channel != 'All Platform' and channel or 'All Platform'
        Logger.debug('self.current_channel_intext is ' + str(self.current_channel_intext))
        Logger.debug('self.current_channel is ' + str(self.current_channel))
        return True
        
    def insert_status(self,status,status_index = None):
        if status in self.all_status:
            return False

        if status_index is None:status_index = len(self.all_status)

        self.all_status.insert(status_index,status)
        self.__insert_status(status,status_index)
        return True

    def __insert_status(self,status,index):        
        data = status.parsed
        try: text = data.title
        except: text = data.text
        title_text = '%s said at %s,' % (data.username, data.time)
        #title_text = '%s at %s' % (data.username, utc2str(data.time))
        content_text = text
        
        try:origin_name = status.parsed.username_origin
        except:origin_name = None
        
        #---------------Finding attachment and handling----------------------#

        try: attachs = data.attachments
        except: attachs = None
        
        self.getKeywords(content_text,data.username,data.time,status.ID,origin_name,attachs,False)
        content_text = DividingUnicode.div(content_text,30)
        
        #-------------------status inserted to the snsdata------------------------#
                               
        self.snsdata.append({'title':title_text, 
                             'content':content_text, 
                             'name':data.username,
                             'time':data.time,
                             'ID':status.ID,
                             'origin_name':origin_name,
                             'attachments':attachs})
        #scroll view operation
        newItem = SNSListItem(sns_content=content_text,sns_title=title_text,sns_index=index)
        
        #---------------------Add the attachment to the itemview----------------------# 
        itemlayout = newItem.ids.attachment_layout_item
         
        for att in attachs:
            if att['type'] == 'picture':
                try: index = att['format'].index('link')
                except: index = None
                if index != None:
                    if att['data'].find('.gif') == -1:
                        att_image = AsyncImage(source=att['data'],size_hint_y=.2)
                        itemlayout.add_widget(att_image)
                        # break if only one image need add to the home time view
                        break
            elif att['type'] == 'link':
                Logger.info(att['data'])
                
        #---------------------------------------------------------------------#
        self.statusGridLayout.add_widget(newItem)

    def getKeywords(self,status_content,status_username=None,status_time=None,
                    statusID=None,username_origin=None,attachments=None,is_touch_in=False):
        '''
        to store full information, we did extract the keywords, 
        now we just save the full status to keep all useful information
        '''
        #tag version
        '''
        tags = extractKeywords(status)
        
        tagsInList = False
        index = 0
        for status in self.statusList:
            if tags == status['keywords']:
                index = self.statusList.index(status)
                status['frequency'] += 1
                tagsInList = True
        
        if not tagsInList:
            self.statusList.append({'keywords':tags,
                                    'frequency' : 1,
                                    'time' : 0,
                                    'like' :None,
                                    'currentTime' :time.strftime("%b %d %H:%M:%S")
                                    })
            index = len(self.statusList)-1
        '''
        #----------------------------------------------------#
        #full status version
        
        statusInList = False
        index = 0
        for status in self.statusList:
            if statusID == status['status_ID']:
                index = self.statusList.index(status)
                if is_touch_in:
                    status['frequency'] += 1
                statusInList = True
        
        if not statusInList:
            self.statusList.append({'status_ID':statusID,
                                    'status_content':status_content,
                                    'status_username':status_username,
                                    'user_name_origin':username_origin,
                                    'status_time':status_time,
                                    'frequency' : 0,
                                    'time' : 0,
                                    'like' :None,
                                    'currentTime' :time.strftime("%a, %d %b %Y %H:%M:%S"),
                                    'show_on_screen_time':0,
                                    'speed_of_on_Screen':0,
                                    'attachments_contain':attachments
                                    })
            index = len(self.statusList)-1
        #------------------------------------------------------#

        '''                        
        with open('conf/status.json', 'wb') as fd:
            json.dump(self.statusList, fd,indent = 2)
        '''
                
        return index

    def sns_args_converter(self, row_index, item):
        return {
            'sns_index': row_index,
            'sns_content': item['content'],
            'sns_title': item['title']}

    def refresh_status(self):
        Clock.unschedule(self.status_shown_on_screen)
        self.moreClickTimes = 0
        temp_length = len(self.snsdata)
        del self.all_status[0:len(self.all_status)]
        del self.snsdata[0:len(self.snsdata)]
        self.statusGridLayout.clear_widgets()
        
        if not self.current_channel == None:
            if temp_length>0:
                hl = sp.home_timeline(self.STATUS_SIZE+temp_length, self.current_channel)
            else:
                hl = sp.home_timeline(self.STATUS_SIZE, self.current_channel)
        else:
            hl = sp.home_timeline(self.STATUS_SIZE, self.current_channel)

        i = 0
        
        if len(hl)>0:
            self.first_status = hl[0]
            Logger.debug('first status inserted')
        for s in hl:
            if self.insert_status(s, i):
                i += 1
                
        Logger.debug("length of sns data " +str (len(self.snsdata)))        
        self.StatusListview.scroll_y = 1
        
        #schedule the clock
        Clock.schedule_interval(self.status_shown_on_screen, self.SHOW_ON_SCREEN_FREQUENCE)
        return True
        
    def more_status(self):
        Logger.debug('The length of the sp is ' + str(len(sp)))
        self.moreClickTimes = self.moreClickTimes + 1
        n  = len(self.all_status) + len(sp) * 10 * self.moreClickTimes
        Logger.debug('The number n is ' + str(n))
        more_home_timeline = sp.home_timeline(n,self.current_channel)
        first_in_more = len(more_home_timeline)
        
        if self.first_status == None:
            self.refresh_status()
            self.moreClickTimes = self.moreClickTimes - 1
            return False

        
        '''
        i = 0
        for sta in more_home_timeline:
            if sta == first_status:
                first_in_more = i
                print 'first status in more status ' + str(i)
                break
            i+=1
        '''
        
        #Find the original fisrt status    
        for i in range(len(more_home_timeline)):
            if more_home_timeline[i].parsed.text==self.first_status.parsed.text:
                first_in_more = i
                Logger.debug('first status in more status ' + str(i))
                break
        
        
        i=0
        j=len(self.snsdata)
        for sta in more_home_timeline:
            if i >= first_in_more+self.STATUS_SIZE:
                if self.insert_status(sta, j):
                    j+=1
                    #print i, j
            i += 1
        Logger.debug("length of sns data "+ str(len(self.snsdata)))
            
        self.StatusListview.scroll_y = 1
        return True
    
    def my_y_callback(self,obj, value):
        Logger.debug('on listview', obj, 'scroll y changed to', value)
        Logger.debug('The status on the screen is ', self.status_shown_on_screen(obj, value))
    
    def scroll_speed(self):
        pass
    
    def status_shown_on_screen(self,obj=None, scroll_y=None):
        if scroll_y == None:
            scroll_y = self.StatusListview.scroll_y
        
        head_status = round((1-scroll_y)*(len(self.snsdata)-2.8))
        status_list_height = Window.size[1] - 90
        status_per_screen = round(status_list_height / 150)
        tail_status = head_status + status_per_screen - 1
        
        #record the shown on screen time
        #for i in range(int(head_status),int(tail_status+1)):
            #self.statusList[i]['show_on_screen_time'] += self.SHOW_ON_SCREEN_FREQUENCE
        #Logger.debug('The shown status is ' + str(head_status) + ' to ' + str(tail_status))
        
        return (head_status,tail_status)
    
    def save_status_feedback(self,obj=None, value=None):
        with open('conf/status.json', 'wb') as fd:
            json.dump(self.statusList, fd,indent = 2)
        
class SNSApp(App):
    
    def build(self):
        
        #load kv file
        Builder.load_file('layout/sns.kv')
        Builder.load_file('layout/sns_popup.kv')
        Builder.load_file('layout/channel_view.kv')
        Builder.load_file('layout/scrollLayoutView.kv')
        Builder.load_file('layout/channel_list_layout.kv')
        Builder.load_file('layout/post_status.kv')
        
        self.sns = SNS(name='sns')
        #self.channel = Channel(name='channel')
        #self.sns.snsdata.append({'content':"Hi", 'title':'Testing1'})
        
        self.load_channel()
        self.transition = SlideTransition(duration=.35)
        root = ScreenManager(transition=self.transition)
        root.add_widget(self.sns)
        
        Config.read('config.ini')
        
        Config.set('graphics', 'height','1280')
        Config.set('graphics', 'width','720')
        
        Config.set('kivy','log_level','debug')
        Config.set('kivy','log_dir','logs')
        Config.set('kivy','log_enable ','1')
        Config.set('kivy','log_name','kivy_%y-%m-%d_%_.txt')
        Config.write()
        
        self.choose_status_index = 0
        Clock.schedule_interval(self.sns.save_status_feedback,5)
        
        time.clock()

        #for s in sp.home_timeline(10):
            #self.sns.insert_status(s)
        
        return root
    
    def on_start(self):
        print 'Program start.'
        
    def on_stop(self):
        self.sns.save_status_feedback()
        self.save_channel()
        self.save_config()
        
    def on_pause(self):
        return True
    
    def on_resume(self):
        pass

    def load_channel(self):
        if not exists(self.channel_fn):
            return
        with open(self.channel_fn,'rb') as fd:
            channeldata = json.load(fd)
        self.sns.channeldata = channeldata
        
        
    def save_channel(self):
        with open(self.channel_fn, 'wb') as fd:
            json.dump(self.sns.channeldata, fd, indent = 2)
        sp.save_config()
            
    def del_channel(self,channel_index):
        if self.sns.channeldata[channel_index]['name']!=u'':
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
         
        Logger.debug(temp_channel)
         
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
                Logger.debug('channel get url is: ' + channel.get('url'))

            if temp_channel_platform in ('RenrenBlog', 'RenrenShare', 'RenrenStatus', 'SinaWeiboStatus', 'TencentWeiboStatus', ) :
                SNSChannel['auth_info']['callback_url'] = channel.get('callback_url')
        
            #Logger.debug(SNSChannel)

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
        new_sns_popup = SNSPopup()
        new_sns_popup.change_index(snsindex)
        Logger.debug('popup has index ' + str(new_sns_popup.sns_index))
        new_sns_popup.open()
        
    def show_status(self, snsindex):
        self.choose_status_index = snsindex
        content = self.sns.snsdata[snsindex]['content']
        name = self.sns.snsdata[snsindex]['name']
        statustime = self.sns.snsdata[snsindex]['time']
        username_origin = self.sns.snsdata[snsindex]['origin_name']
        ID = self.sns.snsdata[snsindex]['ID']
        attachments = self.sns.snsdata[snsindex]['attachments']

        indexInStatusList = self.sns.getKeywords(content,name,statustime,ID,username_origin,attachments,True)
        
        new_content_popup = MSSPopup(sns_index=snsindex)
        Logger.debug('New popup build')
        startTime = time.clock()
        new_content_popup.change_index(snsindex, 
                                       self.sns.snsdata[snsindex]['title'], 
                                       content,
                                       indexInStatusList,
                                       startTime,
                                       attachments)
        Logger.debug('adding the attachments to the popup')
        
        new_content_popup.add_attachments()
        
        Logger.debug('StatusMSSPopup has index ' + str(new_content_popup.sns_index))
        
        new_content_popup.open()
        
        #print self.sns.snsdata[new_content_popup.sns_index]['content']
    
    def close_status(self, snsindex, starttime, like):
        self.sns.statusList[snsindex]['time'] += (time.clock()-starttime)
        self.sns.statusList[snsindex]['like'] = like
        
        with open('conf/status.json', 'wb') as fd:
            json.dump(self.sns.statusList, fd,indent = 2)
        
    def forward_status(self, message, text):
        Logger.debug('forward_status to ' + self.sns.current_channel_intext)
        sp.forward(message, text, self.sns.current_channel)
        
    def reply_status(self, message, text):
        Logger.debug('reply_status to ' + message.ID.channel)
        sp.reply(message, text)
        
    def update_status(self, post_content):
        Logger.debug('update_status to ' + self.sns.current_channel_intext)
        Logger.debug(post_content)
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
        
    def OpenDropDownMenu(self,obj):
        self.sns.dropdownmenu.open(obj)
        
    def aboutPopup(self):
        newAboutPopup = AboutPopup()
        newAboutPopup.open()
        
    def helpPopup(self):
        newHelpPopup = HelpPopup()
        newHelpPopup.open()
        
    def open_url(self,url):
        webbrowser.open(url)
        
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
    
