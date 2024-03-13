from PyQt6.QtCore import QSize, Qt, QDate, QSettings
from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QDialog
import sys, api
import datetime as dt
from dateutil.relativedelta import relativedelta, FR, MO

class LoginPopup(QDialog):
    def save(self):
        self.settings.setValue('server', self.server_le.text())
        self.settings.setValue('school', self.school_le.text())
        self.settings.setValue('user', self.user_le.text())
        self.settings.setValue('password', self.password_le.text())
    def __init__(self, settings):
        QWidget.__init__(self)
        uic.loadUi('login.ui', self)
        self.settings = settings
        self.server_le.setText(self.settings.value('server') or '')
        self.school_le.setText(self.settings.value('school') or '')
        self.user_le.setText(self.settings.value('user') or '')
        self.password_le.setText(self.settings.value('password') or '')
        self.dialog_btnb.accepted.connect(self.save)

class MainWindow(QMainWindow):
    current_date = QDate.currentDate()
    def date_changed(self):
        new_date = self.date_edit.date()
        if self.current_date.weekNumber() != new_date.weekNumber():
            self.fetch_week()
        self.current_date = new_date

    def load_settings(self):
        self.server   = self.settings.value('server')
        self.school   = self.settings.value('school')
        self.user     = self.settings.value('user')
        self.password = self.settings.value('password')

    def login_popup(self):
        popup = LoginPopup(self.settings)
        popup.exec()

    def update_cached_class(self):
        if self.classes_cb.currentIndex() != 0:
            self.settings.setValue('class_choice', self.classes_cb.currentIndex())

    def load_cached_class(self):
        self.classes_cb.setCurrentIndex(self.settings.value('class_choice', type=int))

    def fetch_week(self):
        selected_day = self.date_edit.date().toPyDate()
        week_number = selected_day.isocalendar()[1]
        monday = dt.date.fromisocalendar(selected_day.year, week_number, 1)
        friday = dt.date.fromisocalendar(selected_day.year, week_number, 5)
        data = api.get_table(self, monday, friday, api.class_by_name(self, self.classes_cb.currentText()))
        self.timetable.setRowCount(len(data))
        self.timetable.setColumnCount(len(data[0]))
        for row in range(len(data)):
            for col in range(len(data[row])):
                entry_data = data[row][col]
                widget = QWidget()
                layout = QHBoxLayout()
                entry_data.sort()
                for lesson in entry_data:
                    layout.addWidget(QLabel(lesson[0]))
                widget.setLayout(layout)
                self.timetable.setCellWidget(row, col, widget)

    def __init__(self):
        super().__init__()
        uic.loadUi("mainwindow.ui", self)
        self.settings = QSettings('l-koehler', 'untis-py')
        self.load_settings()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.dateChanged.connect(self.date_changed)
        self.login_btn.pressed.connect(self.login_popup)
        self.classes_cb.currentIndexChanged.connect(self.update_cached_class)
        self.show()
        # if the credentials are already all set, log in automatically
        credentials = [self.server, self.school, self.user, self.password]
        if None not in credentials and '' not in credentials:
            self.session = api.login(self, credentials)
            if self.session != None: # if login successful
                self.classes_cb.addItems([i.name for i in self.session.klassen()])
                self.load_cached_class()
                table = self.fetch_week()
        else:
            self.session = None

app = QApplication(sys.argv)

window = MainWindow()

app.exec()
