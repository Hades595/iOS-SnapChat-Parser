import sqlite3

# https://xperylab.medium.com/decrypting-and-extracting-juicy-data-snap-17301aa57a87 

conn = sqlite3.connect('recovered.db')
cur = conn.cursor()

qry = open('gallerydbquery.sql', 'r').read()
cur.execute(qry)

output = cur.fetchall()

def convert_to_str(key):
    return ''.join(format(byte, '02x') for byte in key)

def convert_to_bytes(input):
    if type(input) == str:
        return bytes.fromhex(input.strip())
    elif type(input) == bytes:
        return input
    else:
        raise Exception('Input type unrecognised')

with open('output.csv', 'w', encoding="utf-8") as f: 
    f.write("SNAP_ID,Region,Latitude,Longitude,Key,IV\n")       
    for row in output:
        snap_id = row[0]
        region = "\"" + row[1] + "\"" if row[1] else ""
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

