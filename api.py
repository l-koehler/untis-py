import webuntis, json, requests, urllib, time, web_utils
import datetime as dt

def get_cached(cache, starttime):
    timetable = None
    for cache_entry in cache:
        if cache_entry[0] == starttime:
            return API_Response(cache_entry[1], True, cache_entry[0])
    raise CacheMiss("Week not cached, but cache-only mode active!")

def school_search(partial_name):
    # return: [display name, server URL]
    baseurl = "https://schoolsearch.webuntis.com/schoolquery2"
    json = {
        "id": "untis-mobile-blackberry-2.7.4",
        "jsonrpc": "2.0",
        "method": "searchSchool",
        "params": [{
            "search": f"{partial_name}"
        }]
    }
    data = requests.post(url=baseurl, json=json).json()
    if "error" in data:
        return [data["error"]["message"], "ERR"]
    return [
        [school["loginName"], school["server"]] for school in data["result"]["schools"]
    ]

"""
Version of "PeriodObject" that doesn't include any session references.
Used for Lesson Info popups from cache
"""
class SerPeriod:
    def __init__(self, periodObject):
        self.activityType = str(periodObject.activityType)
        self.code = str(periodObject.code)
        self.type = str(periodObject.type)
        if len(periodObject.klassen) == 1:
            self.klassen_str = periodObject.klassen[0].name
        else:
            self.klassen_str = '; '.join([i.name for i in periodObject.klassen])
        self.long_name = periodObject.subjects[0].long_name
        self.starttime = periodObject.start.time().strftime('%H:%M')
        self.endtime = periodObject.end.time().strftime('%H:%M')
        try:
            self.room_str = f"{periodObject.rooms[0].name}"
            if periodObject.original_rooms != periodObject.rooms and periodObject.original_rooms != []:
                self.room_str += f" (originally in {periodObject.original_rooms[0].name})"
        except IndexError:
            self.room_str = "Unknown"
            
    # Consider all SerPeriods equal (for checking if a redraw is needed)
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return True
        else:
            return False

"""
API Response object, contains the timetable and some extra info
Implements __eq__ to check if the responses would be _visually_ any different when rendered
"""
class API_Response:
    def __init__(self, table, is_cached, starttime):
        self.table = table
        self.is_cached = is_cached
        self.starttime = starttime
        
# these can be raised instead of returning a response
class CacheMiss(Exception):
    """Raise when cache forced but no entry present"""
    pass
class InvalidDate(Exception):
    """like webuntis.errors.DateNotAllowed"""
    pass
class ServerReplError(Exception):
    """Reading timetable failed, server replied with {message}"""
    pass
class APIReplError(Exception):
    """Like above, but for the App API"""
    pass
"""
This part combines the two untis APIs to get a usable timetable
It also deals with caching logic and some reformatting
"""

class API:
    def __init__(self, credentials, cache):
        self.cache = cache
        self.error_state = None
        
        new_session = webuntis.Session(
            server=credentials[0],
            school=credentials[1],
            username=credentials[2],
            password=credentials[3],
            useragent="WebUntis Desktop"
        )
        try:
            self.session = new_session.login()
        except webuntis.errors.RemoteError as e:
            self.session = None
            self.error_state = ["err", f"<b>Error:</b> {e}<br>Check credentials!"]
            return
        except Exception as e:
            self.session = None
            self.error_state = ["err", f"<b>Error:</b> {e}"]
            return
        
        self.app_api = App_API(credentials)
        try:
            self.app_api.login()
        except Exception as e:
            self.error_state = ["warn", f"<b>Warning:</b> App API Error encountered, App API disabled. Exams will not be displayed!<br><b>API Error:</b> {e}"]
            self.app_api = App_API_Stub()
            return


    def get_table(self, starttime, endtime, no_cache=False):
        # try loading from cache
        timetable = None
        if no_cache == False:
            for cache_entry in self.cache:
                if cache_entry[0] == starttime:
                    return API_Response(cache_entry[1], True, cache_entry[0])
        # didnt load, ask the server
        try:
            timetable = self.session.my_timetable(
                start=starttime, end=endtime
            )
            timetable = timetable.to_table()
        except webuntis.errors.DateNotAllowed as err:
            raise InvalidDate("Date not allowed! (is it within a single school year?)")
        except Exception as err:
            raise ServerReplError(f"Server replied with error: \"{err}\"!")
        if "error" in timetable:
            raise ServerReplError(f"Server replied with error: \"{err}\"!")

        exam_table = self.app_api.getExams(starttime, endtime)
        if "error" in exam_table:
            raise APIReplError(f"App API replied with error: \"{exam_table['error']}\"!")
        exam_table = exam_table["result"]["exams"]
        
        ret = []
        # add one because same-day still is one day
        time_range = range((endtime - starttime).days + 1)
        # somewhat comprehensible parser (might be a lie)
        for vertical_time_range in timetable:
            vertical_time = vertical_time_range[0]
            for weird_blob in vertical_time_range[1:]:
                blob_ret = [[] for _ in time_range]
                for day in weird_blob:
                    day_n = (day[0] - starttime).days
                    lesson = day[1]
                    day_ret = []
                    for period in list(lesson):
                        subject = period.subjects[0]
                        for exam in exam_table:
                            if exam["subjectId"] == subject.id:
                                exam_start = dt.datetime.strptime(exam["startDateTime"], '%Y-%m-%dT%H:%MZ')
                                exam_end = dt.datetime.strptime(exam["endDateTime"], '%Y-%m-%dT%H:%MZ')
                                is_within_period = exam_start <= period.start and exam_end >= period.end
                                if is_within_period:
                                    period.code = "exam"
                                    period.type = "ex"
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
                        elif period.code == "exam":
                            color = "blue"
                        elif period.code == "irregular" or rooms_changed:
                            color = "orange"
                        elif period.code_color != None:
                            color = period.code_color
                        else:
                            color = "white"
                        period_specific_item = [subject.name, room_str, notes_str, color, SerPeriod(period)]
                        day_ret.append(period_specific_item)
                    day_ret.sort()
                    blob_ret[day_n] = day_ret
                ret.append(blob_ret)
        """
        Structure of ret:
        list of "hours", each containing one list per day, each containing a period_specific_item
        """
        self.cache = [i for i in self.cache if i[0] != starttime]
        self.cache.append([starttime, ret])
        return API_Response(ret, False, starttime)

"""
This part deals with the undocumented mobile API.
Some repeated functions were split into web_utils.py.
Refer to https://github.com/SapuSeven/BetterUntis/wiki/Untis-Mobile-API-Reference
"""
class App_API:
    def __init__(self, credentials):
        self.session = requests.Session()
        
        self.server=credentials[0]
        self.school=credentials[1]
        self.username=credentials[2]
        self.password=credentials[3]
        
        self.api_url = f"https://{self.server}/WebUntis/jsonrpc_intern.do"
        
        # "magic values" obtained from BetterUntis
        self.untis_id = "untis-mobile-blackberry-2.7.4"
        self.version = "i5.12.3"
        
    def login(self):
        self.getAppSharedSecret()
        self.getUserData()

    def getAuth(self):
        auth = {
            "clientTime": int(time.time() * 1000),
            "otp": web_utils.create_time_based_code(self.secret),
            "user": self.username
        }
        return auth

    def getAppSharedSecret(self):
        url_params = {
            "school": self.school,
            "m": f"getAppSharedSecret",
            "a": "true",
            "v": self.version
        }
        data = {
            "id": self.untis_id,
            "jsonrpc": "2.0",
            "method": f"getAppSharedSecret",
            "params": [{
                "userName": self.username,
                "password": self.password
            }]
        }
        api_url = web_utils.concat_literal_params(self.api_url, url_params)
        data = self.session.post(api_url, json=data)
        self.secret = data.json()["result"]
        
    def genericAuthenticatedRequest(self, method, parameters):
        url_params = {
            "school": self.school,
            "m": method,
            "a": "true",
            "v": self.version
        }
        data = {
            "id": self.untis_id,
            "jsonrpc": "2.0",
            "method": method,
            "params": [{**{
                "auth": self.getAuth()
            }, **parameters}]
        }
        api_url = web_utils.concat_literal_params(self.api_url, url_params)
        data = self.session.post(api_url, json=data)
        return data.json()

    def getUserData(self):
        response = self.genericAuthenticatedRequest("getUserData2017", {})
        self.user_type = response["result"]["userData"]["elemType"]
        self.user_id =   response["result"]["userData"]["elemId"]
    
    def getExams(self, monday, friday):
        params = {
            "id": self.user_id,
            "type": self.user_type,
            "startDate": monday.isoformat(),
            "endDate": friday.isoformat()
        }
        response = self.genericAuthenticatedRequest("getExams2017", params)
        return response

    # unused
    # works, but would be a pain to write so we keep using 'webuntis' for this
    def getTimetable(self, monday, friday):
        params = {
            "id": self.user_id,
            "type": self.user_type,
            "startDate": monday.isoformat(),
            "endDate": friday.isoformat(),
            # the following parameters are commented as "unknown usage" on BetterUntis
            "masterDataTimestamp": 0,
            "timetableTimestamp" : 0,
            "timetableTimestamps": []
        }
        response = self.genericAuthenticatedRequest("getTimetable2017", params)
        return response

class App_API_Stub:
    def getExams(self, a, b):
        return {"result": {"exams": []}}
