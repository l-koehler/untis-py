## Not made or endorsed by the Untis GMBH!
## For the official (mobile) App, visit untis.at!

### Limitations
Read-only: The API is read-only, can't do anything about that.  
No Tests: These are not exposed through the API, can't change that. 
Weeks are limited to 5 days with 8 hours. Might change later.  
The UI is atrocious: seriously it takes up 3/4 of my screen, sorry ig  

### Installation on Linux
You need the following Dependencies:  

* PyQt6 (you can also use PyQt5 by passing `--qt5` to the program)  
* webuntis    (python package)  
* py-datetime (python package)  

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

The server should be something like `subdomain.webuntis.com` and is the   
domain + subdomain you use when logging into the website.  

The school is found in the `?school=` URL parameter of the website login page.  

For example:
The login URL `https://thing.webuntis.com/WebUntis/?school=HS+Example+School#/basic/login`  
will result in the server `thing.webuntis.com` and the school `HS+Example+School`.  

The username and password are just whatever you use for the website.  

### Arguments
* Use `--qt5` to force the program to use PyQt5, it will otherwise  
  use PyQt6 if available.  
* Use `--fake-data` to test the program without connecting to WebUntis.  
  (not when using `--text-only`, only with the Qt UI).  
* Use `--delete-settings` to forget the stored login data and cache.  
* Use `--no-cache` to (only this time) skip loading/saving cache.  
  This does not disable caching entirely, just the loading/saving!  
* Use `--force-cache` to enter cache-only mode. This will prevent  
  the program from connecting to WebUntis entirely.  
* If `--credentials <server> <school> <username> <password>` is  
  passed to the program, QSettings will not be used.  
  In combination with `--text-only`, this allows for usage of the program  
  without installing PyQt.  

### Terminal-only arguments
* Use `-t` or `--text-only` to not use an UI,  
  instead outputting a formatted table to the console.  
  This will also disable using the cache for timetable data.  
* Use `--offset <weeks>` or `-o<weeks>` to get another week.  
  The offset can be negative.  
* Use `--no-color` to disable color codes.  

### Other notes
If you changed the `icon.svg` file, regenerate the `.ico`/`.png` files:  
```
magick -background transparent -define 'icon:auto-resize=16,24,32,64' ./icon.svg ./icon.ico
magick ./icon.svg -transparent white ./icon.png && magick -resize 48x48 ./icon.png ./icon.png
```
