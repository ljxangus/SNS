# Kivy

### Basic App

Hello world

    import kivy

	from kivy.app import App
	from kivy.unix.label import Label

	class MyApp(App):

    	def build(self):
        	return Label(text='Hello world')

	if __name=='__main__':
    	MyApp().run()

Notes:

  * Create app inheriting App class `from kivy.app import App`. The file is save in /kivy/app.py (check if necessary)
  * `from kivy.uix.label import Label`One important thing to note here is the way packages/classes are laid out. The `uix` module is the section that holds the user interface elements like layouts and widgets.
  * In this function we need to initialize and return the ***Root Widget***

### Kivy Life cycle
![](https://dl.dropboxusercontent.com/u/106605049/summer%20research/Kivy/cycle.jpg)

Next: [Customized the app](Customized-app)

This app contains Username/Password
~~~~
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput

class LoginScreen(GridLayout):
    def __init__(self, **kwargs):
        super(LoginScreen, self).__init__(**kwargs)
        self.cols=2
        self.add_widget(Label(text='UserName'))
        self.username = TextInput(multiline=False)
        self.add_widget(self.username)
        self.add_widget(Label(text='Password'))
        self.password = TextInput(password=True,multiline=False)
        self.add_widget(self.password)

class MyApp(App):
    def build(self):
        return LoginScreen()

if __name__=='__main__':
    MyApp().run()

~~~~
Notes:

* Call `super()` in order to implement the functionality of the original class being overloaded. Don't  omit `**kwargs`.
* GridLayout will take care of its children in two columns.

Kivy Architecture Overview
![](https://dl.dropboxusercontent.com/u/106605049/summer%20research/Kivy/architecture%20overview.jpg)

Notes:

* ***KivyLanguage*** The kivy language is used to easily and efficiently describe user interfaces.
* UIX modules containis commonly used widgets and layouts
* Widgets -- elements that provides functionality
* Layouts -- the arrangement of widgets
* Input Events(Touch) -- **Down, Up, Move**

### Touch event handling

```
def on_touch_down(self, touch):
    for child in self.children[:]:
        if child.dispatch('on_touch_down', touch):
            return True
```

* Widgets are tree-like structure, handling will be done in like traverse the tree
* If we want to let the widget only watch the area inside it, we can use the method `collide_point()` to achieve this. Pass the touch position to it and it will return `True` or `False`.

### Events Handling of Kivy
![](https://dl.dropboxusercontent.com/u/106605049/summer%20research/Kivy/Event%20Handling.jpg)

#### Main loop of Kivy app

```
while True:
	animate_something()
	time.sleep(.10)
```

##### Schedulaing a repetive event
```
def my_callback(dt):
    print 'My callback is called',dt
Clock.schedule_interval(my_callback, 1/  30.)
```

When the event need to exit, just add `Clock.unschedule(my_callback)`

Scheduling one-time event:`Clock.schedule_once(my_callback,1)`

##### Widget Events
There two types of events:
* Property event:when change the size and position
* Widget-defined event: e.g. when the button is pressed or released

Bingding to the property
`your_widget_instance.bind(property_name=function_name)`

Example code

```
#binding to the property
class RootWidget(BoxLayout):
    def __init__(self, **kwargs):
        super(RootWidget, self).__init__(**kwargs)
        self.add_widget(Button(text='btn 1'))
        cb = CustomBtn()
        cb.bind(pressed=self.btn_pressed)
        self.add_widget(cb)
        self.add_widgte(Button(ext='btn 2'))

    def btn_pressed(self, instance, pos):
        print ('pos: printed from root widget: {pos}'.format(pos=.pos))
```

## Input architecture
Global architecture can be reviewed as :
`Input providers -> Motion event -> Post processing -> Dispatch to Window`	

### How .kv file work with the .py script?
This is done when we use `App().run()`, inside the function, it will automatically call `load_kv()`. The default filename should be the same as the app's name.
e.g.
> Executing this application without a corresponding `.kv` file will work, but nothing will be shown on the screen. This is expected, because the Controller class has no widgets in it, it’s just a FloatLayout. We can create the UI around the Controller class in a file named `controller.kv`, which will be loaded when we run the ControllerApp.

