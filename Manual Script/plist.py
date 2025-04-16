import plistlib

file_name = r"keychain.plist"
with open(file_name, "rb") as infile:
    plist = plistlib.load(infile)
for i in plist["genp"]:
    try:
        if i["gena"].decode('ASCII') == "egocipher.key.avoidkeyderivation":
            print(i['v_Data'].hex())
    except:
        continue