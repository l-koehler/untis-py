import sys, os, api, re, threading
import datetime as dt
from dateutil.relativedelta import relativedelta, FR, MO

use_qt5 = None
try:
    if "--force-qt5" in sys.argv:
        # skip trying to import qt6
        raise(ImportError)
    from PyQt6.QtCore import Qt, QDate, QSettings, pyqtSignal, QTimer
    from PyQt6 import QtCore
    from PyQt6.QtGui import QShortcut, QKeySequence, QIcon, QBrush, QColor
    from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QHBoxLayout, QVBoxLayout, QWidget, QPushButton, QDialog, QFrame, QAbstractItemView, QMessageBox, QTableWidgetItem, QSizePolicy, QSpacerItem, QToolButton, QDateEdit, QTableWidget, QStatusBar, QTabWidget, QComboBox
    use_qt5 = False
except ImportError:
    if not "--force-qt6" in sys.argv:
        from PyQt5.QtCore import Qt, QDate, QSettings, pyqtSignal, QTimer
        from PyQt5 import QtCore
        from PyQt5.QtGui import QIcon, QBrush, QColor, QKeySequence
        from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QHBoxLayout, QVBoxLayout, QWidget, QPushButton, QDialog, QFrame, QAbstractItemView, QMessageBox, QTableWidgetItem, QShortcut, QSizePolicy, QSpacerItem, QToolButton, QDateEdit, QTableWidget, QStatusBar,  QTabWidget, QComboBox
        use_qt5 = True
    else:
        print("Could not import PyQt5 or PyQt6. At least one of these is needed.")
        sys.exit(0)

class QFrame_click(QFrame):
    clicked = pyqtSignal()
    def mousePressEvent(self, ev):
        self.clicked.emit()

class QLabel_click(QLabel):
    clicked = pyqtSignal()
    def mousePressEvent(self, ev):
        self.clicked.emit()

def size_policy():
    if use_qt5:
        return QSizePolicy
    else:
        return QSizePolicy.Policy

class LoginPopup(QDialog):
    def save(self):                
        self.settings.setValue('server', self.server)
        self.settings.setValue('school', self.school)
        self.settings.setValue('user', self.user_le.text())
        self.settings.setValue('password', self.password_le.text())
        self.close()
    
    def cb_change(self):
        if self.old_text == self.school_le.text():
            return
        self.old_text = self.school_le.text()
        
        results = api.school_search(self.school_le.text())
        entries = [i[0] for i in results]
        self.school_cb.clear()

        if len(results) == 2 and results[1] == "ERR":
            self.school_cb.addItem(results[0])
            self.err_backed = True
        elif len(results) == 0:
            self.school_cb.addItem("No Results")
            self.err_backed = True
        else:
            self.school_cb.addItems(entries)
            self.err_backed = False
            
    def cb_sel(self):
        if self.err_backed:
            return
        data = api.school_search(self.school_cb.currentText())
        if len(data) == 0 or (len(data) == 2 and data[1] == "ERR"):
            return
        self.server = api.school_search(self.school_cb.currentText())[0][1]
        self.school = self.school_cb.currentText()
        
    def __init__(self, settings):
        QWidget.__init__(self)
        self.old_text = ""
        self.err_backed = True
        self.search_timer = QTimer()
        self.search_timer.timeout.connect(self.cb_change)
        self.search_timer.start(1000) # only search once a second at most
        self.vlayout = QVBoxLayout(self)
        
        self.setWindowTitle("Edit Credentials")
        self.resize(172, 244)

        self.school_lbl = QLabel()
        self.vlayout.addWidget(self.school_lbl)
        self.school_lbl.setText("School:")
        
        self.school_le = QLineEdit()
        self.vlayout.addWidget(self.school_le)

        self.school_cb = QComboBox()
        self.vlayout.addWidget(self.school_cb)
        self.school_cb.currentIndexChanged.connect(self.cb_sel)
        
        self.user_lbl = QLabel()
        self.vlayout.addWidget(self.user_lbl)
        self.user_lbl.setText("Username:")
        self.user_le = QLineEdit()
        self.vlayout.addWidget(self.user_le)

        self.password_lbl = QLabel()
        self.vlayout.addWidget(self.password_lbl)

        self.password_lbl.setText("Password:")
        self.password_le = QLineEdit()
        self.vlayout.addWidget(self.password_le)
        
        self.btn_layout = QHBoxLayout()
        self.vlayout.addLayout(self.btn_layout)

        self.btn_ok = QPushButton()
        self.btn_ok.setText("Save")
        self.btn_layout.addWidget(self.btn_ok)
        self.btn_cc = QPushButton()
        self.btn_cc.setText("Cancel")
        self.btn_layout.addWidget(self.btn_cc)
        
        self.btn_ok.pressed.connect(self.save) # type: ignore
        self.btn_cc.pressed.connect(self.close) # type: ignore
        
        self.settings = settings
        
        self.server = self.settings.value('server') or ''
        
        self.school_le.setText(self.settings.value('school') or '')
        self.school = self.settings.value('school') or ''
        self.user_le.setText(self.settings.value('user') or '')
        self.password_le.setText(self.settings.value('password') or '')

class InfoPopup(QDialog):
    def __init__(self, parent, index):        
        QWidget.__init__(self)
        self.setWindowTitle("Lesson Info")
        self.vlayout = QVBoxLayout(self)
        self.close_btn = QPushButton()
        self.close_btn.setText("Close")
        self.close_btn.pressed.connect(self.close)
        self.lesson_tab = QTabWidget()
        self.vlayout.addWidget(self.lesson_tab)
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

            rt_info = f"<h4>{full_repl.long_name}</h4>"
            rt_info += f"<br>Start: {full_repl.starttime}"
            rt_info += f"<br>End: {full_repl.endtime}"
            if status_str:
                rt_info += f"<br>Type: {status_str}"
            rt_info += f"<br>Room: {full_repl.room_str}"
            if full_repl.klassen_str:
                rt_info += f"<br>Classes: {full_repl.klassen_str}"
            if lesson[2]:
                rt_info += f"<br>Info: {lesson[2]}"
            title = f"{i+1}: {lesson[0]}"
            info_lbl = QLabel(f"{rt_info}")
            info_lbl.setWordWrap(True)
            self.lesson_tab.addTab(info_lbl, title)
        self.vlayout.addWidget(self.close_btn)
        self.lesson_tab.setCurrentIndex(index)
        self.close_btn.pressed.connect(self.close)

class MainWindow(QMainWindow):
    def setupUi(self, MainWindow):
        MainWindow.setWindowTitle("Untis")
        MainWindow.resize(1116, 674)
        sizePolicy = QSizePolicy(size_policy().Expanding, size_policy().Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        self.centralwidget = QWidget(MainWindow)
        sizePolicy = QSizePolicy(size_policy().Expanding, size_policy().Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)
        self.centralwidget.setAutoFillBackground(True)
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        spacerItem = QSpacerItem(20, 5, size_policy().Minimum, size_policy().Fixed)
        self.verticalLayout.addItem(spacerItem)
        self.top_bar_qhb = QHBoxLayout()
        spacerItem1 = QSpacerItem(10, 20, size_policy().Fixed, size_policy().Minimum)
        self.top_bar_qhb.addItem(spacerItem1)
        self.prev_btn = QToolButton(self.centralwidget)
        self.prev_btn.setText("")
        self.top_bar_qhb.addWidget(self.prev_btn)
        spacerItem2 = QSpacerItem(100, 20, size_policy().Maximum, size_policy().Minimum)
        self.top_bar_qhb.addItem(spacerItem2)
        self.login_btn = QPushButton(self.centralwidget)
        self.login_btn.setText("Login")
        self.top_bar_qhb.addWidget(self.login_btn)
        spacerItem3 = QSpacerItem(100, 20, size_policy().Maximum, size_policy().Minimum)
        self.top_bar_qhb.addItem(spacerItem3)
        self.reload_btn = QPushButton(self.centralwidget)
        self.reload_btn.setText("Reload")
        self.top_bar_qhb.addWidget(self.reload_btn)
        spacerItem4 = QSpacerItem(100, 20, size_policy().Maximum, size_policy().Minimum)
        self.top_bar_qhb.addItem(spacerItem4)
        self.date_edit = QDateEdit(self.centralwidget)
        self.date_edit.setDateTime(QtCore.QDateTime(QtCore.QDate(2024, 2, 16), QtCore.QTime(0, 0, 0)))
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setCurrentSectionIndex(2)
        self.top_bar_qhb.addWidget(self.date_edit)
        spacerItem5 = QSpacerItem(100, 20, size_policy().Maximum, size_policy().Minimum)
        self.top_bar_qhb.addItem(spacerItem5)
        self.next_btn = QToolButton(self.centralwidget)

        self.top_bar_qhb.addWidget(self.next_btn)
        spacerItem6 = QSpacerItem(10, 20, size_policy().Fixed, size_policy().Minimum)
        self.top_bar_qhb.addItem(spacerItem6)
        self.verticalLayout.addLayout(self.top_bar_qhb)
        self.timetable = QTableWidget(self.centralwidget)
        sizePolicy = QSizePolicy(size_policy().Expanding, size_policy().Expanding)
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
            self.timetable.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
            self.timetable.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        else:
            self.next_btn.setArrowType(QtCore.Qt.ArrowType.RightArrow)
            self.prev_btn.setArrowType(QtCore.Qt.ArrowType.LeftArrow)
            self.date_edit.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.DefaultContextMenu)
            self.timetable.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
            self.timetable.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(MainWindow)
        MainWindow.setStatusBar(self.statusbar)
        self.prev_btn.setShortcut("Left")
        self.reload_btn.setShortcut("Up, Ctrl+R")
        self.next_btn.setShortcut("Right")
        
    current_date = QDate.currentDate()
    def date_changed(self):
        new_date = self.date_edit.date()
        self.setFocus()
        if self.current_date.weekNumber() != new_date.weekNumber():
            self.fetch_week()
        self.current_date = new_date

    def cache_warn_helper(self, new_text):
        if self.cache_warning[1].text() != "" and new_text != "":
            # change text
            self.cache_warning[1].setText(new_text)
        elif self.cache_warning[1].text() != "" and new_text == "":
            # remove text
            self.cache_warning[1].setText("")
            self.cache_warning[1].hide()
            #self.verticalLayout.removeChildWidget(self.cache_warning[1])
            if not self.isFullScreen():
                self.resize(self.width(), self.cache_warning[0])
        elif self.cache_warning[1].text() == "" and new_text != "":
            # add text
            self.cache_warning[1].setText(new_text)
            self.cache_warning[1].show()
            self.cache_warning[0] = self.height()
            #self.verticalLayout.addChildWidget(self.cache_warning[1])
            if not self.isFullScreen():
                self.resize(self.width(), max(self.height(), 698))
        # fall-through is "" to "", no action needed

    def load_settings(self, no_set_credentials):
        if not no_set_credentials:
            self.server   = self.settings.value('server')
            self.school   = self.settings.value('school')
            self.user     = self.settings.value('user')
            self.password = self.settings.value('password')
        if not "--no-cache" in sys.argv:
            self.ref_cache = self.settings.value('cached_timetable') or []
        else:
            self.ref_cache = []

    def delete_settings(self):
        self.settings.clear()

    def login_popup(self):
        popup = LoginPopup(self.settings)
        popup.exec()
        self.load_settings(False)
        # try to start a new session
        credentials = [self.server, self.school, self.user, self.password]
        if None not in credentials and '' not in credentials:
            self.session = api.API(credentials, self.ref_cache)
            if type(self.session) != list: # if login successful
                self.fetch_week()
            else:
                QMessageBox.critical(
                    self,
                    self.session[0],
                    self.session[1]
                )
                self.session = None

    def info_popup(self, index=0):
        if self.is_interactive:
            popup = InfoPopup(self, index)
            popup.exec()
    
    def draw_week(self):
        selected_day = self.date_edit.date().toPyDate()
        week_number = selected_day.isocalendar()[1]
        monday = dt.date.fromisocalendar(selected_day.year, week_number, 1)
        
        self.is_interactive = False

        self.timetable.setRowCount(len(self.data))

        if not self.week_is_cached:
            self.cache_warn_helper("")
        
        # highlight the current day, if it is within the week
        current_date = QDate.currentDate()
        default_brush = QTableWidgetItem().background()
        for i in range(5):
            ref_tm = QDate(monday).addDays(i)
            if monday == current_date.addDays((i)*-1) and not self.args.no_color:
                brush = QBrush(QColor(0x30, 0xA5, 0x30))
                self.timetable.horizontalHeaderItem(i).setBackground(brush)
            else:
                self.timetable.horizontalHeaderItem(i).setBackground(default_brush)
            # https://doc.qt.io/qt-6/qdate.html#toString-1
            self.timetable.horizontalHeaderItem(i).setText(ref_tm.toString("dddd (d.M)"))
        
        # don't redraw the table when nothing changed
        if self.data == self.last_drawn_data:
            self.is_interactive = True
            return
        else:
            self.last_drawn_data = self.data

        for row in range(len(self.data)):
            for col in range(len(self.data[row])):
                widget = QFrame_click()
                try:
                    entry_data = self.data[row][col]
                    # add the on-click function for lesson info. dont change the lambda it barely works as-is
                    # this is a generic function that calls info_popup without index hint
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
                    lesson_widget = QLabel_click()
                    fn = lambda row=row, col=col, i=i: f"{self.timetable.setCurrentCell(row, col)}\n{self.info_popup(i)}"
                    lesson_widget.clicked.connect(fn)
                    lesson_widget.setTextFormat(Qt.TextFormat.RichText)
                    richtext = f"<b>{lesson[0]}</b><br>{lesson[1]}"
                    stylesheet = f"padding-right:4px; padding-left:4px; margin-top: 4px; margin-bottom:4px; border-radius:4px;"
                    if lesson[3] != "white" and not self.args.no_color:
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
                
        self.is_interactive = True

    def fetch_week(self, replace_cache=False, silent=False, skip_cache=False):
        selected_day = self.date_edit.date().toPyDate()
        week_number = selected_day.isocalendar()[1]
        monday = dt.date.fromisocalendar(selected_day.year, week_number, 1)
        friday = dt.date.fromisocalendar(selected_day.year, week_number, 5)

        if not (replace_cache or skip_cache):
            self.week_is_cached = True
            # quickly load some cache data
            api_response = None
            try:
                api_response = api.get_cached(self.ref_cache, monday)
                self.data = api_response.table
                self.draw_week()
            except Exception as e:
                if self.force_cache:
                    if not silent:
                        QMessageBox.critical(
                            self,
                            "Error loading Timetable!",
                            f"{e}"
                        )
                    return
                
        # properly fetch data
        if replace_cache:
            try:
                api_response = self.session.get_table(monday, friday, (replace_cache or skip_cache))
                self.week_is_cached = api_response.is_cached
                self.data = api_response.table
                return
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error updating Cache!",
                    f"{e}"
                )
            

        def cache_refresh(parent, monday, friday):
            try:
                api_response = parent.session.get_table(monday, friday, True)
                parent.week_is_cached = api_response.is_cached
                parent.data = api_response.table
                parent.tr_data_mon = api_response.starttime
            except Exception as e:
                parent.err_data = f"{e}"
            finally:
                parent.redraw_trip = True
        
        # if our results were from cache, asynchronously refresh that (only if already logged in)
        if (self.week_is_cached and not self.force_cache and not replace_cache and self.session != None):
            # async start a thread with api.get_table
            api_thread = threading.Thread(target=cache_refresh, args = (self, monday, friday,))
            api_thread.start()
    
    def prev_week(self):
        self.date_edit.setDate(self.date_edit.date().addDays(-7))

    def next_week(self):
        self.date_edit.setDate(self.date_edit.date().addDays(7))

    def current_week(self):
        self.date_edit.setDate(QDate.currentDate())

    def reload_all(self):
        self.ref_cache = []
        self.last_drawn_data = None
        # delete all rows and draw empty table to make the reload visible
        self.timetable.setRowCount(0)
        self.timetable.repaint()
        self.session = api.API([self.server, self.school, self.user, self.password], self.ref_cache)
        self.fetch_week()
        self.is_interactive = True

    def test_trip_redraw(self):
        if self.redraw_trip != False:
            self.redraw_trip = False
            if self.err_data != None:
                QMessageBox.critical(
                    self,
                    "Error updating Timetable!",
                    self.err_data
                )
                self.err_data = None
            # check that we didn't race the thread and are still in the same week as the data
            selected_day = self.date_edit.date().toPyDate()
            week_number = selected_day.isocalendar()[1]
            monday = dt.date.fromisocalendar(selected_day.year, week_number, 1)
            if self.tr_data_mon == monday:
                self.draw_week()
    
    def login_thread(self):
        if not self.session_trip:
            return

        credentials = [self.server, self.school, self.user, self.password]
        if None not in credentials and '' not in credentials and not self.args.force_cache:
            if self.session.error_state == None: # if login successful (already tried pre-trip)
                self.fetch_week(skip_cache=True)
            elif self.session.error_state[0] == "err":
                box = QMessageBox (
                    QMessageBox.Icon.Critical,
                    "Login Failed!",
                    f"<h3>Login Failed!</h3><b>Details:</b><br>{self.session.error_state[1]}<h4>Use cached data only?</h4>",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                self.force_cache = (box.exec() == QMessageBox.StandardButton.Yes)
                self.session = None
            else:
                # just warn about the app api, it's replaced with a stub at this point anyways
                box = QMessageBox (
                    QMessageBox.Icon.Warning,
                    "Warning: App API Error!",
                    f"<h3>App Login Failed!</h3>{self.session.error_state[1]}",
                    QMessageBox.StandardButton.Ok
                )
                box.exec()
                # :3
                self.cache_warn_helper("<span style='color:orange;'>App API failed, exams missing!</span>")
        elif self.args.force_cache:
            self.force_cache = True
            self.session = None
        else:
            # invalid credentials
            self.session = None
        
        if self.force_cache:
            self.cache_warn_helper("<span style='color:#F44;'>Cache-only mode active, restart to disable!</span>")
            self.fetch_week()
        
        # stop trying this, its useless
        self.session_timer.stop()

    def login_thread_defer(parent):
        credentials = [parent.server, parent.school, parent.user, parent.password]
        if None not in credentials and '' not in credentials and not parent.args.force_cache:
            # this part can take forever in theory
            parent.session = api.API(credentials, parent.ref_cache)

        # trip in any case, to ensure the fairly frequent login timer doesn't run forever
        parent.session_trip = True

    def __init__(self, args):
        super().__init__()
        self.args = args
        self.settings = QSettings('l-koehler', 'untis-py')
        self.is_interactive = False
        self.redraw_trip = False # tripped by thread whenever the data was asynchronously refreshed
        self.redraw_timer = QTimer()
        self.redraw_timer.timeout.connect(self.test_trip_redraw)
        self.session_trip = False
        self.session_timer = QTimer()
        self.session_timer.timeout.connect(self.login_thread)
        
        # don't overwrite argument credentials
        if args.credentials == None:
            self.load_settings(no_set_credentials=False)
        else:
            self.server, self.school, self.user, self.password = args.credentials
            self.load_settings(no_set_credentials=True)
        
        if args.delete_settings:
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

        self.date_edit.setDate(QDate.currentDate().addDays(args.offset*7))
        self.shortcut_current_week = QShortcut(QKeySequence('Down'), self)
        self.shortcut_current_week.activated.connect(self.current_week)
        self.timetable.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.date_edit.dateChanged.connect(self.date_changed)
        self.login_btn.pressed.connect(self.login_popup)
        self.timetable.cellClicked.connect(self.info_popup)
        self.prev_btn.pressed.connect(self.prev_week)
        self.next_btn.pressed.connect(self.next_week)
        self.reload_btn.pressed.connect(self.reload_all)
        self.timetable.setHorizontalHeaderLabels([""]*5)
        self.force_cache = False
        self.cache_warning = [0, QLabel()]
        self.verticalLayout.addWidget(self.cache_warning[1], 0, Qt.AlignmentFlag.AlignBottom)
        self.data = None
        self.last_drawn_data = None
        self.tr_data_mon = None
        self.session = None
        self.week_is_cached = False
        self.err_data = None
        self.show()
        
        # try loading cached data to display at-least-something during login/fetch (unless that'll happen anyways)
        if not args.force_cache:
            self.cache_warn_helper("Not yet logged in, data might be outdated!")
            
            self.force_cache = True
            self.fetch_week(silent=True)
            self.force_cache = False
        
        # if the credentials are already all set, log in asynchronously
        self.session_thread = threading.Thread(target=self.login_thread_defer)
        self.redraw_timer.start(500)
        self.session_timer.start(100)
        self.session_thread.start()

    def closeEvent(self, event):
        # save the new cache before closing
        if not self.args.no_cache and self.session != None:
            self.settings.setValue('cached_timetable', self.session.cache)
        event.accept()
        # cause a AssertionError to kill the login thread
        if self.session_thread.is_alive():
            # causes a RuntimeError in login_thread_defer by starting the already-started thread.
            # this is fully intentional, as we no longer need to login as we are already closing
            # and if a login thread returns neither result nor timeout it could get stuck for ages, leaving the program unable to close
            self.session_thread.start()
