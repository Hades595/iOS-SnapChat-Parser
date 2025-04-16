import hmac
import hashlib
import time
import os
import csv
import sqlite3
import wget
import glob
from Crypto.Cipher import AES
from string import Template

def convert_to_bytes(input):
    if type(input) == str:
        return bytes.fromhex(input.strip())
    elif type(input) == bytes:
        return input
    else:
        raise Exception("Input type unrecognised")

decryptedfilesfolder = r'decryptedfiles'

conn = sqlite3.connect("scdb-27.sqlite3")
cur = conn.cursor()
sql = open("scdbquery.sql", "r").read()

with open(r"output.csv", "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    headers = next(reader)
    for row in reader:
        try:
            snap_id = row[0]

            testpath = "decryptedfiles\\" + snap_id + ".*"
            if glob.glob(testpath):
                continue

            query = Template(sql).substitute(SNAPID=snap_id)
            cur.execute(query)
            output = cur.fetchall()
            if(len(output) == 0): #Empty so useless
                continue

            #Download the file
            url = output[0][2]
            file = wget.download(url, out=decryptedfilesfolder)
            file_format = output[0][3]

            #Decrypt the file
            key = convert_to_bytes(row[4])
            iv = convert_to_bytes(row[5])

            #Add extention
            if (file_format == 'image_jpeg'):
                path = row[0] + ".jpeg"
            elif (file_format == 'video_hevc' or file_format == 'video_avc' ):
                path = row[0] + ".mp4"

            with open(file, 'rb') as f:
                temp = f.read()

            with open(os.path.join(decryptedfilesfolder, path), 'wb') as f:
                f.write(AES.new(key[:32], AES.MODE_CBC, iv).decrypt(temp))

            os.remove(file)
        except:
            print("Failed getting file: " + row[0])
            pass

