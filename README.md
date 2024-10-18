## Not made or endorsed by the Untis GMBH!
## For the official (mobile) App, visit untis.at!

### Limitations
Weeks are limited to 5 days with 8 hours. Might change later.  
The UI is atrocious: seriously it takes up 3/4 of my screen, sorry ig  

### Installation on Linux
You need the following Dependencies:  

* PyQt6 (you can also use PyQt5 by passing `--qt5` to the program)  
* webuntis    (python package)  
* py-datetime (python package)  

Also required, but commonly already present is the "requests" package.  

Install these and run `python3 ./main.py` to see if it works.  
If you want to have it available in the Menu, run `./install.sh` (on linux).  
After running the install script, you can safely remove this folder.  

The install script registers the `untis` command to open this program.  

* You can pass `--system` to the script to install this program for all users  
* You can pass `--uninstall` to uninstall this program.  

`--uninstall` works even if you only download the script. You still need  
to pass `--system` if your installation is system-wide, but nothing bad  
will happen if you don't do that (it just won't work).  

You can re-run the script without data loss at least for minor updates.  

### Compile on Windows
Create a .exe (`./dist/main.exe`)  
```
set PYTHONOPTIMIZE=2
pyinstaller --onefile --add-data="icon.ico;." --windowed --icon="./icon.ico" main.py
```

You can move the resulting exe wherever, there is no proper installation.  

### Logging in

Search your School in the top textbox, then select it from the dropdown menu.  
If you can't find your school, look at what is written behind the `?school=`  
part of the login website.  

The username and password are just whatever you use for the website.  

### Arguments
```
usage: main.py [-h] [-t] [--force-qt5 | --force-qt6] [--delete-settings] [--no-cache | --force-cache] [-o OFFSET] [--no-color]
               [--credentials SERVER SCHOOL USERNAME PASSWORD]

options:
  -h, --help            show this help message and exit
  -t, --text-only       output to terminal instead of UI
  --force-qt5           only use pyqt5, fail even if pyqt6 is available
  --force-qt6           only use pyqt6, fail even if pyqt5 is available
  --delete-settings     delete settings (cache and credentials) before start
  --no-cache            skip reading/writing cache data
  --force-cache         never connect to webuntis, only use cache
  -o OFFSET, --offset OFFSET
                        offset the initially displayed week by OFFSET (positive or negative)
  --no-color            don't highlight special lessons (text-only mode: disable color codes)
  --credentials SERVER SCHOOL USERNAME PASSWORD
                        Temporary credentials that won't be saved. When used with text-only mode, pyqt is not needed.
```

### Other notes
If you changed the `icon.svg` file, regenerate the `.ico`/`.png` files:  
```
magick -background transparent -define 'icon:auto-resize=16,24,32,64' ./icon.svg ./icon.ico
magick ./icon.svg -transparent white ./icon.png && magick -resize 48x48 ./icon.png ./icon.png
```
This Program is GPL3-licensed to be compatible with [BetterUntis](https://github.com/sapuseven/betteruntis),  
from which some code and a lot of research was copied.  
In particular, several functions in web_utils.py are translated from BetterUntis.  

