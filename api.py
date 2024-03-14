import webuntis
import datetime as dt
from PyQt6.QtWidgets import QMessageBox

def login(self, credentials):
    new_session = webuntis.Session(
        username=credentials[2],
        password=credentials[3],
        server=credentials[0],
        school=credentials[1],
        useragent="WebUntis Desktop",
    )
    try:
        s = new_session.login()
        return s
    except webuntis.errors.RemoteError as e:
        # Invalid credentials
        dlg = QMessageBox.critical(
            self,
            "Login failed!",
            f"Error: \"{e}\". Check credentials!"
        )
        return None
    except Exception as e:
        # Likely network error
        dlg = QMessageBox.critical(
            self,
            "Login failed!",
            f"Unknown Error: {e}"
        )
        return None

def class_by_name(self, name):
    for klasse in self.session.klassen():
        if klasse.name == name:
            return klasse
    dlg = QMessageBox.critical(
        self,
        "Class could not be selected!",
        "Open issue at https://github.com/l-koehler/untis-desktop"
    )
    exit(-1)

def get_table(self, starttime, endtime, klasse):
    # try loading from cache
    timetable = None
    for cache_entry in self.cached_responses:
        if cache_entry[0] == starttime:
            return cache_entry[1]
    # didnt load, ask the server
    try:
        if timetable == None:
            timetable = self.session.timetable_extended(
                start=starttime, end=endtime, klasse=klasse
            ).to_table()
    except webuntis.errors.RemoteError:
        dlg = QMessageBox.critical(
            self,
            "Permision Error!",
            f"The user {self.user} does not have permission to view the Timetable for {klasse.name}!"
        )
        return None
    except Error as err:
        dlg = QMessageBox.critical(
            self,
            "Reading Timetable failed!",
            f"Unknown Error: \"{err}\"!"
        )
        return None
    ret = []
    # somewhat comprehensible parser (might be a lie)
    for vertical_time_range in timetable:
        vertical_time = vertical_time_range[0]
        for weird_blob in vertical_time_range[1:]:
            blob_ret = []
            for day in weird_blob:
                #date = day[0]
                lesson = day[1]
                day_ret = []
                for period in list(lesson):
                    subject = period.subjects[0]
                    # period_specific_item: A single Lesson.
                    # This Lesson is packed in a list with other lessons at the same time.
                    notes = []
                    if period.info != "":
                        notes.append(period.info)
                    if period.type == "ex":
                        notes.append("Exam")
                    if notes == []:
                        notes_str = ""
                    elif len(notes) == 1:
                        notes_str = notes[0]
                    else:
                        notes_str = "; ".join(notes)

                    # string indicating room
                    rooms_changed = False
                    if len(period.rooms) == 0:
                        room_str = ""
                    elif period.original_rooms != period.rooms and period.original_rooms:
                        room_str = f"{period.original_rooms[0].name} -> {period.rooms[0].name}"
                        rooms_changed = True
                    else:
                        room_str = period.rooms[0].name

                    # string indicating color
                    if period.code == "cancelled":
                        color = "red"
                    elif period.code == "irregular" or rooms_changed:
                        color = "orange"
                    else:
                        color = "white"

                    period_specific_item = [subject.name, room_str, notes_str, color, period]
                    day_ret.append(period_specific_item)
                blob_ret.append(day_ret)
            ret.append(blob_ret)
    """"
    Structure of ret:
    list of "hours", each containing one list per day, each containing the structure in L89
    """
    return ret
