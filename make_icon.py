"""Skapar app.ico till .exe-bygget. Kör en gång på Windows:  python make_icon.py

Vill du ha en EGEN ikon? Lägg en bildfil som heter `custom_icon.png` i den här
mappen (helst kvadratisk, t.ex. 256x256). Då används den istället för
standardikonen. Ta bort filen för att gå tillbaka till standard.
"""

import os
import sys

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication

from appicon import render_pixmap

CUSTOM_IMAGE = "custom_icon.png"


def main():
    QApplication(sys.argv)  # krävs för att kunna rita/ladda bilder

    if os.path.exists(CUSTOM_IMAGE):
        pixmap = QPixmap(CUSTOM_IMAGE)
        if pixmap.isNull():
            print(f"Kunde inte läsa {CUSTOM_IMAGE} – använder standardikonen.")
            pixmap = render_pixmap(256)
        else:
            print(f"Använder din egen bild: {CUSTOM_IMAGE}")
    else:
        pixmap = render_pixmap(256)

    if pixmap.save("app.ico", "ICO"):
        print("Skapade app.ico")
        return 0
    print("Kunde inte skapa app.ico (bygget funkar ändå, men utan egen ikon).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
