import webuntis, json, requests, urllib, time, base64, hmac, hashlib, web_utils
import datetime as dt

def get_cached(cache, starttime):
    timetable = None
    for cache_entry in cache:
        if cache_entry[0] == starttime:
            return [True, cache_entry[1]]
    return ["err", "Reading Timetable failed", f"Week not cached, but cache-only mode active!"]

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
This part directly accesses the public/documented API and
uses App_API for access to the undocumented one
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
            self.error_state = f"Error: \"{e}\". Check credentials!"
            print(self.error_state)
            return
        except Exception as e:
            self.session = None
            self.error_state = f"Error: \"{e}\""
            print(self.error_state)
            return
        self.app_api = App_API(credentials)
        try:
            self.app_api.login()
        except Exception as e:
            self.error_state = f"App API Error: \"{e}\""
            print(self.error_state)
            return


    def get_table(self, starttime, endtime, no_cache=False):
        # try loading from cache
        timetable = None
        if no_cache == False:
            for cache_entry in self.cache:
                if cache_entry[0] == starttime:
                    return [True, cache_entry[1]]
        # didnt load, ask the server
        try:
            timetable = self.session.my_timetable(
                start=starttime, end=endtime
            )
            timetable = timetable.to_table()
        except Exception as err:
            if (err == "startDate and endDate are not within a single school year."):
                return ["err", "Reading Timetable failed", "Weeks spanning several school years are not supported!"]
            return ["err", "Reading Timetable failed", f"Server replied with error: \"{err}\"!"]
        if "error" in timetable:
            return ["err", "Unknown Error", f"Server replied with error: \"{err}\"!"]

        exam_table = self.app_api.getExams(starttime, endtime)
        if "error" in exam_table:
            return ["err", "Unknown App API Error", f"Server replied with error: \"{err}\"!"]
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
                            if exam["subjectId"] == subject.id and exam["startDateTime"] == period.start.strftime('%Y-%m-%dT%H:%M') + 'Z':
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
                        period_specific_item = [subject.name, room_str, notes_str, color, period]
                        day_ret.append(period_specific_item)
                    blob_ret[day_n] = day_ret
                ret.append(blob_ret)
        """
        Structure of ret:
        list of "hours", each containing one list per day, each containing a period_specific_item
        """
        self.cache = [i for i in self.cache if i[0] != starttime]
        self.cache.append([starttime, ret])
        return [False, ret]

"""
This part deals with the undocumented mobile API.
Some repeated functions were split into web_utils.py.
These functions sometimes are translated code from https://github.com/SapuSeven/BetterUntis
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
        

    # verify_code and create_time_based_code are almost completely from BetterUntis
    def verify_code(self, key: bytes, time: int) -> int:
        t = time
        array_of_byte = bytearray(8)

        for i in range(8):
            array_of_byte[7 - i] = t & 0xFF
            t >>= 8

        local_mac = hmac.new(key, array_of_byte, hashlib.sha1)
        hashed_key = local_mac.digest()
        k = hashed_key[19] & 0xFF
        t = 0

        for i in range(4):
            l = hashed_key[(k & 0xF) + i] & 0xFF
            t = (t << 8) | l

        return (t & 0x7FFFFFFF) % 1000000

    def create_time_based_code(self) -> int:
        timestamp = int(time.time() * 1000)
        if self.secret and len(self.secret) > 0:
            decoded_key = base64.b32decode(self.secret.upper(), casefold=True)
            return self.verify_code(decoded_key, timestamp // 30000)  # Code will change every 30000 milliseconds
        else:
            return 0

    def getAuth(self):
        auth = {
            "clientTime": int(time.time() * 1000),
            "otp": self.create_time_based_code(),
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
