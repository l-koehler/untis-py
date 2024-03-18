## Not made or endorsed by the Untis GMBH!
## For the official App, visit untis.at!

#### Features
Basic Desktop application for WebUntis, written in Python.  
Loads a lot faster than the website, especially when considering starting a browser.  

#### Limitations
Read-only: The API is read-only, can't do anything about that  
Weeks are limited to 5 days with 8 hours. Will change later  
The UI is atrocious: seriously it takes up 3/4 of my screen, sorry ig  

#### Installation
You need the following Dependencies:  
* PyQt6 (you can also use PyQt5 by passing `--qt5` to the program)  
* webuntis  
* python-datetime  

Install these and run main.py.  
TODO (later): Package this and publish to pip  

#### Compile on Windows
Maybe "compile" the .svg if you changed it:  
```
magick -background transparent -define 'icon:auto-resize=16,24,32,64' ./icon.svg ./icon.ico
```
Create a .exe (`./dist/main.exe`)  
```
set PYTHONOPTIMIZE=2
pyinstaller --onefile --add-data="mainwindow.ui;." --add-data="login.ui;." --add-data="lesson_info.ui;." --add-data="icon.ico;." --windowed --icon="./icon.ico" main.py
```
The releases on github are compressed using [UPX](https://upx.github.io/),  
the uncompressed size is about 32 MB.  
