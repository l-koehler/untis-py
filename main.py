from PyQt6.QtCore import QSize, Qt, QDate, QSettings
from PyQt6 import uic
from PyQt6.QtGui import QTextFormat, QShortcut, QKeySequence
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QDialog, QFrame
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

class InfoPopup(QDialog):
    def __init__(self, parent):
        QWidget.__init__(self)
        uic.loadUi('lesson_info.ui', self)
        self.lesson_tab.clear()
        col = parent.timetable.currentColumn()
        row = parent.timetable.currentRow()
        # richtext info about the lesson
        hour_data = parent.data[row][col]
        for i in range(len(hour_data)):
            lesson = hour_data[i]
            full_repl = lesson[-1]

            room_str = f"{full_repl.rooms[0].name}"
            if full_repl.original_rooms != full_repl.rooms and full_repl.original_rooms != []:
                room_str += f" (originally in {full_repl.original_rooms[0].name})"

            if full_repl.code == "cancelled":
                status_str = "Cancelled"
            elif full_repl.code == "irregular":
                status_str = "Substitution"
            elif full_repl.type == "ls":
                status_str = "Regular"
            elif full_repl.type == "oh":
                status_str = "Office Hour"
            elif full_repl.type == "sb":
                status_str = "Standby"
            elif full_repl.type == "bs":
                status_str = "Break Supervision"
            elif full_repl.type == "ex":
                status_str = "Examination"
            else:
                status_str = "unknown/report error"

            if len(full_repl.klassen) == 1:
                klassen_str = full_repl.klassen[0]
            else:
                klassen_str = '; '.join([i.name for i in full_repl.klassen])

            rt_info = f"<h3>{lesson[0]}</h3>\
            <br>Start: {full_repl.start.time()}\
            <br>End: {full_repl.end.time()}\
            <br>Type: {status_str}\
            <br>Room: {room_str}\
            <br>Classes: {klassen_str}"
            if full_repl.info != "":
                rt_info += f"<br>Info: {full_repl.info}"

            title = f"{i+1}: {lesson[0]}"
            info_lbl = QLabel(f"{rt_info}")
            info_lbl.setWordWrap(True)
            self.lesson_tab.addTab(info_lbl, title)
        self.close_btn.pressed.connect(self.close)

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

    def info_popup(self):
        popup = InfoPopup(self)
        popup.exec()

    def update_cached_class(self):
        if self.classes_cb.currentIndex() != 0:
            self.settings.setValue('class_choice', self.classes_cb.currentIndex())
            # delete cache, it is only valid for one class
            self.cached_responses = []
            self.fetch_week()

    def load_cached_class(self):
        self.classes_cb.setCurrentIndex(self.settings.value('class_choice', type=int))

    def fetch_week(self):
        selected_day = self.date_edit.date().toPyDate()
        week_number = selected_day.isocalendar()[1]
        monday = dt.date.fromisocalendar(selected_day.year, week_number, 1)
        friday = dt.date.fromisocalendar(selected_day.year, week_number, 5)
        self.data = api.get_table(self, monday, friday, api.class_by_name(self, self.classes_cb.currentText()))
        if self.data == None:
            return # error was already displayed earlier

        # add entry to cache, if not yet cached
        if not monday in [i[0] for i in self.cached_responses]:
            self.cached_responses.append([monday, self.data])

        self.timetable.setRowCount(len(self.data))

        for row in range(len(self.data)):
            for col in range(len(self.data[row])):
                entry_data = self.data[row][col]
                widget = QWidget()
                layout = QHBoxLayout()
                entry_data.sort()
                for i in range(len(entry_data)):
                    lesson = entry_data[i]
                    lesson_widget = QLabel()
                    lesson_widget.setTextFormat(Qt.TextFormat.RichText)
                    richtext = f"<b>{lesson[0]}</b><br>{lesson[1]}"
                    if lesson[2] != '':
                        richtext += f"<br>{lesson[2]}"
                    if lesson[3] != 'white':
                        lesson_widget.setStyleSheet(f"background-color:{lesson[3]}")
                    lesson_widget.setText(richtext)
                    layout.addWidget(lesson_widget)
                    if len(entry_data) != 1 and i+1 != len(entry_data):
                        # add separator
                        line = QFrame()
                        line.setFrameShape(QFrame.Shape.VLine)
                        line.setStyleSheet("background-color:lightgray;color:lightgray")
                        layout.addWidget(line)
                widget.setLayout(layout)
                self.timetable.setCellWidget(row, col, widget)

    def prev_week(self):
        self.date_edit.setDate(self.date_edit.date().addDays(-7))

    def next_week(self):
        self.date_edit.setDate(self.date_edit.date().addDays(7))

    def current_week(self):
        self.date_edit.setDate(QDate.currentDate())

    def reload_all(self):
        self.cached_responses = []
        # delete all rows and draw empty table to make the reload visible
        self.timetable.setRowCount(0)
        self.timetable.repaint()
        self.fetch_week()

    def __init__(self):
        super().__init__()
        uic.loadUi("mainwindow.ui", self)
        self.settings = QSettings('l-koehler', 'untis-py')
        self.load_settings()
        self.date_edit.setDate(QDate.currentDate())
        self.shortcut_current_week = QShortcut(QKeySequence('Down'), self)
        self.date_edit.dateChanged.connect(self.date_changed)
        self.login_btn.pressed.connect(self.login_popup)
        self.classes_cb.currentIndexChanged.connect(self.update_cached_class)
        self.timetable.cellClicked.connect(self.info_popup)
        self.prev_btn.pressed.connect(self.prev_week)
        self.next_btn.pressed.connect(self.next_week)
        self.reload_btn.pressed.connect(self.reload_all)
        self.shortcut_current_week.activated.connect(self.current_week)
        self.timetable.setHorizontalHeaderLabels(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        self.show()
        # if the credentials are already all set, log in automatically
        self.data = None
        self.cached_responses = [] # lists of (monday, data)
        credentials = [self.server, self.school, self.user, self.password]
        if None not in credentials and '' not in credentials:
            self.session = api.login(self, credentials)
            if self.session != None: # if login successful
                self.classes_cb.addItems([i.name for i in self.session.klassen()])
                self.load_cached_class() # triggers update_cached_class triggers fetch_week
        else:
            self.session = None

app = QApplication(sys.argv)

window = MainWindow()

app.exec()
