# libraries Import
from tkinter import *
import customtkinter
from tkinter import filedialog
import plistlib
import os
import subprocess
import sqlite3
import csv
import wget
import glob
from string import Template
from Crypto.Cipher import AES

# Main Window Properties

window = Tk()
window.title("iOSSnapchatParser")
window.geometry("500x350")
window.configure(bg="#FFFFFF")

check_download = customtkinter.StringVar(value="on")
SQLITE_FILE_HEADER = "SQLite format 3\x00"
DEFAULT_PAGESIZE = 1024
KEY_SIZE = 32
SALT_SIZE = 16


def read_file(path, type="bytes"):
    """
    Read file at path, specify read type <'bytes'> or <'text'>
    """
    mode = {"bytes": "rb", "text": "r"}
    try:
        with open(path, mode[type]) as f:
            file = f.read()
    except Exception as e:
        print(f"Failed to open file : {path}")
        print(f"Error raised : {e}")
    return file


def convert_to_bytes(input):
    if type(input) == str:
        return bytes.fromhex(input.strip())
    elif type(input) == bytes:
        return input
    else:
        raise Exception("Input type unrecognised")


def decrypt_file(db_path, out_path):
    blist = read_file(db_path)
    with open(out_path, "wb") as f:
        f.write(SQLITE_FILE_HEADER.encode())
        for i in range(0, len(blist), DEFAULT_PAGESIZE):
            tblist = (
                blist[i : i + DEFAULT_PAGESIZE]
                if i > 0
                else blist[SALT_SIZE : i + DEFAULT_PAGESIZE]
            )
            f.write(
                AES.new(key[:32], AES.MODE_CBC, tblist[-48:-32]).decrypt(tblist[:-48])
            )
            f.write(b"\x00" * 48)


def button_select_GUID():
    global GUID_folder_path
    GUID_folder_path = filedialog.askdirectory()
    Entry_id2.configure(placeholder_text=os.path.basename(GUID_folder_path))


def button_select_keychain():
    global keychain_plist
    keychain_plist = filedialog.askopenfilename()
    Entry_id4.configure(placeholder_text=os.path.basename(keychain_plist))


def button_select_OutputDir():
    global Output_folder_path
    Output_folder_path = filedialog.askdirectory()
    Entry_id10.configure(placeholder_text=os.path.basename(Output_folder_path))


def Process_Keychain(file_name):
    print("Processing keychain....")
    try:
        with open(file_name, "rb") as infile:
            plist = plistlib.load(infile)
        for i in plist["genp"]:
            try:
                if i["gena"].decode("ASCII") == "egocipher.key.avoidkeyderivation":
                    return i["v_Data"].hex()
            except:
                continue
    except:
        print("Exception Occured")


def convert_to_wsl_path(windows_path):
    # Extract the drive letter and the rest of the path
    drive_letter = windows_path.split(":")[0].lower()
    wsl_path = windows_path.replace("\\", "/")
    wsl_path = wsl_path.replace(f"{drive_letter.upper()}:", f"/mnt/{drive_letter}")
    return wsl_path


def Decrypt_gallery(gallery_db, output_dir):
    # Decrypt DB
    output = os.path.join(output_dir, "gallery.decrypted.sqlite")
    decrypt_file(gallery_db, output)
    # sqlite3 gallery.decrypted.sqlite ".recover" | sqlite3 recovered.db
    wsl_db_path = convert_to_wsl_path(output)
    command = (
        'wsl sqlite3 "'
        + wsl_db_path
        + '" ".recover" | wsl sqlite3 "'
        + os.path.split(wsl_db_path)[0]
        + "/recovered.db"
        + '"'
    )
    print(subprocess.check_call(["powershell", command]))


def Parsing_SCDB(scdb_path, output_dir):
    conn = sqlite3.connect(scdb_path)
    cur = conn.cursor()
    sql = """SELECT ZGALLERYSNAP.ZCAPTURETIMEUTC,ZGALLERYSNAP.ZDURATION,ZGALLERYSNAP.ZMEDIADOWNLOADURL,ZGALLERYSNAP.ZSERVLETMEDIAFORMAT FROM ZGALLERYSNAP WHERE ZMEDIAID = '$SNAPID'"""
    output_csv_path = os.path.join(output_dir, "output.csv")
    updated_csv_path = os.path.join(output_dir, "SnapChat Data.csv")

    with open(output_csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)

        headers.extend(["Capture Time", "Duration", "URL", "Format"])

        with open(updated_csv_path, "w", encoding="utf-8", newline="") as new_f:
            writer = csv.writer(new_f)
            writer.writerow(headers)
            for row in reader:
                try:
                    snap_id = row[0]

                    query = Template(sql).substitute(SNAPID=snap_id)
                    cur.execute(query)
                    output = cur.fetchall()

                    if len(output) == 0:  # Empty so useless
                        continue

                    capture_time = output[0][0]
                    duration = output[0][1]
                    url = output[0][2]
                    file_format = output[0][3]
                    row.extend([capture_time, duration, url, file_format])
                    writer.writerow(row)

                except:
                    print("Failed getting file: " + row[0])
                    pass

    os.remove(output_csv_path)


def convert_to_str(key):
    return "".join(format(byte, "02x") for byte in key)


def convert_to_bytes(input):
    if type(input) == str:
        return bytes.fromhex(input.strip())
    elif type(input) == bytes:
        return input
    else:
        raise Exception("Input type unrecognised")


def Generate_CSV(output_dir):
    conn = sqlite3.connect(os.path.join(output_dir, "recovered.db"))
    cur = conn.cursor()

    qry = """SELECT
	snap_key_iv.snap_id AS 'SNAP ID',
	snap_address_title.address_title AS 'Region',
	snap_location_table.latitude AS 'Latitude',
	snap_location_table.longitude AS 'Longitude',
	snap_key_iv.key AS 'Key',
	snap_key_iv.iv AS 'IV'
    FROM 
        snap_key_iv
    LEFT JOIN
        snap_location_table ON snap_key_iv.snap_id = snap_location_table.snap_id
    LEFT JOIN
        snap_address_title ON snap_address_title.snap_id = snap_key_iv.snap_id"""

    cur.execute(qry)

    output = cur.fetchall()

    with open(os.path.join(output_dir, "output.csv"), "w", encoding="utf-8") as f:
        f.write("SNAP_ID,Region,Latitude,Longitude,Key,IV\n")
        for row in output:
            snap_id = row[0]
            region = '"' + row[1] + '"' if row[1] else ""
            lat = str(row[2]) if row[2] else ""
            lon = str(row[3]) if row[3] else ""
            key = convert_to_str(row[4]) if row[4] else ""
            iv = convert_to_str(row[5]) if row[5] else ""
            string_row = ",".join([snap_id, region, lat, lon, key, iv]) + "\n"

            try:
                f.write(string_row)
            except:

                print(string_row)

    conn.commit()
    conn.close()


def Download_Snaps(output_dir):
    # Create Folder
    new_folder = output_dir + r"/Downloaded Snaps"
    os.makedirs(new_folder)

    csv_path = os.path.join(output_dir, "SnapChat Data.csv")

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)

        for row in reader:
            try:
                snap_id = row[0]
                url = row[8]
                file_format = row[9]
                key = convert_to_bytes(row[4])
                iv = convert_to_bytes(row[5])

                testpath = new_folder + "\\" + snap_id + ".*"
                if glob.glob(testpath):
                    continue

                file = wget.download(url, out=new_folder)

                # Add extention
                if file_format == "image_jpeg":
                    path = row[0] + ".jpeg"
                elif file_format == "video_hevc" or file_format == "video_avc":
                    path = row[0] + ".mp4"

                with open(file, "rb") as f:
                    temp = f.read()

                with open(os.path.join(new_folder, path), "wb") as f:
                    f.write(AES.new(key[:32], AES.MODE_CBC, iv).decrypt(temp))

                os.remove(file)

            except:
                print("Failed getting file: " + row[0])
                pass



def button_select_Process():
    try:
        if GUID_folder_path == "":
            print("Error!")
        elif keychain_plist == "":
            print("Error!")
        elif Output_folder_path == "":
            print("Error!")

        # Process Key chain - Get egocipher key
        global key
        key = convert_to_bytes(Process_Keychain(keychain_plist))

        # Decrypt Gallery Database - Documents/gallery_encrypted_db/<digit>/<uid>/gallery.encrypteddb
        gallery_path = GUID_folder_path + r"//Documents//gallery_encrypted_db//"
        for folder, sub, files in os.walk(gallery_path):
            for file in files:
                if file == "gallery.encrypteddb":
                    gallery_path = os.path.join(folder, file)
                    Decrypt_gallery(gallery_path, Output_folder_path)
                    # Generate CSV
                    Generate_CSV(Output_folder_path)
                    print("Completed Generation of CSV")

        # Parse SCDB - Documents/gallery_data_object/<digit>/<uid>/scdb-27.sqlite3
        scdb_path = GUID_folder_path + r"//Documents//gallery_data_object//"
        for folder, sub, files in os.walk(scdb_path):
            for file in files:
                if file == "scdb-27.sqlite3":
                    scdb_path = os.path.join(folder, file)
                    Parsing_SCDB(scdb_path, Output_folder_path)
                    print("completed parsing")

        # Download Snaps
        if check_download.get() == "on":
            Download_Snaps(Output_folder_path)

    except Exception as e:
        print(e)


Checkbox_id11 = customtkinter.CTkCheckBox(
    master=window,
    text="Download Snaps",
    text_color="#000000",
    border_color="#000000",
    fg_color="#808080",
    hover_color="#808080",
    corner_radius=4,
    border_width=2,
    variable=check_download,
    onvalue="on",
    offvalue="off",
)
Checkbox_id11.place(x=30, y=260)
Button_id1 = customtkinter.CTkButton(
    master=window,
    text="Browse",
    font=("undefined", 14),
    text_color="#000000",
    hover=True,
    hover_color="#949494",
    height=30,
    width=95,
    border_width=2,
    corner_radius=6,
    border_color="#000000",
    bg_color="#FFFFFF",
    fg_color="#F0F0F0",
    command=button_select_GUID,
)
Button_id1.place(x=380, y=50)
Label_id9 = customtkinter.CTkLabel(
    master=window,
    text="Output Directory:",
    font=("Arial", 14),
    text_color="#000000",
    height=30,
    width=95,
    corner_radius=0,
    bg_color="#FFFFFF",
    fg_color="#FFFFFF",
)
Label_id9.place(x=30, y=170)
Button_id3 = customtkinter.CTkButton(
    master=window,
    text="Browse",
    font=("undefined", 14),
    text_color="#000000",
    hover=True,
    hover_color="#949494",
    height=30,
    width=95,
    border_width=2,
    corner_radius=6,
    border_color="#000000",
    bg_color="#FFFFFF",
    fg_color="#F0F0F0",
    command=button_select_keychain,
)
Button_id3.place(x=380, y=130)
Label_id5 = customtkinter.CTkLabel(
    master=window,
    text="Path to Snapchat Folder",
    font=("Arial", 14),
    text_color="#000000",
    height=30,
    width=95,
    corner_radius=0,
    bg_color="#FFFFFF",
    fg_color="#FFFFFF",
)
Label_id5.place(x=30, y=10)
Entry_id10 = customtkinter.CTkEntry(
    master=window,
    placeholder_text="Output",
    placeholder_text_color="#454545",
    font=("Arial", 14),
    text_color="#000000",
    height=30,
    width=320,
    border_width=2,
    corner_radius=6,
    border_color="#000000",
    bg_color="#FFFFFF",
    fg_color="#F0F0F0",
)
Entry_id10.place(x=30, y=210)
Button_id7 = customtkinter.CTkButton(
    master=window,
    text="Process",
    font=("undefined", 14),
    text_color="#000000",
    hover=True,
    hover_color="#949494",
    height=30,
    width=95,
    border_width=2,
    corner_radius=6,
    border_color="#000000",
    bg_color="#FFFFFF",
    fg_color="#F0F0F0",
    command=button_select_Process,
)
Button_id7.place(x=380, y=260)
Entry_id2 = customtkinter.CTkEntry(
    master=window,
    placeholder_text="XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
    placeholder_text_color="#454545",
    font=("Arial", 14),
    text_color="#000000",
    height=30,
    width=320,
    border_width=2,
    corner_radius=6,
    border_color="#000000",
    bg_color="#FFFFFF",
    fg_color="#F0F0F0",
)
Entry_id2.place(x=30, y=50)
Entry_id4 = customtkinter.CTkEntry(
    master=window,
    placeholder_text="keychain.plist",
    placeholder_text_color="#454545",
    font=("Arial", 14),
    text_color="#000000",
    height=30,
    width=320,
    border_width=2,
    corner_radius=6,
    border_color="#000000",
    bg_color="#FFFFFF",
    fg_color="#F0F0F0",
)
Entry_id4.place(x=30, y=130)
Button_id8 = customtkinter.CTkButton(
    master=window,
    text="Browse",
    font=("undefined", 14),
    text_color="#000000",
    hover=True,
    hover_color="#949494",
    height=30,
    width=95,
    border_width=2,
    corner_radius=6,
    border_color="#000000",
    bg_color="#FFFFFF",
    fg_color="#F0F0F0",
    command=button_select_OutputDir,
)
Button_id8.place(x=380, y=210)
Label_id6 = customtkinter.CTkLabel(
    master=window,
    text="Keychain (.plist)",
    font=("Arial", 14),
    text_color="#000000",
    height=30,
    width=95,
    corner_radius=0,
    bg_color="#FFFFFF",
    fg_color="#FFFFFF",
)
Label_id6.place(x=30, y=90)

# run the main loop
window.mainloop()
