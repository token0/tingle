# Tingle
[![Build Status](https://travis-ci.org/ale5000-git/tingle.svg?branch=master)](https://travis-ci.org/ale5000-git/tingle)

## What this does
This will allow you to patch the Android system and inject features without needing to recompile the OS or install Xposed.

Notably, it is made to inject support for signature spoofing into the system so it can spoof Android app signatures (useful for [microG](https://microg.org/)).

## Compatibility
Windows, Linux, macOS (OS X) and Android.  
It doesn't require root on the OS where you run it but it require root on the device you want to patch.

## How to use
1. Make sure you have Python, Java and ADB available.
2. Make sure `Developer options` is enabled. This is hidden by default since sometime in Android 4.x, you can show it by going to `About phone` and tapping on the `Build number` five times in succession.
3. In the developer settings, find the setting for `Android debugging` and enable it.
4. Find the setting for `Root access` and make sure ADB has root access.
5. Connect your device via USB.
6. Now, on the computer, run `python main.py` (or `python3 main.py`).
7. Select the option 1 to allow the patcher to do everything automatically.
8. Reboot the device.

You can run this patcher also when the device is in Android's recovery (provided /system is mounted).

You will need to reboot for Android to detect that you've installed a new framework and so for Dalvik/ART to re-optimise all the apps on the phone. Without this, you may receive an `INSTALL_FAILED_DEXOPT` error when installing new apps.

Note: You will need to redo this everytime you flash a new /system partition (e.g. flashing an updated CyanogenMod zip or a new ROM).
