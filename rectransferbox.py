from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout

Builder.load_file('rectransferbox.kv')

class RecTransferBox(BoxLayout):
    pass

    def download_rec(self):
        self.parent.download_rec()