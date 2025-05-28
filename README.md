**This is a mirror of https://codeberg.org/l-koehler/untis-py**  
**I likely won't see pull requests / issues here!**  

For the official (mobile) app, visit untis.at!

## Limitations

Weeks are limited to 5 days with 8 hours. Might change later.  
The UI is atrocious: seriously it takes up 3/4 of my screen, sorry ig  

## Installation

figure it out, i give up.  

## On NixOS

There is a flake file, use that.  
You can use `nix develop` or direnv to get a dev shell with all dependencies.  

## Logging in

Search your School in the top textbox, then select it from the dropdown menu.  
If you can't find your school, look at what is written behind the `?school=`  
part of the login website.  

The username and password are just whatever you use for the website.  

## Arguments

```text
usage: main.py [-h] [-t] [--force-qt5 | --force-qt6] [--delete-settings] [--no-cache | --force-cache]
               [-o OFFSET] [--no-color] [--credentials SERVER SCHOOL USERNAME PASSWORD]

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

The `--credentials` flag takes 4 arguments:  

* Server: Something like `subdomain.webuntis.com`, same as for the website  
* School: From the WebUntis `?school` parameter, for example `HS+Some+School`. Used in the website login page URL.  
* Username and Password are the same as for the website.  

## Other notes

If you changed the `icon.svg` file, regenerate the `.ico`/`.png` files:  

```sh
cd ./untis_py/icons
magick -background transparent -define 'icon:auto-resize=16,24,32,64' ./icon.svg ./icon.ico
magick ./icon.svg -transparent white ./icon.png && magick -resize 48x48 ./icon.png ./icon.png
```

This Program is GPL3-licensed to be compatible with [BetterUntis](https://github.com/sapuseven/betteruntis),  
from which some code and a lot of research was copied.  
In particular, several functions in web_utils.py are translated from BetterUntis.  
