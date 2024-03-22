#! /usr/bin/env python3

import subprocess
import traceback
from typing import Optional
import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

from icc_brightness import icc_brightness
from icc_brightness import clean

current_brightness: Optional[int] = None
max_brightness: Optional[int] = None


def update_brightness():
    global current_brightness
    global max_brightness

    try:
        if max_brightness is not None and current_brightness is not None:
            icc_brightness(current_brightness, max_brightness)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        GLib.idle_add(update_brightness)


def change_signal_handler(*args, **kwargs):
    global current_brightness
    global max_brightness
    match kwargs["member"]:
        case "brightnessChanged":
            current_brightness = int(args[0])
            update_brightness()
        case "brightnessMaxChanged":
            if max_brightness is None:
                max_brightness = int(args[0])
                update_brightness()
            else:
                max_brightness = int(args[0])


if __name__ == "__main__":
    DBusGMainLoop(set_as_default=True)
    sb = dbus.SessionBus()

    current_brightness: Optional[int] = None
    max_brightness: Optional[int] = None
    base_interface = "org.kde.Solid.PowerManagement.Actions.BrightnessControl"
    sb.add_signal_receiver(
        change_signal_handler,
        dbus_interface=base_interface,
        interface_keyword="dbus_interface",
        member_keyword="member",
    )

    clean()

    loop = GLib.MainLoop()
    loop.run()
