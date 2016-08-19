#!/usr/bin/env python3
import os, sys, platform, subprocess, tempfile, shutil;

curdir = os.getcwd();
compression_program = "7za";
if sys.platform == "win32": compression_program = curdir+"/tools/7za-w32.exe";

def program_exist(program):
    import distutils.spawn;
    if not distutils.spawn.find_executable(program):
        print(os.linesep + "ERROR: Missing executable =>", program);
        return False;
    return True;

def select_device():
    subprocess.check_output(["adb", "start-server"]);
    devices = subprocess.check_output(["adb", "devices"]).decode("utf-8");
    if devices.count(os.linesep) <= 2:
        print(os.linesep + "ERROR: No device detected! Please connect your device first.");
        sys.exit(1);

    devices = devices.split(os.linesep)[1:-2];
    devices = [a.split("\t")[0] for a in devices];

    if len(devices) > 1:
        print("Enter id of device to target:" + os.linesep);
        id = input("\t" + (os.linesep + "\t").join([str(i)+" - "+a for i,a in zip(range(1, len(devices)+1), devices)]) + os.linesep + os.linesep + "> ");
        chosen_one = devices[int(id)-1];
    else:
        chosen_one = devices[0];
    return chosen_one;

def enable_device_writing(chosen_one):
    root_check = subprocess.check_output(["adb", "-s", chosen_one, "root"]).decode("utf-8");
    if root_check.find("root access is disabled") == 0:
        print(os.linesep + "ERROR: Root access is disabled." + os.linesep + "Enable it in Settings -> Developer options -> Root access -> Apps and ADB.");
        sys.exit(2);
    print("      DEBUG:", root_check.rstrip());
    subprocess.check_call(["adb", "-s", chosen_one, "wait-for-device"]);
    remount_check = subprocess.check_output(["adb", "-s", chosen_one, "remount", "/system"]).decode("utf-8"); print("      DEBUG:", remount_check.rstrip());
    if remount_check.find("remount failed") == 0 and ("Success" not in remount_check):  # Do NOT stop with "remount failed: Success"
        print(os.linesep + "ERROR: Remount failed.");
        sys.exit(3);

# Wait a key press before exit so the user can see the log also when the script is executed with a double click (on Windows)
def on_exit(): import msvcrt; msvcrt.getch();
if sys.platform == "win32": import atexit; atexit.register(on_exit);

if os.environ.get("RUN_TYPE") != "dumb":
    print("Where do you want to take the file to patch?" + os.linesep);
    mode = int(input("\t1 - From the device (adb)" + os.linesep + "\t2 - From the input folder" + os.linesep + os.linesep + "> "));
else:
    mode = 2;

# Check the existence of the needed components
if not program_exist("java") or not program_exist(compression_program): sys.exit(50);
if mode == 1:
    if not program_exist("adb"): sys.exit(51);
    # Select device
    chosen_one = select_device();

print(os.linesep + " *** OS:", platform.system(), platform.release(), "(" + sys.platform + ")");
if mode == 1: print(" *** Selected device:", chosen_one);

# Pull framework somewhere temporary
dirpath = tempfile.mkdtemp();
os.chdir(dirpath);
print(" *** Working dir: %s" % dirpath);

if mode == 1:
    print(" *** Rooting adbd...");
    enable_device_writing(chosen_one);

    print(" *** Pulling framework from device...");
    subprocess.check_output(["adb", "-s", chosen_one, "pull", "/system/framework/framework.jar", "."]);
else:
    shutil.copy2(curdir + "/input/framework.jar", dirpath + "/");

# Disassemble it
print(" *** Disassembling framework...");
subprocess.check_output([compression_program, "x", "-y", "-tzip", "-o./framework/", "./framework.jar", "*.dex"]);
print(" *** Disassembling classes...");
subprocess.check_call(["java", "-jar", curdir+"/tools/baksmali.jar", "-x", "-o./smali/", "framework/classes.dex"]);
###subprocess.check_call(["unzip", "-oq", "framework.jar", "classes.dex"]);

# Check the existence of the file to patch
to_patch = "./smali/android/content/pm/PackageParser.smali";
if not os.path.exists(to_patch):
    print(os.linesep + "ERROR: The disassembling has probably failed, this file is missing:", to_patch);
    sys.exit(4);

# Do the injection
print(" *** Patching...");
f = open(to_patch, "r");
old_contents = f.readlines();
f.close();

f = open(curdir+"/fillinsig.smali", "r");
fillinsig = f.readlines();
f.close();

# Add fillinsig method
i = 0;
contents = [];
already_patched = False;
in_function = False;
right_line = False;
start_of_line = None;
done_patching = False;
stored_register = "v11";
partially_patched = False;

while i < len(old_contents):
    if ";->fillinsig" in old_contents[i]:
        already_patched = True;
    if ".method public static fillinsig" in old_contents[i]:
        partially_patched = True;
    if ".method public static generatePackageInfo(Landroid/content/pm/PackageParser$Package;[IIJJLjava/util/Set;Landroid/content/pm/PackageUserState;I)Landroid/content/pm/PackageInfo;" in old_contents[i]:
        in_function = True;
    if ".method public static generatePackageInfo(Landroid/content/pm/PackageParser$Package;[IIJJLandroid/util/ArraySet;Landroid/content/pm/PackageUserState;I)Landroid/content/pm/PackageInfo;" in old_contents[i]:
        in_function = True;
    if ".method public static generatePackageInfo(Landroid/content/pm/PackageParser$Package;[IIJJLjava/util/HashSet;Landroid/content/pm/PackageUserState;I)Landroid/content/pm/PackageInfo;" in old_contents[i]:
        in_function = True;
    if ".method public static generatePackageInfo(Landroid/content/pm/PackageParser$Package;[IIJJLjava/util/HashSet;ZII)Landroid/content/pm/PackageInfo;" in old_contents[i]:
        in_function = True;
    if ".end method" in old_contents[i]:
        in_function = False;
    if in_function and ".line" in old_contents[i]:
        start_of_line = i + 1;
    if in_function and "arraycopy" in old_contents[i]:
        right_line = True;
    if in_function and "Landroid/content/pm/PackageInfo;-><init>()V" in old_contents[i]:
        stored_register = old_contents[i].split("{")[1].split("}")[0];
    if not already_patched and in_function and right_line and not done_patching:
        contents = contents[:start_of_line];
        contents.append("move-object/from16 v0, p0\n");
        contents.append("invoke-static {%s, v0}, Landroid/content/pm/PackageParser;->fillinsig(Landroid/content/pm/PackageInfo;Landroid/content/pm/PackageParser$Package;)V\n" % stored_register);
        done_patching = True;
    else:
        contents.append(old_contents[i]);
    i = i + 1;

if not already_patched and not partially_patched:
    contents.extend(fillinsig);
elif partially_patched and not already_patched:
    print(" *** Previous failed patch attempt, not including the fillinsig method again...");
elif already_patched:
    print(" *** This framework.jar appears to have been already patched... Exiting.");
    sys.exit(0);

f = open(to_patch, "w");
contents = "".join(contents);
f.write(contents);
f.close();
print(" *** Patching succeeded.");

# Reassemble it
print(" *** Reassembling classes...");
subprocess.check_call(["java", "-jar", curdir+"/tools/smali.jar", "-oclasses.dex", "./smali/"]);
if sys.platform == "win32": subprocess.check_call(["attrib", "-a", "./classes.dex"]);

# Put classes.dex into framework.jar
print(" *** Reassembling framework...");
#subprocess.check_call(["zip", "-q9X", "framework.jar", "classes.dex"]);
subprocess.check_output([compression_program, "a", "-y", "-tzip", "./framework.jar", "./classes.dex"]);

if mode == 1:
    # Push to device
    print(" *** Pushing changes to the device...");
    subprocess.check_output(["adb", "-s", chosen_one, "push", "framework.jar", "/system/framework/framework.jar"]);

print(" *** All done! :)");

# Clean up
os.chdir(curdir);
#shutil.rmtree(dirpath);
