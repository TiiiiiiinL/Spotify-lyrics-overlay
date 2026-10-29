"""Creates app.ico for the .exe build. Run once on Windows:  python make_icon.py

Want your OWN icon? Put an image file named `custom_icon.png` in this
folder (preferably square, e.g. 256x256). It will be used instead of the
default icon. Delete the file to go back to the default.
"""

import os
import sys

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication

from appicon import render_pixmap

CUSTOM_IMAGE = "custom_icon.png"


def main():
    QApplication(sys.argv)  # required to draw/load images

    if os.path.exists(CUSTOM_IMAGE):
        pixmap = QPixmap(CUSTOM_IMAGE)
        if pixmap.isNull():
            print(f"Could not read {CUSTOM_IMAGE} – using the default icon.")
            pixmap = render_pixmap(256)
        else:
            print(f"Using your own image: {CUSTOM_IMAGE}")
    else:
        pixmap = render_pixmap(256)

    if pixmap.save("app.ico", "ICO"):
        print("Created app.ico")
        return 0
    print("Could not create app.ico (the build still works, just without a custom icon).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
