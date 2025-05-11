from datetime import date
from . import api
from dateutil.relativedelta import relativedelta, FR, MO

# text-only mode
class colors:
    blue   = "\033[94m"
    cyan   = "\033[96m"
    skip   = "\033[65m" # "no ideogram attributes", used to fix some mess with string lengths
    yellow = "\033[93m"
    green  = "\033[92m"
    red    = "\033[91m"
    reset  = "\033[0m"

def main(args):
    starttime = date.today() + relativedelta(weekday=MO(-1))
    starttime += relativedelta(weeks=args.offset)
    endtime = starttime + relativedelta(weekday=FR)

    qt_ver = None
    settings = None
    if args.credentials == None or not args.force_cache or args.delete_settings:
        if args.force_qt5:
            from PyQt5.QtCore import QSettings
        elif args.force_qt6:
            from PyQt6.QtCore import QSettings
        else:
            try:
                from PyQt6.QtCore import QSettings
            except ImportError:
                from PyQt5.QtCore import QSettings
        settings = QSettings('l-koehler', 'untis-py')

    if args.delete_settings:
        settings.clear()

    # server, school, username, password
    credentials = [None, None, None, None]
    if args.credentials == None:
        if credentials[0] == None: credentials[0] = settings.value('server')
        if credentials[1] == None: credentials[1] = settings.value('school')
        if credentials[2] == None: credentials[2] = settings.value('user')
        if credentials[3] == None: credentials[3] = settings.value('password')
    else:
        credentials = args.credentials

    timetable = None
    if args.force_cache:
        cache = settings.value('cached_timetable') or []
        timetable = api.get_cached(cache, starttime).table
    else:
        session = api.API(credentials, [])
        if session.error_state != None:
            print(f"Failed to login: {session.error_state}")
            exit(1)
        timetable = session.get_table(starttime, endtime).table
    prettyprint_response(timetable, args)


def prettyprint_response(timetable, args):
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
                if not args.no_color:
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
    # i lied, final_response isn't even close to final
    for day in [day for day in final_response if day != ""]:
        day_as_ls = day.split('\n')
        if index == date.today().weekday() and not args.no_color:
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
