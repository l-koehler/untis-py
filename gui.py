import sys, os, api
import datetime as dt
from dateutil.relativedelta import relativedelta, FR, MO

use_qt5 = True
if not "--qt5" in sys.argv:
    use_qt5 = False
    try:
        from PyQt6.QtCore import Qt, QDate, QSettings
        from PyQt6 import uic
        from PyQt6.QtGui import QShortcut, QKeySequence, QIcon
        from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QHBoxLayout, QWidget, QPushButton, QDialog, QFrame, QAbstractItemView, QMessageBox
    except ImportError:
        use_qt5 = True
if use_qt5:
    from PyQt5.QtCore import Qt, QDate, QSettings
    from PyQt5 import uic
    from PyQt5.QtGui import QIcon
    from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QHBoxLayout, QWidget, QPushButton, QDialog, QFrame, QAbstractItemView, QMessageBox

class LoginPopup(QDialog):
    def save(self):
        self.settings.setValue('server', self.server_le.text())
        self.settings.setValue('school', self.school_le.text())
        self.settings.setValue('user', self.user_le.text())
        self.settings.setValue('password', self.password_le.text())
    def __init__(self, settings):
        QWidget.__init__(self)
        if getattr(sys, 'frozen', False):
            path = os.path.join(sys._MEIPASS, "login.ui")
        else:
            path = "./login.ui"
        uic.loadUi(path, self)
        self.settings = settings
        self.server_le.setText(self.settings.value('server') or '')
        self.school_le.setText(self.settings.value('school') or '')
        self.user_le.setText(self.settings.value('user') or '')
        self.password_le.setText(self.settings.value('password') or '')
        self.dialog_btnb.accepted.connect(self.save)

class InfoPopup(QDialog):
    def __init__(self, parent):
        QWidget.__init__(self)
        if getattr(sys, 'frozen', False):
            path = os.path.join(sys._MEIPASS, "lesson_info.ui")
        else:
            path = "./lesson_info.ui"
        uic.loadUi(path, self)
        col = parent.timetable.currentColumn()
        row = parent.timetable.currentRow()
        parent.timetable.selectionModel().clear()
        # richtext info about the lesson
        hour_data = parent.data[row][col]
        for i in range(len(hour_data)):
            lesson = hour_data[i]
            full_repl = lesson[-1]
            if full_repl == None:
                self.lesson_tab.addTab(QLabel(f"<h4>Example Entry</h4>\n{lesson[1]}"), lesson[0])
                continue

            room_str = f"{full_repl.rooms[0].name}"
            if full_repl.original_rooms != full_repl.rooms and full_repl.original_rooms != []:
                room_str += f" (originally in {full_repl.original_rooms[0].name})"

            if full_repl.activityType != "Unterricht": # why is it localized qwq
                status_str = full_repl.activityType
            elif full_repl.code == "cancelled":
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

            long_name = full_repl.subjects[0].long_name
            rt_info = f"<h4>{long_name}</h4>\
            <br>Start: {full_repl.start.time().strftime('%H:%M')}\
            <br>End: {full_repl.end.time().strftime('%H:%M')}\
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

    def delete_settings(self):
        self.settings.clear()

    def login_popup(self):
        popup = LoginPopup(self.settings)
        popup.exec()
        self.load_settings()
        # try to start a new session
        credentials = [self.server, self.school, self.user, self.password]
        if None not in credentials and '' not in credentials:
            self.session = api.login(self, credentials)
            if type(self.session) != list: # if login successful
                self.fetch_week()
            else:
                QMessageBox.critical(
                    self,
                    self.session[0],
                    self.session[1]
                )
                self.session = None

    def info_popup(self):
        popup = InfoPopup(self)
        popup.exec()

    def fetch_week(self):
        selected_day = self.date_edit.date().toPyDate()
        week_number = selected_day.isocalendar()[1]
        monday = dt.date.fromisocalendar(selected_day.year, week_number, 1)
        friday = dt.date.fromisocalendar(selected_day.year, week_number, 5)

        if "--fake-data" not in sys.argv:
            self.data = api.get_table(self.cached_timetable, self.session, monday, friday)
        else:
            self.data = [[[['mo 1', 'regular lesson', '', 'white', None]], [['tu 1', 'regular lesson', '', 'white', None]]], [[['mo 2', 'single, red', '', 'red', None]], [['tu 2', 'single, orange', '', 'orange', None]]], [[['mo 3', 'half, white', '', 'white', None], ['mo 3', 'second half', '', 'white', None]], [['hello', 'half, red', '', 'red', None], ['world', 'other half', '', 'white', None]]]]
        if self.data != [] and self.data[0] == "err":
            QMessageBox.critical(
                self,
                self.data[1],
                self.data[2]
            )
            return

        # add entry to cache, if not yet cached
        if not monday in [i[0] for i in self.cached_timetable]:
            self.cached_timetable.append([monday, self.data])

        self.timetable.setRowCount(len(self.data))

        for row in range(len(self.data)):
            for col in range(len(self.data[row])):
                try:
                    entry_data = self.data[row][col]
                except IndexError:
                    entry_data = []
                widget = QWidget()
                layout = QHBoxLayout()
                entry_data.sort()
                for i in range(len(entry_data)):
                    lesson = entry_data[i]
                    lesson_widget = QLabel()
                    lesson_widget.setTextFormat(Qt.TextFormat.RichText)
                    richtext = f"<b>{lesson[0]}</b><br>{lesson[1]}"
                    if lesson[2] != '':
                        richtext += f"<br><small>{lesson[2]}</small>"
                    if lesson[3] != 'white':
                        stylesheet = f"border-radius:4px; background-color:{lesson[3]}"
                        lesson_widget.setStyleSheet(stylesheet)
                    lesson_widget.setContentsMargins(2,0,0,0)
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
        self.cached_timetable = []
        # delete all rows and draw empty table to make the reload visible
        self.timetable.setRowCount(0)
        self.timetable.repaint()
        self.fetch_week()

    def __init__(self):
        super().__init__()
        if getattr(sys, 'frozen', False):
            ui_path = os.path.join(sys._MEIPASS, "mainwindow.ui")
            ico_path = os.path.join(sys._MEIPASS, "icon.ico")
        else:
            ui_path = "./mainwindow.ui"
            ico_path = "./icon.ico"
        uic.loadUi(ui_path, self)
        # workaround to set icon on windows
        # how did this mess of an OS ever succeed
        if sys.platform == "win32":
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('l-koehler.untis-py')
        # set application icon
        self.setWindowIcon(QIcon(ico_path))

        for index in range(len(sys.argv)):
            if sys.argv[index] == '--credentials':
                if len(sys.argv) < index+5:
                    print(f"--credentials takes 4 arguments, {len(sys.argv)-index-1} were passed!")
                    print("use --credentials <server> <school> <username> <password>")
                    exit(1)
                self.server   = sys.argv[index+1]
                self.school   = sys.argv[index+2]
                self.user     = sys.argv[index+3]
                self.password = sys.argv[index+4]
        if '--credentials' not in sys.argv:
            self.settings = QSettings('l-koehler', 'untis-py')
            self.load_settings()
            if "--delete-settings" in sys.argv:
                self.delete_settings()

        self.date_edit.setDate(QDate.currentDate())
        if not use_qt5:
            self.shortcut_current_week = QShortcut(QKeySequence('Down'), self)
            self.shortcut_current_week.activated.connect(self.current_week)
        self.timetable.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.date_edit.dateChanged.connect(self.date_changed)
        self.login_btn.pressed.connect(self.login_popup)
        self.timetable.cellClicked.connect(self.info_popup)
        self.prev_btn.pressed.connect(self.prev_week)
        self.next_btn.pressed.connect(self.next_week)
        self.reload_btn.pressed.connect(self.reload_all)
        self.timetable.setHorizontalHeaderLabels(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        self.show()
        # if the credentials are already all set, log in automatically
        self.data = None
        self.cached_timetable = [] # lists of (monday, data)
        credentials = [self.server, self.school, self.user, self.password]
        if None not in credentials and '' not in credentials and '--fake-data' not in sys.argv:
            self.session = api.login(credentials)
            if type(self.session) != list: # if login successful
                self.fetch_week()
            else:
                QMessageBox.critical(
                    self,
                    self.session[0],
                    self.session[1]
                )
                self.session = None
        elif '--fake-data' in sys.argv:
            self.fetch_week()
        else:
            self.session = None
