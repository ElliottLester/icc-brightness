#! /usr/bin/env python3

import subprocess
import json
import os
from typing import Optional
import typing_extensions
import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

brightness: Optional[int] = None
max_brightness: Optional[int] = None
output: Optional[str] = None

CWD = os.path.dirname(__file__)
ICC_BRIGHTNESS_GEN = os.path.join(CWD, "icc-brightness-gen")
TEMP_FOLDER = "/tmp"
BACKLIGHT_PATH = "/sys/class/backlight/intel_backlight"
BRIGHTNESS_PATH = os.path.join(BACKLIGHT_PATH, "brightness")
MAX_BRIGHTNESS_PATH = os.path.join(BACKLIGHT_PATH, "max_brightness")
KSCREENDOC = "/usr/bin/kscreen-doctor"


def update_brightness():
    global brightness
    global max_brightness

    try:
        if max_brightness is not None and brightness is not None:
            icc_filename = "brightness_%d_%d.icc" % (brightness, max_brightness)
            icc_filepath = os.path.join(TEMP_FOLDER, icc_filename)
            subprocess.run(
                [
                    ICC_BRIGHTNESS_GEN,
                    icc_filepath,
                    str(brightness),
                    str(max_brightness),
                ],
                check=True,
            )
            subprocess.run(
                [KSCREENDOC, "output.{}.iccprofile.{}".format(output, icc_filepath)]
            )
            # icc_brightness(current_brightness, max_brightness)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        GLib.idle_add(update_brightness)


def change_signal_handler(*args, **kwargs):
    global brightness
    global max_brightness
    match kwargs["member"]:
        case "brightnessChanged":
            brightness = int(args[0])
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

    with open(BRIGHTNESS_PATH) as infile:
        brightness: Optional[int] = int(infile.readline())
    with open(MAX_BRIGHTNESS_PATH) as infile:
        max_brightness: Optional[int] = int(infile.readline())

    outputs = json.loads(subprocess.run([KSCREENDOC, "-j"], capture_output=True).stdout)

    output = outputs["outputs"][0]["name"]

    base_interface = "org.kde.Solid.PowerManagement.Actions.BrightnessControl"
    sb.add_signal_receiver(
        change_signal_handler,
        dbus_interface=base_interface,
        interface_keyword="dbus_interface",
        member_keyword="member",
    )

    loop = GLib.MainLoop()
    loop.run()
