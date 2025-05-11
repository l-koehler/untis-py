#!/usr/bin/env python3
import sys, argparse

parser = argparse.ArgumentParser()
parser.add_argument("-t", "--text-only", help="output to terminal instead of UI", action="store_true")
force_ver = parser.add_mutually_exclusive_group()
force_ver.add_argument("--force-qt5", help="only use pyqt5, fail even if pyqt6 is available", action="store_true")
force_ver.add_argument("--force-qt6", help="only use pyqt6, fail even if pyqt5 is available", action="store_true")
parser.add_argument("--delete-settings", help="delete settings (cache and credentials) before start", action="store_true")
cache_mode = parser.add_mutually_exclusive_group()
cache_mode.add_argument("--no-cache", help="skip reading/writing cache data", action="store_true")
cache_mode.add_argument("--force-cache", help="never connect to webuntis, only use cache", action="store_true")
parser.add_argument("-o", "--offset", help="offset the initially displayed week by OFFSET (positive or negative)", type=int, default=0)
parser.add_argument("--no-color", help="don't highlight special lessons (text-only mode: disable color codes)", action="store_true")
parser.add_argument("--credentials", nargs=4, metavar=("SERVER","SCHOOL","USERNAME","PASSWORD"), type=str, help="Temporary credentials that won't be saved. When used with text-only mode, pyqt is not needed.", default=None)
args = parser.parse_args()

if args.text_only:
    from . import tui
    tui.main(args)
    sys.exit(0)
else:
    from . import gui
    app = gui.QApplication(sys.argv)
    window = gui.MainWindow(args)
    app.exec()
    sys.exit(0)
