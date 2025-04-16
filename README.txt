You will need 2 databases for this script to work:
1. gallery.encrypteddb
	1a. (and key from the keystore, look for 'egocipher.key.avoidkeyderivation', add this in the script) 
2. scdb-27.sqlite3

Run the scripts in the following order:
1. decryptdb.py, this will generate a decrypted database -> gallery.decrypted.sqlite (this contains the iv and key for decryption of snaps)
2. parsegallerydb.py, this will parse the gallery database into a CSV
3. decryptfile.py, this pulls down snaps from snapchat and decrypts them (stores the SNAP_ID as filename)