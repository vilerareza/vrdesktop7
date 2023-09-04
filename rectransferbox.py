from datetime import date, datetime
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.picker import MDDatePicker, MDTimePicker
from kivy.properties import ObjectProperty, StringProperty

Builder.load_file('rectransferbox.kv')


class RecTransferBox(BoxLayout):
    
    btnDownload = ObjectProperty(None)
    btnDate = ObjectProperty(None)
    btnTime = ObjectProperty(None)
    btnCancel = ObjectProperty(None)
    lblStatus = ObjectProperty(None)
    strDate = StringProperty('')
    strTime = StringProperty('')
    strStatus = StringProperty('')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        datetime_ = datetime.now()
        self.date_ = datetime_.date()
        self.time_ = datetime_.time()
        self.strDate = self.date_.strftime('%d-%m-%y')
        self.strTime = self.time_.strftime('%H:%M')

    def download_rec(self):
        self.parent.download_rec(self.date_, self.time_)

    def close_me(self):
        self.parent.close_rec_dialog()

    def show_date_time_picker(self, sender):

        def is_selection_exist():
            # Check if rec file for selected date and time exist
            return self.parent.is_rec_exist(self.date_.year, self.date_.month, self.date_.day, self.time_.hour)
           
        def select_date_time(instance, value, *args):

            if sender == self.btnDate:
                self.date_=value
                # Updating the button text to selected date
                sender.text=value.strftime('%d-%m-%y') 
            elif sender == self.btnTime:
                self.time_=value
                # Updating the button text to selected date
                sender.text=value.strftime('%H:%M') 
            
            # Validate the existence of rec file
            if is_selection_exist():
                # Enable the download button
                self.btnDownload.disabled=False
            else:
                # Disable the download button
                self.btnDownload.disabled=True

        if (sender == self.btnDate):
            # Show date selection dialog

            try:
                date_dialog = MDDatePicker(
                    min_date = date(self.parent.rec_val_dates['year_min'], self.parent.rec_val_dates['month_min'], self.parent.rec_val_dates['date_min']),
                    max_date = date(self.parent.rec_val_dates['year_max'], self.parent.rec_val_dates['month_max'], self.parent.rec_val_dates['date_max'])
                )
            except:
                date_dialog = MDDatePicker()

            date_dialog.bind(on_save = select_date_time)
            date_dialog.open()

        elif (sender == self.btnTime):
            # Show time selection dialog
            time_now = datetime.now().time()
            time_dialog = MDTimePicker()
            time_dialog.am_pm = time_now.strftime('%p').lower()
            time_dialog.set_time(time_now)
            time_dialog.bind(on_save = select_date_time)
            time_dialog.open()

    def button_release_callback(self, button):

        if button == self.btnDownload:
            self.download_rec()
        elif button == self.btnCancel:
            self.close_me()
        else:
            # Show date and time picker
            self.show_date_time_picker(sender=button)