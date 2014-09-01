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
from kivy.uix.image import AsyncImage, Image
import re
        
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
    link = StringProperty()
    sns_indexinlist = 0
    startTime = 0
    attachments = None
    digest_info= None
    def change_index(self, index, title, content, indexinlist,start,attach=None,digest_informoation=None):
        self.sns_index = index
        self.title_data = title #app.sns.snsdata[index]['title']
        self.content_data = content #app.sns.snsdata[index]['content']
        self.sns_indexinlist = indexinlist
        self.startTime = start
        self.attachments = attach
        self.digest_info = digest_informoation
        try:
            self.link = re.search("(?P<url>https?://[^\s]+)", self.content_data).group("url")
        except:
            pass
        self.content_data = DividingUnicode.div(self.content_data, 20)
        
    def add_attachments(self):
        if self.attachments == None:
            return False
        
        attachment_layout = self.ids.w_popup_attachments
        
        #---------------------Add the attachment to the itemview----------------------# 
        for att in self.attachments:
            if att['type'] == 'picture':
                try: index = att['format'].index('link')
                except: index = None
                if index != None:
                    att_image = AsyncImage(source=att['data'],halign='top',valign='left')
                    attachment_layout.add_widget(att_image)
                
        #---------------------------------------------------------------------#
        return True
        
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
        
class DividingUnicode:
    @staticmethod
    def div(unicodestr,divlength=20):
        '''
            HERE we need to divide the text manually, so that 
            they can shown in the right form and can \n automatically 
            according to the screen size.
        '''
        tempstr = []
        j=0
        #The divide length of the unicode string
        DIVLENGTH = divlength
    
        for i in range(len(unicodestr)):
            if i%DIVLENGTH==0 and i!=0:
                tempstr.append(unicodestr[i-DIVLENGTH:i])
                j=i
            if len(unicodestr)-i<DIVLENGTH:
                tempstr.append(unicodestr[j:len(unicodestr)])
                break
    
        mergestr = unicode()
        for stri in tempstr:
            mergestr = mergestr + stri + ' '
        
        return mergestr
        
