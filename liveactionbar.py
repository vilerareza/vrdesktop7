from kivy.lang import Builder
from kivy.uix.gridlayout import GridLayout
from mylayoutwidgets import ImageButton, ImageToggle
from kivy.properties import ListProperty, ObjectProperty

Builder.load_file('liveactionbar.kv')

class LiveActionBar (GridLayout):

    def button_press_callback(self, button):
        if button == self.ids.capture_image_button:
            button.source = 'images/multiview/capturedown.png'
            if self.parent:
                self.parent.capture_image()
        elif button == self.ids.centering_actionbar_icon:
            button.source = 'images/multiview/centering_down.png'
        elif button == self.ids.download_icon:
            button.source = 'images/multiview/download_down.png'
        #manager = App.get_running_app().manager
    
    def button_release_callback(self, button):
        if button == self.ids.capture_image_button:
            button.source = 'images/multiview/capturenormal.png'
        elif button == self.ids.centering_actionbar_icon:
            button.source = 'images/multiview/centering_normal.png'
            if self.parent:
                self.parent.start_move(dir = 'C')
        elif button == self.ids.download_icon:
            button.source = 'images/multiview/download_normal.png'
            # button.source = 'images/centering_normal.png'
            if self.parent:
                self.parent.start_stop_cam()
                self.parent.get_rec_info()

    def button_touch_action(self, *args):
        if args[0].collide_point(*args[1].pos):
            print ('touch')
    
    def toggle_press_callback(self, button):

        if button == self.ids.light_icon_button:
            if button.state == 'down':
                button.source = 'images/multiview/light_down.png'
                if self.parent:
                    self.parent.light(on=True)
                    print ('light on')
            else:
                button.source = 'images/multiview/light_normal.png'
                if self.parent:
                    self.parent.light(on=False)
                    print ('light off')

        elif button == self.ids.speaker_icon_button:
            if button.state == 'down':
                button.source = 'images/multiview/speaker_down.png'
                if self.parent:
                    self.parent.start_audio_in()
            else:
                button.source = 'images/multiview/speaker_normal.png'
                if self.parent:
                    self.parent.stop_audio_in()
            
        elif button == self.ids.mic_icon_button:
            if button.state == 'down':
                button.source = 'images/multiview/mic_down.png'
                if self.parent:
                    self.parent.start_audio_out()
            else:
                button.source = 'images/multiview/mic_normal.png'
                if self.parent:
                    self.parent.stop_audio_out()

    def reduce_action_control(self):
        # Disable some controls (audio and download)
        self.ids.download_icon.disabled = True
        self.ids.speaker_icon_button.disabled = True
        self.ids.mic_icon_button.disabled = True
    
    def restore_action_control(self):
        # Re-enable some controls (audio and download)
        self.ids.download_icon.disabled = False
        self.ids.speaker_icon_button.disabled = False
        self.ids.mic_icon_button.disabled = False

    def reset(self):
        self.ids.light_icon_button.state = 'normal'
        self.ids.speaker_icon_button.state = 'normal'
        self.ids.mic_icon_button.state = 'normal'