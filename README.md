# Tingle - File patcher for Android
[![Build Status](https://travis-ci.org/ale5000-git/tingle.svg?branch=master)](https://travis-ci.org/ale5000-git/tingle)

## What this does
This will allow you to patch the Android system and inject features without needing to recompile the OS or install Xposed.

Notably, it is made to inject a fake-signature patch into the system so it can spoof android app signatures.

## Compatibility
Windows, Linux, macOS (OS X) and Android.  
It doesn't require root on the OS where you run it but it require root on the device you want to patch.

## How to use
Make sure you have Python, Java and adb available, connect your device via usb. In the phone settings, find the setting for 'Android debugging' and enable it, and find the setting for 'Root Access' and make sure ADB has root access. Now, on the computer, run `python main.py` (or `python3 main.py`).

You will then need to reboot for Android to detect that you've installed a new framework and so for Dalvik/ART to re-optimise all the apps on the phone. Without this, you may receive an `INSTALL_FAILED_DEXOPT` error when installing new apps.

You should now have a system patched to accept spoofed app signatures (Useful for [microG](https://github.com/microg/android_packages_apps_GmsCore)).

Note: You will need to redo this everytime you flash a new /system partition (e.g. flashing an updated cyanogenmod zip or new ROM).
