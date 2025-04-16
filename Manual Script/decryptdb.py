import hashlib
import sqlite3
import os
from Crypto.Cipher import AES

SQLITE_FILE_HEADER = "SQLite format 3\x00" 
DEFAULT_PAGESIZE = 1024
KEY_SIZE = 32
SALT_SIZE = 16

key = '' #Enter your egocipher.key.avoidkeyderivation key here (value)

def read_file(path, type='bytes'):
    '''
    Read file at path, specify read type <'bytes'> or <'text'>
    '''
    mode = {'bytes' : 'rb', 'text' : 'r'}
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
        raise Exception('Input type unrecognised')

def decrypt_file(key, db_path, out_path):
    blist = read_file(db_path)
    salt = blist[:SALT_SIZE]
    with open(out_path, 'wb') as f:
        f.write(SQLITE_FILE_HEADER.encode())
        for i in range(0, len(blist), DEFAULT_PAGESIZE):
            tblist = blist[i:i + DEFAULT_PAGESIZE] if i > 0 else blist[SALT_SIZE:i + DEFAULT_PAGESIZE]
            f.write(AES.new(key[:32], AES.MODE_CBC, tblist[-48:-32]).decrypt(tblist[:-48]))
            f.write(b'\x00'*48)


key = convert_to_bytes(key)
decrypt_file(key, r'gallery.encrypteddb', r"gallery.decrypted.sqlite")

# sqlite3 gallery.decrypted.sqlite ".recover" | sqlite3 recovered.db