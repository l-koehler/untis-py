import sys, api
from datetime import date
from dateutil.relativedelta import relativedelta, FR, MO

if '-t' not in sys.argv and '--text-only' not in sys.argv:
    import gui
    app = gui.QApplication(sys.argv)
    window = gui.MainWindow()
    app.exec()
    sys.exit(0)

# text-only mode
class colors:
    blue   = "\033[94m"
    cyan   = "\033[96m"
    skip   = "\033[65m" # "no ideogram attributes", used to fix some mess with string lengths
    yellow = "\033[93m"
    green  = "\033[92m"
    red    = "\033[91m"
    reset  = "\033[0m"
use_color = not "--no-color" in sys.argv

# server, school, username, password
credentials = [None, None, None, None]
starttime = date.today() + relativedelta(weekday=MO(-1))
for index in range(len(sys.argv)):
    if sys.argv[index] == '--credentials':
        if len(sys.argv) < index+5:
            print(f"--credentials takes 4 arguments, {len(sys.argv)-index-1} were passed!")
            print("use --credentials <server> <school> <username> <password>")
            exit(1)
        credentials[0] = sys.argv[index+1]
        credentials[1] = sys.argv[index+2]
        credentials[2] = sys.argv[index+3]
        credentials[3] = sys.argv[index+4]
    elif sys.argv[index].startswith("-o"):
        offset = int(sys.argv[index][2:])
        starttime += relativedelta(weeks=offset)
    elif sys.argv[index] == '--offset':
        offset = int(sys.argv[index+1])
        starttime += relativedelta(weeks=offset)
endtime = starttime + relativedelta(weekday=FR)

if None in credentials:
    # not all credentials were given, use QSettings to load them
    print("\"--credentials <server> <school> <user> <password>\" not given, using QSettings!")
    use_qt5 = True
    if not "--qt5" in sys.argv:
        use_qt5 = False
        try:
            from PyQt6.QtCore import QSettings
        except ImportError:
            use_qt5 = True
    if use_qt5:
        from PyQt5.QtCore import QSettings
    settings = QSettings('l-koehler', 'untis-py')
    if credentials[0] == None: credentials[0] = settings.value('server')
    if credentials[1] == None: credentials[1] = settings.value('school')
    if credentials[2] == None: credentials[2] = settings.value('user')
    if credentials[3] == None: credentials[3] = settings.value('password')

session = api.login(credentials)
if type(session) == list:
    print(f"Failed to login: {session[1]}")
    exit(1)

timetable = api.get_table([], session, starttime, endtime)

# total mess, but transforms the API response into a nice-looking table
"""
| Monday                  |
|-------------------------|
| GGK (004)               |
| GGK (002  -> 004)       |
| GGK (003) | EEEPY (E04) |

"""

final_response = ["", "", "", "", "", "", ""]

longest_entry = 11
for hour in timetable:
    for day in hour:
        final_str = ""
        for period in day:
            if len(f" {period[0]} ({period[1]}) ") > longest_entry:
                longest_entry = len(f" {period[0]} ({period[1]}) ")
longest_entry += 1

for hour in timetable:
    for day_index in range(len(hour)):
        day = hour[day_index]
        for period_index in range(len(day)):
            period = sorted(day)[period_index]
            period_str = f" {period[0]} ({period[1]}) ".ljust(longest_entry)
            if use_color:
                if period[3] == "red":
                    period_str = colors.red + period_str + colors.reset
                elif period[3] == "orange":
                    period_str = colors.yellow + period_str + colors.reset
                elif period[3] != "white":
                    period_str = colors.cyan + period_str + colors.reset
                else:
                    period_str = colors.skip + period_str + colors.reset
            final_response[day_index] += period_str
            if len(day) != 1 and period_index != len(day)-1:
                final_response[day_index] += "|"
        final_response[day_index] = final_response[day_index].ljust(longest_entry)
        final_response[day_index] += "\n"

weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
index = 0
for day in [day for day in final_response if day != ""]:
    day_as_ls = day.split('\n')
    if index == date.today().weekday() and use_color:
        default_top = (f"═ {colors.green}{weekdays[index]}{colors.reset} ").ljust(longest_entry+len(colors.green+colors.reset), '═')
    else:
        default_top = (f"═ {weekdays[index]} ").ljust(longest_entry, '═')
    index_split_lsn = []
    for line in day_as_ls:
        for char_i in range(len(line)):
            if line[char_i] == "|":
                if char_i not in index_split_lsn:
                    index_split_lsn.append(char_i)
    for i in index_split_lsn:
        default_top = default_top[:i] + '╤' + default_top[i+1:].ljust(longest_entry, '═')
    print(f"╔{default_top}╗")
    for line in day_as_ls:
        if line != "":
            lsn_split_line = line
            for i in index_split_lsn:
                lsn_split_line = lsn_split_line[:i] + '│' + lsn_split_line[i+1:].ljust(longest_entry)
            print(f"║{lsn_split_line}║")
    default_bottom = ''.ljust(longest_entry, '═')
    for i in index_split_lsn:
        default_bottom = default_bottom[:i] + '╧' + default_bottom[i+1:].ljust(longest_entry, '═')
    print(f"╚{default_bottom}╝")
    print("")
    index += 1
