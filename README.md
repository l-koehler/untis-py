#### Features
Basic Desktop application for WebUntis, written in Python.  
Loads a lot faster than the website, especially when considering starting a browser.  

#### Limitations
Read-only: The API is read-only, can't do anything about that  
Weeks are limited to 5 days with 8 hours. Will change later  
The UI is atrocious: seriously it takes up 3/4 of my screen, sorry ig  

#### Installation
You need the following Dependencies:  
* PyQt6  
* webuntis  
* python-datetime  

Install these and run main.py.  
TODO (later): Package this and publish to pip  

#### Compile on Windows
```
set PYTHONOPTIMIZE=2
pyinstaller --noupx --onefile --add-data="mainwindow.ui;." --add-data="login.ui;." --add-data="lesson_info.ui;." --windowed --icon="./icon.ico" main.py
```

#### Other stuff
Icon taken from [iconduck.com](https://iconduck.com/icons/245483/untis-mobile), where it is under the [Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0) License.  
