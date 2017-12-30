Linux Electronic Whiteboard with Wiimote
========================================

With this software you can build and operate a low-cost electronic 
whiteboard. You only need a wiimote, an IR pen and a great OS: gnu/linux.

If you have git installed on your system you can get the latest (development)
version, typing:

$ git clone git://github.com/pnegre/python-whiteboard.git

To download packaged versions of the program, point your browser to
http://github.com/pnegre/python-whiteboard/downloads

It's recommended to disable the desktop effects, to avoid program crashes and
malfunctions.


Compilation and installation
----------------------------

Use make:

$ make all
# make install

If you want to create a .deb package:

$ make deb

Required packages:

- To run the program: python-bluez python-qt5 python-numpy python-xlib
  python python-support python-future
- To run make: libqt5-dev qt5-dev-tools python-qt5-dev
- To build the deb package: build-essential fakeroot dpkg-dev debhelper


Configuration
-------------

The configuration screen has been integrated into the main screen. Siply push
the button labeled "Show configuration".

There are three tabs. In the first one, you can assign actions to the offscreen
areas. In the second one, you can manage the wiimote devices. And in the third
one, you'll find some more options.


Calibration
-----------

The calibration process can be done in two ways:

- You can choose "fullscreen calibration": The application will change into a
  white fullscreen and will draw four crosses, that you have to mark clockwise.

- If you don't mark the "fullscreen" check in the configuration dialog, the
  calibration process is done in the same way, but you have to point at the
  four corners of the SCREEN, in the same order as before: top-left, top-right,
  bottom-left, bottom-right.

After that, you simply push "activate".

In the calibration screen, you can use the UP/DOWN keys to actually move
inwards the calibration points, making it easier to do the process.


Translations
------------

If you want to contribute with some translations, make sure you have the proper
tools installed on your system. In Ubuntu/Debian you'll need the following packages:

- qt4-dev-tools
- pyqt4-dev-tools

(and all its dependencies, of course).

Also, make sure that you have the latest version of the program (check it with git).

To update a translation, go to the trans/ directory and execute the following:

$ linguist pywhiteboard_whatever.ts

And supply the translations.

If you want to contribute a fresh, new translation for an unsupported language,
you first have to generate the .ts file (look at the "generate_trans.sh".

Have fun!


