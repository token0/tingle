#!/usr/bin/env python
"""Tingle - file patcher for Android."""

import sys;
import os;
import subprocess;
import tempfile;
import shutil;

__author__ = 'ale5000, moosd';

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__));
PREVIOUS_DIR = os.getcwd();
DUMB_MODE = False;
compression_program = "7za";

if os.environ.get("TERM") == "dumb":
    DUMB_MODE = True;
if sys.platform == "win32":
    compression_program = "7za-w32";


def init():
    sys.path.insert(1, SCRIPT_DIR+os.sep+"libs");
    import atexit;
    import compatlayer;

    # Activate Python compatibility layer
    compatlayer.fix_all();
    # Add tools folder to search path (used from subprocess), take precedence over system folders
    os.environ["PATH"] = SCRIPT_DIR+os.sep+"tools" + os.pathsep + os.environ.get("PATH", "");
    # Register exit handler
    atexit.register(on_exit);


def on_exit():
    # Return to the previous working directory
    os.chdir(PREVIOUS_DIR);
    # Clean up
    #shutil.rmtree(dirpath);
    if sys.platform == "win32" and not DUMB_MODE:
        import msvcrt;
        msvcrt.getch();  # Wait a keypress before exit (useful when the script is running from a double click)


def exit(error_code):
    if error_code != 0:
        print_(os.linesep+"ERROR CODE:", error_code);
    sys.exit(error_code);


def verify_dependencies(mode):
    from distutils.spawn import find_executable;

    def exec_exists(exec_name):
        if find_executable(exec_name) is not None:
            return True;
        print_(os.linesep+"ERROR: Missing executable =>", exec_name);
        return False;

    if not exec_exists("java") or not exec_exists(compression_program):
        exit(65);
    if mode == 1 and not exec_exists("adb"):
        exit(66);


def remove_ext(filename):
    return filename.rsplit(".", 1)[0];


def debug(msg):
    print_("      DEBUG:", msg);


def warning(msg, first_line=True):
    if first_line:
        print_("      WARNING:", msg);
    else:
        print_("              ", msg);


def get_OS():
    import platform;
    return platform.system()+" "+platform.release();


def input_byte(msg):
    print_(msg, end="");
    if DUMB_MODE:
        print_();
        return "";
    try:
        val = sys.stdin.readline();
        # KeyboardInterrupt leave a "", instead an empty value leave a "\n"
        if val == "":
            import time;
            time.sleep(0.02);  # Give some time for the exception to being caught
    except KeyboardInterrupt:
        raise EOFError;
    else:
        return val.strip()[:1];


def user_question(msg, max_val, default_val=1):
    try:
        val = input_byte(msg+os.linesep+"> ");
    except EOFError:
        print_(os.linesep+os.linesep+"Killed by the user, now exiting ;)");
        sys.exit(130);

    if(val == ""):
        print_("Used default value.");
        return default_val;

    try:
        val = int(val);
        if val > 0 and val <= max_val:
            return val;
    except ValueError:
        pass;

    return user_question("Invalid value, try again...", max_val, default_val);


def select_device():
    subprocess.check_output(["adb", "start-server"]);
    devices = subprocess.check_output(["adb", "devices"]).decode("utf-8");
    if devices.count(os.linesep) <= 2:
        print_(os.linesep+"ERROR: No device detected! Please connect your device first.");
        exit(0);

    devices = devices.split(os.linesep)[1:-2];
    devices = [a.split("\t")[0] for a in devices];

    if len(devices) > 1:
        print_("Enter id of device to target:"+os.linesep);
        id = user_question("\t"+(os.linesep+"\t").join([str(i)+" - "+a for i, a in zip(range(1, len(devices)+1), devices)])+os.linesep, len(devices));
        chosen_one = devices[id-1];
    else:
        chosen_one = devices[0];
    return chosen_one;


def enable_device_writing(chosen_one):
    root_check = subprocess.check_output(["adb", "-s", chosen_one, "root"]).decode("utf-8");
    if root_check.find("root access is disabled") == 0 or root_check.find("adbd cannot run as root") == 0:
        print_(os.linesep+"ERROR: You do NOT have root or root access is disabled.");
        print_(os.linesep+"Enable it in Settings -> Developer options -> Root access -> Apps and ADB.");
        exit(80);
    debug(root_check.rstrip());
    subprocess.check_call(["adb", "-s", chosen_one, "wait-for-device"]);
    remount_check = subprocess.check_output(["adb", "-s", chosen_one, "remount", "/system"]).decode("utf-8");
    debug(remount_check.rstrip());
    if("remount failed" in remount_check) and ("Success" not in remount_check):  # Do NOT stop with "remount failed: Success"
        print_(os.linesep+"ERROR: Remount failed.");
        exit(81);


def brew_input_file(mode, chosen_one):
    if mode == 1:
        # Pull framework somewhere temporary
        print_(" *** Pulling framework from device...");
        subprocess.check_call(["adb", "-s", chosen_one, "pull", "/system/framework/framework.jar", "."]);
    elif mode == 2:
        shutil.copy2(SCRIPT_DIR+"/input/framework.jar", dirpath+"/");
    else:
        shutil.copy2("/system/framework/framework.jar", dirpath+"/");


def disassemble(file, out_dir):
    debug("Disassembling "+file);
    subprocess.check_call(["java", "-jar", SCRIPT_DIR+"/tools/baksmali.jar", "-lsx", "-o"+out_dir, file]);
    return True;


def assemble(in_dir, file, hide_output=False):
    debug("Assembling "+file);
    if hide_output:
        return subprocess.check_output(["java", "-jar", SCRIPT_DIR+"/tools/smali.jar", "-o"+file, in_dir], stderr=subprocess.STDOUT);
    subprocess.check_call(["java", "-jar", SCRIPT_DIR+"/tools/smali.jar", "-o"+file, in_dir]);
    return True;


def find_smali(smali_to_search, dir):
    dir_list = tuple(sorted(os.listdir(dir)));
    for filename in dir_list:
        out_dir = "./smali-"+remove_ext(filename)+"/";
        disassemble(dir+filename, out_dir);
        if os.path.exists(out_dir+smali_to_search):
            return (out_dir, filename, dir_list[-1]);
    return (None, None, None);


init();
print_("Where do you want to take the file to patch?" + os.linesep);
mode = user_question("\t1 - From a device (adb)"+os.linesep + "\t2 - From the input folder"+os.linesep, 3, 2);

# Check the presence of the needed components
verify_dependencies(mode);

# Select device
chosen_one = None;
if mode == 1:
    chosen_one = select_device();

print_(os.linesep+" *** OS:", get_OS(), "("+sys.platform+")");
print_(" *** Mode:", mode);
dirpath = tempfile.mkdtemp();
os.chdir(dirpath);
print_(" *** Working dir: %s" % dirpath);

if mode == 1:
    print_(" *** Selected device:", chosen_one);

if DUMB_MODE:
    exit(0);  # ToDO: Implement full test in dumb mode

brew_input_file(mode, chosen_one);

# Disassemble it
print_(" *** Disassembling framework...");
subprocess.check_output([compression_program, "x", "-y", "-tzip", "-o./framework/", "./framework.jar", "*.dex"]);

if not os.path.exists("framework/"):
    print_(os.linesep+"ERROR: No dex file(s) found, probably the ROM is odexed.");
    exit(86);

print_(" *** Disassembling classes...");
smali_to_search = "android/content/pm/PackageParser.smali";
smali_folder, dex_filename, dex_filename_last = find_smali(smali_to_search, "framework/");

# Check the existence of the file to patch
if smali_folder is None:
    print_(os.linesep+"ERROR: The file to patch cannot be found, please report the problem.");
    exit(82);
to_patch = smali_folder+smali_to_search;

# Do the injection
print_(" *** Patching...");
f = open(to_patch, "r");
old_contents = f.readlines();
f.close();

f = open(SCRIPT_DIR+"/patches/fillinsig.smali", "r");
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
    print_(" *** Previous failed patch attempt, not including the fillinsig method again...");
elif already_patched:
    print_(" *** This framework.jar appears to have been already patched... Exiting.");
    exit(0);

f = open(to_patch, "w");
contents = "".join(contents);
f.write(contents);
f.close();
print_(" *** Patching succeeded.");

# Reassemble it
print_(" *** Reassembling classes...");

def safe_move(orig, dest):
    if not os.path.exists(orig) or os.path.exists(dest.rstrip("/")):
        print_(os.linesep+"ERROR: Safe move fail.");  # ToDO: Notify error better
        exit(85);
    shutil.move(orig, dest);

def move_methods_workaround(dex_filename, dex_filename_last, in_dir, out_dir):
    if(dex_filename == dex_filename_last):
        print_(os.linesep+"ERROR");  # ToDO: Notify error better
        exit(84);
    print_(" *** Moving methods...");
    warning("Experimental code.");
    smali_dir = "./smali-"+remove_ext(dex_filename)+"/";
    smali_dir_last = "./smali-"+remove_ext(dex_filename_last)+"/";
    disassemble(in_dir+dex_filename_last, smali_dir_last);
    safe_move(smali_dir+"android/drm/", smali_dir_last+"android/drm/");
    print_(" *** Reassembling classes...");
    assemble(smali_dir, out_dir+dex_filename);
    assemble(smali_dir_last, out_dir+dex_filename_last);
    if sys.platform == "win32":
        subprocess.check_call(["attrib", "-a", out_dir+dex_filename]);
        subprocess.check_call(["attrib", "-a", out_dir+dex_filename_last]);

os.makedirs("out/");
try:
    assemble(smali_folder, "out/"+dex_filename, True);
    if sys.platform == "win32":
        subprocess.check_call(["attrib", "-a", "out/"+dex_filename]);
except subprocess.CalledProcessError as e:  # ToDO: Check e.cmd
    os.remove(dirpath+"/out/"+dex_filename);  # Remove incomplete file
    if e.returncode != 2:
        print_(os.linesep+e.output.decode("utf-8").strip());
        exit(83);
    warning("The reassembling has failed (probably we have exceeded the 64K methods limit)");
    warning("but do NOT worry, we will retry.", False);
    move_methods_workaround(dex_filename, dex_filename_last, "framework/", "out/");

# Backup the original file
shutil.copy2(dirpath+"/framework.jar", SCRIPT_DIR+"/output/framework.jar.original");

# Put classes back in the archive
print_(" *** Reassembling framework...");
#subprocess.check_call(["zip", "-q9X", "framework.jar", os.curdir+"/out/*.dex"]);
subprocess.check_output([compression_program, "a", "-y", "-tzip", "framework.jar", os.curdir+"/out/*.dex"]);

# Copy the patched file to the output folder
shutil.copy2(dirpath+"/framework.jar", SCRIPT_DIR+"/output/framework.jar");

if mode == 1:
    print_(" *** Rooting adbd...");
    enable_device_writing(chosen_one);
    # Push to device
    print_(" *** Pushing changes to the device...");
    subprocess.check_call(["adb", "-s", chosen_one, "push", "framework.jar", "/system/framework/framework.jar"]);
    # Kill ADB server
    subprocess.check_call(["adb", "kill-server"]);

print_(" *** All done! :)");
