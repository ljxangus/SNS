#-*- coding:utf-8 -*-

'''
This is the app for the SNSDroid Application

created by Jonathan

'''

__version__ = '1.6'

import json
import time
import kivy
import sys
import shelve
import pickle
import sqlite3
import cPickle
# from kivy.logger import Logger
from kivy.config import Config
import kivy.resources
import kivy.clock
import webbrowser
import os

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
from appLog import SNSAPPLog as Logger

kivy.require('1.8.0')
#Config.set('graphics', 'width', '640')
#Config.set('graphics', 'height', '320')

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
running_platform = ''

'''
OS System and its 'code'
Linux (2.x and 3.x)    'linux2'
Windows    'win32'
Windows/Cygwin    'cygwin'
Mac OS X    'darwin'
OS/2    'os2'
OS/2 EMX    'os2emx'
RiscOS    'riscos'
AtheOS    'atheos'
'''

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
    status_duplicate_set = set()
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
        self.SHOW_ON_SCREEN_FREQUENCE = 1
        self.moreClickTimes = 0
        self.first_status = None
        self.ids._channel_spinner.values = self.ch
        
        self.formmer_head_status = 0
        self.formmer_tail_status = 0
        
        self.dropdownmenu = DropDownMenu()
        
        self.statusGridLayout = GridLayout(cols=1, padding=5,size_hint=(1, None))
        self.statusGridLayout.bind(minimum_height=self.statusGridLayout.setter('height'))
        
        self.StatusListview = self.ids._scroll_view_status
        
        self.StatusListview.add_widget(self.statusGridLayout)
        
        '''
        # status.json
        
        if exists('applog/status.json'):
            with open('applog/status.json','rb') as fd:
                statusdata = json.load(fd)
            self.statusList = statusdata
        '''    
        # status sqlite3
        self.status_sqlite3_cx = sqlite3.connect('applog/status_raw_data.db')
        self.status_sqlite3_cu = self.status_sqlite3_cx.cursor()
        try: 
            self.status_sqlite3_cu.execute("""create table status_raw_data (digest TEXT UNIQUE,raw_data BLOB,status_id BLOB, show_on_screen_time INT, click_times INT, show_detail_times INT, like TEXT, currentTime TEXT)""")
            Logger.system_info("status database","Created")
        except sqlite3.Error,e: 
            print 'database create error',"\n", e.args[0]
        self.status_sqlite3_cx.commit()
        
        '''
        try:
            with open('applog/status_duplicated.pickle','rb') as fd:
                self.status_duplicate_set = pickle.load(fd)
        except:
            self.status_duplicate_set = set()
        '''
        
        #binding test
        #self.StatusListview.bind(scroll_y=self.my_y_callback)
        Logger.system_info('The device window size is ' + str(Window.size),'[No Action]')
        Logger.device_behaviour('The device window size is ' + str(Window.size),'[No Action]')
        #for status in self.statusList:
         #   print status['status_content']

    def change_channel(self, spinner, text):
        channel = spinner.text
        if not channel or channel == self.current_channel: return
        self.current_channel = channel != 'All Platform' and channel or None
        self.current_channel_intext = channel != 'All Platform' and channel or 'All Platform'
        Logger.system_info('self.current_channel_intext is ' + str(self.current_channel_intext))
        Logger.system_info('self.current_channel is ' + str(self.current_channel))

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
        
        global running_platform
        if running_platform == 'win32':
            title_text = '%s said at %s,' % (data.username, data.time)
        elif running_platform == 'linux3':
            title_text = '%s at %s' % (data.username, utc2str(data.time))
        elif running_platform == 'darwin':
        	title_text = '%s at %s' % (data.username, utc2str(data.time))
        content_text = text
        
        try:origin_name = status.parsed.username_origin
        except:origin_name = None
        
        digest_info = status.digest()
		
        #---------------Finding attachment and handling----------------------#

        try: attachs = data.attachments
        except: attachs = None
        
        
        #status.json
        #self.getKeywords(content_text,data.username,data.time,status.ID,origin_name,attachs,False,digest_info,status.raw)
        
            
        content_text = DividingUnicode.div(content_text,30)
        
        #-------------------status inserted to the snsdata------------------------#
                               
        self.snsdata.append({'title':title_text, 
                             'content':content_text, 
                             'name':data.username,
                             'time':data.time,
                             'ID':status.ID,
                             'origin_name':origin_name,
                             'attachments':attachs,
                             'digest_info':digest_info,
                             'raw':status.raw,
                             'platform':status.platform,
                             'show_on_screen_time':0,
                             'click_times' : 0,
                             'show_detail_times' : 0,
                             'like' :None,
                             'currentTime' :time.strftime("%a, %d %b %Y %H:%M:%S")})
        #scroll view operation
        newItem = SNSListItem(sns_content=content_text,sns_title=title_text,sns_index=index)
        
        #---------------------Add the attachment to the itemview----------------------# 
        if attachs == None:
            newItem.ids.w_sns_item_content.size_hint_y = None
            
        
        itemlayout = newItem.ids.attachment_layout_item
         
        for att in attachs:
            if att['type'] == 'picture':
                try: index = att['format'].index('link')
                except: index = None
                if index != None:
                    if att['data'].find('.gif') == -1:
                        att_image = AsyncImage(source=att['data'],size_hint_y=.2)
                        newItem.ids.w_sns_item_content.size_hint_y = 0.6
                        itemlayout.add_widget(att_image)
                        # break if only one image need add to the home time view
                        break
            elif att['type'] == 'link':
                Logger.system_info (str(att['data']))
        #----------------------Save the duplicated status to database----------------#
        if running_platform == 'win32':
            self.save_depulicated_status_win32(status)
        elif running_platform == 'linux3':
            pass
        
        self.statusGridLayout.add_widget(newItem)

    def getKeywords(self,status_content,status_username=None,status_time=None,statusID=None,username_origin=None,attachments=None,is_touch_in=False, \
                    digest_info=None,raw=None):

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
        '''
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
        '''
        statusInList = False
        index = 0
        for status in self.statusList:
            if digest_info == status['digest_info']:
                index = self.statusList.index(status)
                statusInList = True
        
        if not statusInList:
            self.statusList.append({'status_ID':statusID,
                                    'digest_info':digest_info,
                                    'raw':raw,
                                    'show_on_screen_time':0
                                    })
            index = len(self.statusList)-1
        #------------------------------------------------------#
                         
        '''
        with open('applog/status.json', 'wb') as fd:
            json.dump(self.statusList, fd,indent = 2)
        '''
                

        return index

    def sns_args_converter(self, row_index, item):
        return {
            'sns_index': row_index,
            'sns_content': item['content'],
            'sns_title': item['title']}

    def refresh_status(self):
        self.save_status_feedback()
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
            Logger.system_info('No status','First status inserted')
        for s in hl:
            if self.insert_status(s, i):
                i += 1
        
        Logger.system_info("Length of sns data " +str (len(self.snsdata)))        
        
        self.StatusListview.scroll_y = 1
        self.formmer_head_status=0
        self.formmer_tail_status=0
        '''
        if running_platform == 'linux3':
            self.save_depulicated_status_android()
            with open('applog/status_duplicated.pickle','wb') as fd:
                pickle.dump(self.status_duplicate_set, fd)
        
        #status json
        with open('applog/status.json', 'wb') as fd:
            json.dump(self.statusList, fd,indent = 2)
        '''
        self.save_status_feedback()
        #schedule the clock
        Clock.schedule_interval(self.status_shown_on_screen, self.SHOW_ON_SCREEN_FREQUENCE)
        return True
    
    def more_status_robust(self):
        self.save_status_feedback()
        Clock.unschedule(self.status_shown_on_screen)
        Logger.system_info('No status','More status clicked')
        self.moreClickTimes = self.moreClickTimes + 1
        n  = len(self.all_status) + len(sp) * 10 * self.moreClickTimes
        
        del self.all_status[0:len(self.all_status)]
        del self.snsdata[0:len(self.snsdata)]
        self.statusGridLayout.clear_widgets()
        
        if self.first_status == None:
            self.refresh_status()
            self.moreClickTimes = self.moreClickTimes - 1
            return False
        
        hl = sp.home_timeline(n, self.current_channel)

        i = 0
        
        if len(hl)>0:
            self.first_status = hl[0]
        for s in hl:
            if self.insert_status(s, i):
                i += 1
        
        Logger.system_info("Length of sns data " +str (len(self.snsdata)))        
        
        self.StatusListview.scroll_y = 1
        self.formmer_head_status=0
        self.formmer_tail_status=0
        '''
        if running_platform == 'linux3':
            #self.save_depulicated_status_android()
            with open('applog/status_duplicated.pickle','wb') as fd:
                pickle.dump(self.status_duplicate_set, fd)
        
        with open('applog/status.json', 'wb') as fd:
            json.dump(self.statusList, fd,indent = 2)
        '''
        
        self.save_status_feedback()
        #schedule the clock
        Clock.schedule_interval(self.status_shown_on_screen, self.SHOW_ON_SCREEN_FREQUENCE)
        return True
        
    def more_status(self):
        Logger.system_info('The length of the sp is ' + str(len(sp)))
        self.moreClickTimes = self.moreClickTimes + 1
        n  = len(self.all_status) + len(sp) * 10 * self.moreClickTimes
        Logger.system_info('The number n is ' + str(n))
        more_home_timeline = sp.home_timeline(n,self.current_channel)
        first_in_more = len(more_home_timeline)
        
        if self.first_status == None:
            self.refresh_status()
            self.moreClickTimes = self.moreClickTimes - 1
            return False
        
        #Find the original fisrt status    
        for i in range(len(more_home_timeline)):
            if more_home_timeline[i].parsed.text==self.first_status.parsed.text:
                first_in_more = i
                Logger.system_info('No status','First status in more status ' + str(i))
                break
        
        
        i=0
        j=len(self.snsdata)
        for sta in more_home_timeline:
            if i >= first_in_more+self.STATUS_SIZE:
                if self.insert_status(sta, j):
                    j+=1
            i+=1
        
        Logger.system_info("Length of sns data "+ str(len(self.snsdata)))
            
        self.StatusListview.scroll_y = 1
        self.formmer_head_status=0
        self.formmer_tail_status=0
        self.save_status_feedback()
        return True
    
    def my_y_callback(self,obj, value):

        Logger.system_info('No status','On listview'+ str(obj) + 'scroll y changed to' + str(value))
        Logger.system_info('The status on the screen is '+ str(self.status_shown_on_screen(obj, value)))
    
    def status_shown_on_screen(self,obj=None, scroll_y=None):        
        if scroll_y == None:
            scroll_y = self.StatusListview.scroll_y
        '''    
        head_status = int(round((1-scroll_y)*(len(self.snsdata)-2.8)))
        status_list_height = Window.size[1] - 90
        status_per_screen = int(round(status_list_height / 150))
        tail_status = head_status + status_per_screen - 1
        '''
        status_list_height = self.StatusListview.height
        statusNum_per_screen = status_list_height/150
        per_status_height_percentage = 150/(150*len(self.snsdata)-self.StatusListview.height)
        head_status = round((1-scroll_y)/per_status_height_percentage)
        tail_status = round(head_status + statusNum_per_screen - 1)
        
        head_status = int(head_status)
        tail_status = int(tail_status)
        
        #record the shown on screen time
        if tail_status <= 0:
            temp_tail_status = 0
        elif tail_status >= len(self.snsdata):
            temp_tail_status = len(self.snsdata) - 1
        else:
            temp_tail_status = tail_status
        
        tail_status = temp_tail_status
            
        #for i in range(int(head_status),temp_tail_status):
            #self.statusList[i]['show_on_screen_time'] += self.SHOW_ON_SCREEN_FREQUENCE
        '''
        TODO: Calculate the status enter-top, enter-bottom, leave-top, leave-bottom 
        '''
        enter_top = None
        enter_bottom = None
        leave_top = None
        leave_bottom = None
        
        if head_status < self.formmer_head_status:
            enter_top = head_status
            leave_bottom = self.formmer_tail_status
            #Logger.status_user(self.snsdata[enter_top]['digest_info'],'Enter top status')
            #Logger.status_user(self.snsdata[leave_bottom]['digest_info'],'Leave bottom status')
            self.formmer_head_status = head_status
            self.formmer_tail_status = tail_status
        elif head_status > self.formmer_head_status:
            leave_top = self.formmer_head_status
            enter_bottom = tail_status
            #Logger.status_user(self.snsdata[leave_top]['digest_info'],'Leave top status')
            #Logger.status_user(self.snsdata[enter_bottom]['digest_info'],'Enter bottom status')
            self.formmer_head_status = head_status
            self.formmer_tail_status = tail_status
        else:
            self.formmer_head_status = head_status
            self.formmer_tail_status = tail_status
        
        #print('The shown status is ' + str(head_status) + ' to ' + str(tail_status))
        for i in range(head_status,tail_status):
            self.snsdata[i]['show_on_screen_time'] += self.SHOW_ON_SCREEN_FREQUENCE
            self.snsdata[i]['currentTime'] = time.strftime("%a, %d %b %Y %H:%M:%S")
        return (head_status,tail_status)
    
    def save_status_feedback(self,obj=None, value=None):
        '''
        for status in self.snsdata:
            for sta in self.statusList:
                if status['digest_info'] == sta['digest_info']:
                    sta['show_on_screen_time'] = status['show_on_screen_time']
        
        with open('applog/status.json', 'wb') as fd:
            json.dump(self.statusList, fd,indent = 2)
        '''
        a = None
        for status in self.snsdata:
            temp_command = "select * from status_raw_data where digest ='" + status['digest_info'] +"'"
            try:
                self.status_sqlite3_cu.execute(temp_command)
                a = self.status_sqlite3_cu.fetchone()
                #print 'select the status successfully in database'
            except sqlite3.Error,e:
                print "Select error","\n", e.args[0]
                continue
            if a != None:
                'show_on_screen_time INT, click_times INT, show_detail_times INT, like TEXT, currentTime TEXT'
                show_on_time = a[3] + status['show_on_screen_time']
                click_times = a[4] + status['click_times']
                show_detail_times = a[5] + status['show_detail_times']
                like = status['like']
                if like == None:
                    like = 'NULL'
                else:
                    like = str(like)
                currentTime = status['currentTime']
                if currentTime == None:
                    currentTime = 'NULL'
                else:
                    currentTime = str(currentTime)
                update_command = "UPDATE status_raw_data SET show_on_screen_time = "+str(show_on_time)+\
                    ", click_times = "+str(click_times)+\
                    ", show_detail_times = "+str(show_detail_times)+\
                    ", like = '"+ like +\
                    "', currentTime = '"+ currentTime +\
                    "' WHERE digest = '"+ status['digest_info']+"';"
                try:
                    self.status_sqlite3_cu.execute(update_command)
                    #print 'update status successfully in database'
                except sqlite3.Error,e:
                    print update_command
                    print "Update status error","\n", e.args[0]
                    continue
            else:
                insert_command = "insert into status_raw_data (digest, raw_data, status_id, show_on_screen_time, click_times, show_detail_times, like, currentTime) values (?,?,?,?,?,?,?,?);"
                raw_data = cPickle.dumps(status['raw'], cPickle.HIGHEST_PROTOCOL)
                status_id = cPickle.dumps(status['ID'], cPickle.HIGHEST_PROTOCOL)
                like = status['like']
                if like == None:
                    like = 'NULL'
                else:
                    like = str(like)
                currentTime = status['currentTime']
                if currentTime == None:
                    currentTime = 'NULL'
                else:
                    currentTime = str(currentTime)
                temp_insert = (status['digest_info'],
                               sqlite3.Binary(raw_data),
                               sqlite3.Binary(status_id),
                               status['show_on_screen_time'],
                               status['click_times'],
                               status['show_detail_times'],
                               like,
                               currentTime)
                try:
                    self.status_sqlite3_cu.execute(insert_command,temp_insert)
                    #print 'insert status successfully in database'
                except sqlite3.Error,e:
                    print "Insertion Error","\n", e.args[0]
                    continue
        self.status_sqlite3_cx.commit()
        Logger.system_info('No status','status database saved')
        return
                   
    def save_depulicated_status_win32(self,status):
        s = shelve.open('applog/status_hash.bat')
        flag = s.has_key(status.digest())
        
        checked_status = {'ID':status.ID,
                          'raw':status.raw,
                          'platform':status.platform}
        if flag == True:
            s.close()
            return
        else:
            s[status.digest()] = checked_status
        
        s.close()
        return
    
    def save_depulicated_status_android(self):
        status_database = open('applog/status_database.pickle','wb')
        for status in self.snsdata:
            if status['digest_info'] in self.status_duplicate_set:
                continue
            else:
                checked_status = {'ID':status['ID'],
                                  'raw':status['raw'],
                                  'platform':status['platform']}
            
                self.status_duplicate_set.add(status['digest_info'])
                pickle.dump(checked_status, status_database)
        
        status_database.close()
        return
        
class SNSApp(App):
    
    def build(self):
        global running_platform
        #load kv file
        Builder.load_file('layout/sns.kv')
        Builder.load_file('layout/sns_popup.kv')
        Builder.load_file('layout/channel_view.kv')
        Builder.load_file('layout/channel_list_layout.kv')
        Builder.load_file('layout/post_status.kv')
        if running_platform == 'win32' or 'darwin':
            Builder.load_file('layout/scrollLayoutView.kv')
        elif running_platform == 'linux3':
            Builder.load_file('layout/scrollLayoutView_android.kv')
        
        self.sns = SNS(name='sns')
        
        self.load_channel()
        self.transition = SlideTransition(duration=.35)
        root = ScreenManager(transition=self.transition)
        root.add_widget(self.sns)
        
        '''
        Config.read('config.ini')
        Config.set('graphics', 'height','1280')
        Config.set('graphics', 'width','720')
        Config.set('kivy','log_level','debug')
        Config.set('kivy','log_dir','logs')
        Config.set('kivy','log_enable ','1')
        Config.set('kivy','log_name','kivy_%y-%m-%d_%_.txt')
        Config.write()
        '''
        
        self.choose_status_index = 0
        
        # status.json
        # Clock.schedule_interval(self.sns.save_status_feedback,5)
        
        time.clock()

        #for s in sp.home_timeline(10):
            #self.sns.insert_status(s)
        Logger.system_info('No status','APP build')
        return root
        
    def on_stop(self):
        self.database_save()
        self.save_channel()
        self.save_config()
        Logger.system_info('No status','APP on_stop()')
        Logger.device_stop()
        
    def on_pause(self): 
        self.databse_pause_save()
        self.save_channel()
        self.save_config()
        Logger.system_info('No status','APP on_pause()')
        Logger.device_pause()
        return True
    
    def on_resume(self):
        Logger.system_info('No status','APP on_resume()')
    
    def database_save(self):
        self.sns.save_status_feedback()
        self.sns.status_sqlite3_cu.close()
        self.sns.status_sqlite3_cx.close()
    
    def databse_pause_save(self):
        self.sns.save_status_feedback()
        
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
         
        Logger.system_info('No status','Temp channel added' + str(temp_channel) )
         
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
                Logger.system_info('No status','Channel get url is: ' + channel.get('url'))

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
        self.sns.more_status_robust()
        snsdata = self.sns.snsdata
        self.sns.snsdata = []
        self.sns.snsdata = snsdata
        
    def refresh_channel(self):
        #self.sns.refresh_status()
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
        Logger.system_info('Popup has index ' + str(new_sns_popup.sns_index),'Popup shown')
        
        Logger.status_user(self.sns.snsdata[snsindex]['digest_info'],'Status clicked by user')
        self.sns.snsdata[snsindex]['click_times'] += 1
        new_sns_popup.open()
        
    def show_status(self, snsindex):
        self.choose_status_index = snsindex
        content = self.sns.snsdata[snsindex]['content']
        name = self.sns.snsdata[snsindex]['name']
        statustime = self.sns.snsdata[snsindex]['time']
        username_origin = self.sns.snsdata[snsindex]['origin_name']
        ID = self.sns.snsdata[snsindex]['ID']
        attachments = self.sns.snsdata[snsindex]['attachments']
        digest_info = self.sns.snsdata[snsindex]['digest_info']
        raw = self.sns.snsdata[snsindex]['raw']
        
        Logger.status_user(digest_info,'Details of this status shown')
        
        '''
        #status.json
        global running_platform
        if running_platform == 'win32':
            indexInStatusList = self.sns.getKeywords(content,name,statustime,ID,username_origin,attachments,True,digest_info,raw)
        else:
            indexInStatusList = self.sns.getKeywords(content,name,utc2str(statustime),ID,username_origin,attachments,True,digest_info,raw)
        '''
        
        new_content_popup = MSSPopup(sns_index=snsindex)
        Logger.system_info('No status','New popup build')
        startTime = time.clock()
        new_content_popup.change_index(snsindex, 
                                       self.sns.snsdata[snsindex]['title'], 
                                       content,
                                       snsindex,
                                       startTime,
                                       attachments,
                                       self.sns.snsdata[snsindex]['digest_info'])
        Logger.system_info('No status','Adding the attachments to the popup')
        
        new_content_popup.add_attachments()
        
        Logger.system_info('StatusMSSPopup has index ' + str(new_content_popup.sns_index),'MSSPopup Added')
        Logger.status_user(self.sns.snsdata[snsindex]['digest_info'],'Status details popup shown')
        
        new_content_popup.open()
        
        #print self.sns.snsdata[new_content_popup.sns_index]['content']
    
    def close_status(self, snsindex, starttime, like):
        
        self.sns.snsdata[snsindex]['show_detail_times'] += 1
        self.sns.snsdata[snsindex]['like'] = like
        '''
        with open('applog/status.json', 'wb') as fd:
            json.dump(self.sns.statusList, fd,indent = 2)
        '''
        if like==True:
            Logger.status_user(self.sns.snsdata[snsindex]['digest_info'],'User like the status')
        elif like==False:
            Logger.status_user(self.sns.snsdata[snsindex]['digest_info'],'User dislike the status')
        else:
            Logger.status_user(self.sns.snsdata[snsindex]['digest_info'],'User do not care the status')
        
        Logger.status_user(self.sns.snsdata[snsindex]['digest_info'],'Status detail popup closed')
        
    def forward_status(self, message, text):
        Logger.status_user('No status','Forward_status to ' + message.ID.channel)
        Logger.status_user(text,'Forward status comment')
        sp.forward(message, text, message.ID.channel)
        
    def reply_status(self, message, text):
        Logger.status_user('No status','Reply_status to ' + message.ID.channel)
        Logger.status_user(text,'Reply status comment')
        sp.reply(message, text)
        
    def update_status(self, post_content):
        Logger.status_user('No status','Update_status to ' + self.sns.current_channel_intext)
        Logger.status_user(post_content,'Updated status content')
        
        if sp.update(post_content, self.sns.current_channel):
            return True
        else:
            return False
        
    def go_update_status(self, sns_index):
        name = 'update_status'
        if self.root.has_screen(name):
            self.root.remove_widget(self.root.get_screen(name))
        view = UpdateStatus(name = name)

        self.root.add_widget(view)
        self.transition.direction = 'left'
        self.root.current = view.name
        
        Logger.status_user(self.sns.snsdata[sns_index]['digest_info'],'Update a status')
        
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
        
        Logger.status_user(self.sns.snsdata[sns_index]['digest_info'],'Forward the status')
        
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
        
        Logger.status_user(self.sns.snsdata[sns_index]['digest_info'],'Reply the status')
    
    def go_sns_quietly(self):
        self.transition.direction = 'right'
        self.root.current = 'sns'
        
        Logger.user_behaviour('No status','Go back to home timeline view')
        
    def OpenDropDownMenu(self,obj):
        self.sns.dropdownmenu.open(obj)
        
    def aboutPopup(self):
        newAboutPopup = AboutPopup()
        newAboutPopup.open()
        
    def helpPopup(self):
        newHelpPopup = HelpPopup()
        newHelpPopup.open()
        
    def open_url(self,url,digest_info=None):
        Logger.status_user(digest_info,'Open the url in status')
        webbrowser.open(url)
        
    @property
    def channel_fn(self):
        channel_fn = 'conf/sns.json'
        return channel_fn
        #return join(self.user_data_dir, 'sns.json')
        
if __name__=="__main__":
    running_platform = sys.platform
    if not os.path.exists('applog'):
        os.mkdir('applog')
    Logger.device_start()
    Logger.system_info('Running platform is: '+ running_platform)
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
    
