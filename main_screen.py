'''
This is the app for the SnSDroid Application

'''

__version__ = '1.0'

import json
import time
from os.path import join, exists
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.properties import ListProperty, StringProperty, \
        NumericProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.clock import Clock

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

class SNSView(Screen):

    sns_index = NumericProperty()
    sns_title = StringProperty()
    sns_content = StringProperty()

#the class for the channel editting screen	
class ChannelView(Screen):

    channel_index = NumericProperty()
    channel_title = StringProperty()
    channel_content = StringProperty()

class StatusBar(BoxLayout):
    time_str = StringProperty()
    connection_status = StringProperty()

    def __init__(self, **kwargs):
        super(StatusBar, self).__init__(**kwargs)
        Clock.schedule_interval(self.update, 0.5)

    def update(self,*args):
        self.time_str = time.strftime("%b %d %H:%M:%S")
        self.connection_status = 'Yes'

#class for the sns list view in the main screen
class SNSListItem(BoxLayout):

    sns_title = StringProperty()
    sns_index = NumericProperty()

class ChannelListItem(BoxLayout):

    channel_title = StringProperty()
    channel_index = NumericProperty()
    
class Channel(Screen):
    channeldata = ListProperty()

    def channel_args_converter(self, row_index, item):
        return {
            'channel_index': row_index,
            'channel_content': item['content'],
            'channel_title': item['title']}

class SNS(Screen):
    snsdata = ListProperty()
    channeldata = ListProperty()

    def sns_args_converter(self, row_index, item):
        return {
            'sns_index': row_index,
            'sns_content': item['content'],
            'sns_title': item['title']}
			
class GeneralOptions(BoxLayout):
	channel_index = NumericProperty()
	channel_info = ListProperty()
	
class SNSApp(App):
    
    def build(self):
        self.sns = SNS(name='sns')
        #self.channel = Channel(name='channel')
        self.load_channel()
        
        self.transition = SlideTransition(duration=.35)
        root = ScreenManager(transition=self.transition)
        root.add_widget(self.sns)
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
			
    def del_channel(self,channel_index):
	del self.sns.channeldata[channel_index]
	self.save_channel()
	self.refresh_channel()
	self.go_channel()
		
    def edit_channel(self,channel_index):
	channel = self.sns.channeldata[channel_index]
	name = 'channel{}'.format(channel_index)
		
	if self.root.has_screen(name):
	    self.root.remove_widget(self.root.get_screen(name))
			
	view = ChannelView(
            name=name,
            channel_index=channel_index,
            channel_title=channel.get('title'),
            channel_content=channel.get('content'))
	
	self.root.add_widget(view)
        self.transition.direction = 'left'
        self.root.current = view.name            
		
    def add_channel(self):
	self.sns.channeldata.append({'title': 'New Channel', 'content': ''})
	channel_index = len(self.sns.channeldata) - 1
	self.edit_channel(channel_index)
#channelinformation needed
	
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
			
    def set_channel_content(self, channel_index, channel_content):
	self.sns.channeldata[channel_index]['content'] = channel_content
	channeldata = self.sns.channeldata
	self.sns.channeldata = []
	self.sns.channeldata = channeldata
	self.save_channel()
	self.refresh_channel()
			
    def set_channel_title(self, channel_index, channel_title):
        self.sns.channeldata[channel_index]['title'] = channel_title
        self.save_channel()
        self.refresh_channel()

    def refresh_sns(self):
        snsdata = self.sns.snsdata
        self.sns.snsdata = []
        self.sns.snsdata = snsdata
		
    def refresh_channel(self):
        channeldata = self.sns.channeldata
        self.sns.channeldata = []
        self.sns.channeldata = channeldata

    def go_sns(self):
        self.transition.direction = 'right'
        self.root.current = 'sns'

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
	
    @property
    def channel_fn(self):
        return join(self.user_data_dir, 'sns.json')

if __name__=="__main__":
    SNSApp().run()
