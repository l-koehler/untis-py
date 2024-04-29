import webuntis

def login(credentials):
    new_session = webuntis.Session(
        server=credentials[0],
        school=credentials[1],
        username=credentials[2],
        password=credentials[3],
        useragent="WebUntis Desktop"
    )
    try:
        s = new_session.login()
        return s
    except webuntis.errors.RemoteError as e:
        return ["Login Failed!", f"Error: \"{e}\". Check credentials!"]
    except Exception as e:
        return ["Login Failed!", f"Error: \"{e}\""]

def get_table(cache, session, starttime, endtime):
    # try loading from cache
    timetable = None
    for cache_entry in cache:
        if cache_entry[0] == starttime:
            return cache_entry[1]
    # didnt load, ask the server
    try:
        timetable = session.my_timetable(
            start=starttime, end=endtime
        ).to_table()
    except Exception as err:
        exit()
        return ["err", "Reading Timetable failed", f"Unknown Error: \"{err}\"!"]
    ret = []
    # somewhat comprehensible parser (might be a lie)
    for vertical_time_range in timetable:
        vertical_time = vertical_time_range[0]
        for weird_blob in vertical_time_range[1:]:
            blob_ret = [[],[],[],[],[]]
            for day in weird_blob:
                day_n = (day[0] - starttime).days
                lesson = day[1]
                day_ret = []
                for period in list(lesson):
                    subject = period.subjects[0]
                    # period_specific_item: A single Lesson.
                    # This Lesson is packed in a list with other lessons at the same time.
                    notes = []
                    if period.info != "":
                        notes.append(period.info)
                    if period.substText != "":
                        notes.append(period.substText)
                    if period.type == "ex":
                        notes.append("Exam")
                    if notes == []:
                        notes_str = ""
                    elif len(notes) == 1:
                        notes_str = notes[0]
                    else:
                        notes_str = "; ".join(notes)

                    # string indicating room
                    try:
                        rooms_changed = False
                        if len(period.rooms) == 0:
                            room_str = ""
                        elif period.original_rooms != period.rooms and period.original_rooms:
                            room_str = f"{period.original_rooms[0].name} -> {period.rooms[0].name}"
                            rooms_changed = True
                        else:
                            room_str = period.rooms[0].name
                    except IndexError:
                        rooms_changed = True
                        room_str = "Unknown"

                    # string indicating color
                    if period.code == "cancelled":
                        color = "red"
                    elif period.code == "irregular" or rooms_changed:
                        color = "orange"
                    elif period.code_color != None:
                        color = period.code_color
                    else:
                        color = "white"
                    period_specific_item = [subject.name, room_str, notes_str, color, period]
                    day_ret.append(period_specific_item)
                blob_ret[day_n] = day_ret
            ret.append(blob_ret)
    """"
    Structure of ret:
    list of "hours", each containing one list per day, each containing the structure in L89
    """
    return ret
