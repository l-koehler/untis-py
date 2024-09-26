import sys, os, api, re, concurrent.futures
import datetime as dt
from dateutil.relativedelta import relativedelta, FR, MO

use_qt5 = True
if not "--qt5" in sys.argv:
    use_qt5 = False
    try:
        from PyQt6.QtCore import Qt, QDate, QSettings, pyqtSignal, QThread, QObject
        from PyQt6 import QtCore, QtWidgets
        from PyQt6.QtGui import QShortcut, QKeySequence, QIcon, QBrush, QColor
        from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QHBoxLayout, QWidget, QPushButton, QDialog, QFrame, QAbstractItemView, QMessageBox, QTableWidgetItem
    except ImportError:
        use_qt5 = True
if use_qt5:
    from PyQt5.QtCore import Qt, QDate, QSettings, pyqtSignal, QThread, QObject
    from PyQt5 import QtCore, QtWidgets
    from PyQt5.QtGui import QIcon, QBrush, QColor, QKeySequence
    from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QHBoxLayout, QWidget, QPushButton, QDialog, QFrame, QAbstractItemView, QMessageBox, QTableWidgetItem, QShortcut

class QFrame_click(QFrame):
    clicked = pyqtSignal()
    def mousePressEvent(self, ev):
        self.clicked.emit()

def size_policy():
    if use_qt5:
        return QtWidgets.QSizePolicy
    else:
        return QtWidgets.QSizePolicy.Policy

class ReloadData(QObject):
    redraw_requested = pyqtSignal()

    def run(self, parent, monday, friday):
        parent.data = api.get_table([], parent.session, monday, friday, True)[1]
        self.redraw_requested.emit()


class LoginPopup(QDialog):
    def save(self):
        # fix some common mistakes with the server address
        # remove http(s) prefix and (trailing) slashes
        server_text = re.sub(r'https?://', '', self.server_le.text()).replace('/', '')
                
        self.settings.setValue('server', self.server_le.text())
        self.settings.setValue('school', self.school_le.text())
        self.settings.setValue('user', self.user_le.text())
        self.settings.setValue('password', self.password_le.text())
    def __init__(self, settings):
        QWidget.__init__(self)
        self.setWindowTitle("Dialog")
        self.resize(172, 244)
        self.dialog_btnb = QtWidgets.QDialogButtonBox(self)
        self.dialog_btnb.setGeometry(QtCore.QRect(0, 210, 161, 32))

        self.server_le = QtWidgets.QLineEdit(self)
        self.server_le.setGeometry(QtCore.QRect(10, 30, 151, 22))
        self.server_lbl = QtWidgets.QLabel(self)
        self.server_lbl.setGeometry(QtCore.QRect(10, 10, 151, 17))
        self.server_lbl.setText("Server:")
        self.school_lbl = QtWidgets.QLabel(self)
        self.school_lbl.setGeometry(QtCore.QRect(10, 60, 151, 17))
        self.school_lbl.setText("School:")
        self.school_le = QtWidgets.QLineEdit(self)
        self.school_le.setGeometry(QtCore.QRect(10, 80, 151, 22))
        self.user_lbl = QtWidgets.QLabel(self)
        self.user_lbl.setGeometry(QtCore.QRect(10, 110, 151, 17))
        self.user_lbl.setText("Username:")
        self.user_le = QtWidgets.QLineEdit(self)
        self.user_le.setGeometry(QtCore.QRect(10, 130, 151, 22))
        self.password_lbl = QtWidgets.QLabel(self)
        self.password_lbl.setGeometry(QtCore.QRect(10, 160, 151, 17))
        self.password_lbl.setText("Password:")
        self.password_le = QtWidgets.QLineEdit(self)
        self.password_le.setGeometry(QtCore.QRect(10, 180, 151, 22))
        
        if (use_qt5):
            self.dialog_btnb.setOrientation(QtCore.Qt.Horizontal)
            self.dialog_btnb.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
            self.password_le.setEchoMode(QtWidgets.QLineEdit.PasswordEchoOnEdit)
        else:
            self.dialog_btnb.setOrientation(QtCore.Qt.Orientation.Horizontal)
            self.dialog_btnb.setStandardButtons(QtWidgets.QDialogButtonBox.StandardButton.Cancel|QtWidgets.QDialogButtonBox.StandardButton.Ok)
            self.password_le.setEchoMode(QtWidgets.QLineEdit.EchoMode.PasswordEchoOnEdit)

        self.dialog_btnb.accepted.connect(self.accept) # type: ignore
        self.dialog_btnb.rejected.connect(self.reject) # type: ignore
        
        self.settings = settings
        self.server_le.setText(self.settings.value('server') or '')
        self.school_le.setText(self.settings.value('school') or '')
        self.user_le.setText(self.settings.value('user') or '')
        self.password_le.setText(self.settings.value('password') or '')
        self.dialog_btnb.accepted.connect(self.save)

class InfoPopup(QDialog):
    def __init__(self, parent):        
        QWidget.__init__(self)
        self.setWindowTitle("Lesson Info")
        self.resize(249, 283)
        self.close_btn = QtWidgets.QPushButton(self)
        self.close_btn.setGeometry(QtCore.QRect(10, 250, 231, 25))
        self.close_btn.setText("Close")
        self.close_btn.pressed.connect(self.close)
        if (parent.session == None or parent.force_cache):
            self.warning = QLabel(self)
            self.warning.setText("<h2>Unavailable!</h2><p>Lesson Details are not available<br>in cache-only mode.</p><p>To disable cache-only mode,<br>restart the program.</p>")
            self.warning.setWordWrap(True)
            return
        if (parent.week_is_cached):
            parent.fetch_week(True)
            
        self.lesson_tab = QtWidgets.QTabWidget(self)
        self.lesson_tab.setGeometry(QtCore.QRect(10, 10, 231, 231))
        self.lesson_tab.setCurrentIndex(1)
        
        col = parent.timetable.currentColumn()
        row = parent.timetable.currentRow()
        parent.timetable.selectionModel().clear()
        self.close_btn.pressed.connect(self.close)
        # richtext info about the lesson
        try:
            hour_data = parent.data[row][col]
        except:
            hour_data = [None]
            
        
        for i in range(len(hour_data)):
            if hour_data == [None]:
                self.content = QLabel(self)
                self.content.setText("<h2>No Lesson planned!</h2>")
                self.content.setWordWrap(True)
                continue
                
            lesson = hour_data[i]
            full_repl = lesson[-1]

            try:
                room_str = f"{full_repl.rooms[0].name}"
                if full_repl.original_rooms != full_repl.rooms and full_repl.original_rooms != []:
                    room_str += f" (originally in {full_repl.original_rooms[0].name})"
            except IndexError:
                room_str = "Unknown"

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
    def setupUi(self, MainWindow):
        MainWindow.setWindowTitle("Untis")
        MainWindow.resize(1116, 674)
        sizePolicy = QtWidgets.QSizePolicy(size_policy().Expanding, size_policy().Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        sizePolicy = QtWidgets.QSizePolicy(size_policy().Expanding, size_policy().Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)
        self.centralwidget.setAutoFillBackground(True)
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        spacerItem = QtWidgets.QSpacerItem(20, 5, size_policy().Minimum, size_policy().Fixed)
        self.verticalLayout.addItem(spacerItem)
        self.top_bar_qhb = QtWidgets.QHBoxLayout()
        spacerItem1 = QtWidgets.QSpacerItem(10, 20, size_policy().Fixed, size_policy().Minimum)
        self.top_bar_qhb.addItem(spacerItem1)
        self.prev_btn = QtWidgets.QToolButton(self.centralwidget)
        self.prev_btn.setText("")
        self.top_bar_qhb.addWidget(self.prev_btn)
        spacerItem2 = QtWidgets.QSpacerItem(100, 20, size_policy().Maximum, size_policy().Minimum)
        self.top_bar_qhb.addItem(spacerItem2)
        self.login_btn = QtWidgets.QPushButton(self.centralwidget)
        self.login_btn.setText("Login")
        self.top_bar_qhb.addWidget(self.login_btn)
        spacerItem3 = QtWidgets.QSpacerItem(100, 20, size_policy().Maximum, size_policy().Minimum)
        self.top_bar_qhb.addItem(spacerItem3)
        self.reload_btn = QtWidgets.QPushButton(self.centralwidget)
        self.reload_btn.setText("Reload")
        self.top_bar_qhb.addWidget(self.reload_btn)
        spacerItem4 = QtWidgets.QSpacerItem(100, 20, size_policy().Maximum, size_policy().Minimum)
        self.top_bar_qhb.addItem(spacerItem4)
        self.date_edit = QtWidgets.QDateEdit(self.centralwidget)
        self.date_edit.setDateTime(QtCore.QDateTime(QtCore.QDate(2024, 2, 16), QtCore.QTime(0, 0, 0)))
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setCurrentSectionIndex(2)
        self.top_bar_qhb.addWidget(self.date_edit)
        spacerItem5 = QtWidgets.QSpacerItem(100, 20, size_policy().Maximum, size_policy().Minimum)
        self.top_bar_qhb.addItem(spacerItem5)
        self.next_btn = QtWidgets.QToolButton(self.centralwidget)

        self.top_bar_qhb.addWidget(self.next_btn)
        spacerItem6 = QtWidgets.QSpacerItem(10, 20, size_policy().Fixed, size_policy().Minimum)
        self.top_bar_qhb.addItem(spacerItem6)
        self.verticalLayout.addLayout(self.top_bar_qhb)
        self.timetable = QtWidgets.QTableWidget(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(size_policy().Expanding, size_policy().Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.timetable.sizePolicy().hasHeightForWidth())
        self.timetable.setSizePolicy(sizePolicy)
        self.timetable.setAutoFillBackground(True)
        self.timetable.setAlternatingRowColors(True)
        self.timetable.setShowGrid(False)
        self.timetable.setRowCount(8)
        self.timetable.setColumnCount(5)
        self.timetable.horizontalHeader().setCascadingSectionResizes(False)
        self.timetable.horizontalHeader().setDefaultSectionSize(220)
        self.timetable.horizontalHeader().setMinimumSectionSize(210)
        self.timetable.verticalHeader().setVisible(False)
        self.timetable.verticalHeader().setDefaultSectionSize(70)
        self.timetable.verticalHeader().setMinimumSectionSize(70)
        self.verticalLayout.addWidget(self.timetable)
        if use_qt5:
            self.next_btn.setArrowType(QtCore.Qt.RightArrow)
            self.prev_btn.setArrowType(QtCore.Qt.LeftArrow)
            self.date_edit.setContextMenuPolicy(QtCore.Qt.DefaultContextMenu)
            self.timetable.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
            self.timetable.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        else:
            self.next_btn.setArrowType(QtCore.Qt.ArrowType.RightArrow)
            self.prev_btn.setArrowType(QtCore.Qt.ArrowType.LeftArrow)
            self.date_edit.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.DefaultContextMenu)
            self.timetable.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollMode.ScrollPerPixel)
            self.timetable.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollMode.ScrollPerPixel)
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        MainWindow.setStatusBar(self.statusbar)
        self.prev_btn.setShortcut("Left")
        self.reload_btn.setShortcut("Up, Ctrl+R")
        self.next_btn.setShortcut("Right")
        
    current_date = QDate.currentDate()
    def date_changed(self):
        new_date = self.date_edit.date()
        if self.current_date.weekNumber() != new_date.weekNumber():
            self.fetch_week()
        self.current_date = new_date

    def load_settings(self, no_set_credentials):
        if not no_set_credentials:
            self.server   = self.settings.value('server')
            self.school   = self.settings.value('school')
            self.user     = self.settings.value('user')
            self.password = self.settings.value('password')
        if not "--no-cache" in sys.argv:
            self.cached_timetable = self.settings.value('cached_timetable') or []
        else:
            self.cached_timetable = []

    def delete_settings(self):
        self.settings.clear()

    def login_popup(self):
        popup = LoginPopup(self.settings)
        popup.exec()
        self.load_settings(False)
        # try to start a new session
        credentials = [self.server, self.school, self.user, self.password]
        if None not in credentials and '' not in credentials:
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

    def info_popup(self):
        if self.is_interactive:
            popup = InfoPopup(self)
            popup.exec()
    
    def draw_week(self):
        selected_day = self.date_edit.date().toPyDate()
        week_number = selected_day.isocalendar()[1]
        monday = dt.date.fromisocalendar(selected_day.year, week_number, 1)
        
        self.is_interactive = False

        self.timetable.setRowCount(len(self.data))

        for row in range(len(self.data)):
            for col in range(len(self.data[row])):
                widget = QFrame_click()
                try:
                    entry_data = self.data[row][col]
                    # add the on-click function for lesson info. dont change the lambda it barely works as-is
                    if (len(entry_data) != 0):
                        fn = lambda row=row, col=col: f"{self.timetable.setCurrentCell(row, col)}\n{self.info_popup()}"
                        widget.clicked.connect(fn)
                except IndexError:
                    entry_data = []
                layout = QHBoxLayout()
                layout.setContentsMargins(0, 0, 0, 0);
                
                if (col != 0):
                    line = QFrame()
                    line.setFrameShape(QFrame.Shape.VLine)
                    line.setStyleSheet("background-color:white;")
                    line.setMaximumWidth(1)
                    layout.addWidget(line)
                else:
                    layout.addSpacing(6)

                entry_data.sort()
                for i in range(len(entry_data)):
                    lesson = entry_data[i]
                    lesson_widget = QLabel()
                    lesson_widget.setTextFormat(Qt.TextFormat.RichText)
                    richtext = f"<b>{lesson[0]}</b><br>{lesson[1]}"
                    stylesheet = f"padding-right:4px; padding-left:4px; margin-top: 4px; margin-bottom:4px; border-radius:4px;"
                    if lesson[3] != "white":
                         stylesheet+=f"background-color:{lesson[3]};"
                    if lesson[2] != '':
                        richtext += f"<br><small>{lesson[2]}</small>"
                    lesson_widget.setStyleSheet(stylesheet)
                    lesson_widget.setText(richtext)
                    layout.addWidget(lesson_widget)
                    if len(entry_data) != 1 and i+1 != len(entry_data):
                        # add separator
                        line = QFrame()
                        line.setFrameShape(QFrame.Shape.VLine)
                        line.setStyleSheet("background-color:gray;margin-top:7px;margin-bottom:7px;border-radius:5px")
                        layout.addWidget(line)
                
                if (len(entry_data) == 0):
                   layout.addWidget(QWidget())
                
                
                if (col != len(self.data[row])-1):
                    line = QFrame()
                    line.setFrameShape(QFrame.Shape.VLine)
                    line.setStyleSheet("background-color:white;")
                    line.setMaximumWidth(1)
                    layout.addWidget(line)
                else:
                    layout.addSpacing(6)
                
                widget.setLayout(layout)
                
                self.timetable.setCellWidget(row, col, widget)
                
        # highlight the current day, if it is within the week
        current_date = QDate.currentDate()
        default_brush = QTableWidgetItem().background()
        weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        for i in range(len(weekdays)):
            weekday = weekdays[i]
            if (monday == current_date.addDays((i)*-1)):
                brush = QBrush(QColor(0x30, 0xA5, 0x30))
                self.timetable.horizontalHeaderItem(i).setBackground(brush)
            else:
                self.timetable.horizontalHeaderItem(i).setBackground(default_brush)
        self.is_interactive = True


    def fetch_week(self, replace_cache=False):
        selected_day = self.date_edit.date().toPyDate()
        week_number = selected_day.isocalendar()[1]
        monday = dt.date.fromisocalendar(selected_day.year, week_number, 1)
        friday = dt.date.fromisocalendar(selected_day.year, week_number, 5)

        if "--fake-data" not in sys.argv:
            if (self.force_cache):
                self.data = api.get_cached(self.cached_timetable, monday)
            else:
                self.data = api.get_table(self.cached_timetable, self.session, monday, friday, replace_cache)
            self.week_is_cached = self.data[0]
            self.data = self.data[1]
        else:
            self.data = [[[['mo 1', 'regular lesson', '', 'white', None]], [['tu 1', 'regular lesson', '', 'white', None]]], [[['mo 2', 'single, red', '', 'red', None]], [['tu 2', 'single, orange', '', 'orange', None]]], [[['mo 3', 'half, white', '', 'white', None], ['mo 3', 'second half', '', 'white', None]], [['hello', 'half, red', '', 'red', None], ['world', 'other half', '', 'white', None]]]]
        if self.data != [] and self.data[0] == "err":
            QMessageBox.critical(
                self,
                self.data[1],
                self.data[2]
            )
            return
        
        if replace_cache:
            return
        
        self.draw_week()
        
        # if our results were from cache, asynchronously refresh that
        if (self.week_is_cached and self.force_cache == False):
            self.refresh_week(monday, friday)
            self.week_is_cached = False
    
    def refresh_week(self, monday, friday):
        self.thread = QThread()
        self.worker = ReloadData()
        self.worker.moveToThread(self.thread)
        
        self.worker.redraw_requested.connect(self.thread.quit)
        self.worker.redraw_requested.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.redraw_requested.connect(self.draw_week)
        
        self.thread.start()
        self.worker.run(self, monday, friday)
        
    
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
        self.is_interactive = True

    def __init__(self):
        super().__init__()
        
        self.executor = concurrent.futures.ThreadPoolExecutor()

        self.settings = QSettings('l-koehler', 'untis-py')
        self.is_interactive = False
        self.load_settings('--credentials' in sys.argv) # don't overwrite credentials true/false
        
        if "--delete-settings" in sys.argv:
            self.delete_settings()
        if getattr(sys, 'frozen', False):
            ico_path = os.path.join(sys._MEIPASS, "icon.ico")
        else:
            ico_path = "./icon.ico"
        self.setupUi(self)
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
        self.date_edit.setDate(QDate.currentDate())
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
        self.force_cache = False
        self.week_is_cached = False
        self.show()
        # if the credentials are already all set, log in automatically
        self.data = None
        credentials = [self.server, self.school, self.user, self.password]
        if None not in credentials and '' not in credentials and '--fake-data' not in sys.argv and '--force-cache' not in sys.argv:
            self.session = api.login(credentials)
            if type(self.session) != list: # if login successful
                self.fetch_week()
            else:
                box = QMessageBox (
                    QMessageBox.Icon.Critical,
                    self.session[0],
                    f"<h3>Login Failed!</h3><b>Details:</b><br>{self.session[1]}<h4>Use cached data only?</h4>",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                self.force_cache = (box.exec() == QMessageBox.StandardButton.Yes)
                self.session = None
        elif '--fake-data' in sys.argv:
            self.fetch_week()
        elif '--force-cache' in sys.argv:
            self.force_cache = True
            self.session = None
        else:
            self.session = None
        
        if self.force_cache:
            cache_warning = QLabel("<span style='color:#F44;'>Cache-only mode active, restart to disable!</span>")
            self.verticalLayout.addWidget(cache_warning)
            # resize to just-enough-to-fit unless it is already big enough
            self.resize(self.width(), max(self.height(), 698))
            self.hide(); self.show()
            self.fetch_week()

    def closeEvent(self, event):
        # save the new cache before closing
        if not "--no-cache" in sys.argv:
            self.settings.setValue('cached_timetable', self.cached_timetable)
        event.accept()
