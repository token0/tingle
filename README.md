# Framework Patcher for Android

## What this does
If you have a rooted phone, this will allow you to patch the android system and inject features without needing to recompile the OS or install Xposed.

Notably, it is made to inject a fake-signature patch into the system so it can spoof android app signatures.

## How to use
Make sure you have Python, Java and adb available, connect your device via usb and run `python patch.py` (or `python3 patch.py`).

You will then need to reboot for Android to detect that you've installed a new framework and so for Dalvik/ART to re-optimise all the apps on the phone. Without this, you may receive an `INSTALL_FAILED_DEXOPT` error when installing new apps.

You should now have a system patched to accept spoofed app signatures (Useful for [microG](https://github.com/microg/android_packages_apps_GmsCore)).

Note: You will need to redo this everytime you flash a new /system partition (e.g. flashing an updated cyanogenmod zip or new ROM).
