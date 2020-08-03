from struct import *
import os
import binascii
import sys

DEBUG = True

def pdebug(*arg):
    print(*arg) if DEBUG else ""

def extract(params):
    if len(params) > 1:
        print("Opening file... This may take a while depending on the size.")
        if os.path.isfile(params[1]):
            file = open(params[1], "rb")
            arrHeader = []
            # Header Info
            arrHeader.append(unpack("<I", file.read(4))[0])  # magicNumber
            arrHeader.append(unpack("<I", file.read(4))[0])  # headerLength
            arrHeader.append(unpack("<I", file.read(4))[0])  # version
            arrHeader.append(unpack("<I", file.read(4))[0])  # soundbankid

            currentPos = 8
            while (currentPos < arrHeader[1]):
                arrHeader.append(unpack("<I", file.read(4))[0])  # Unknown
                currentPos = currentPos + 4

            arrHIRC = []
            # HIRC
            print(unpack("cccc", file.read(4)))  # hirc magic
            hircLen = unpack("<I", file.read(4))[0]  # chunkLength
            hircObjectsNo = unpack("<I", file.read(4))[0]  # object no
            print("hircObjectsNo ", hircObjectsNo )
            for i in range(hircObjectsNo):
                objType = int(unpack("<B", file.read(1))[0])
                objLen = int(unpack("<I", file.read(4))[0])
                objectId = int(unpack("<I", file.read(4))[0])
                print("object id", objectId)
                if objType == 2:
                    unpack("cccc", file.read(4)) #waste unknown data
                    print("+- type sfx")
                    includedInBNK = ord(unpack("<c", file.read(1))[0])
                    streamed = False
                    if includedInBNK == 0:
                        print(" |- not streamed")
                    elif includedInBNK == 1:
                        print(" |- streamed")
                        streamed = True
                    elif includedInBNK == 2:
                        print(" |-streamed, zero latency")
                        streamed = True
                    audioID = int(unpack("<I", file.read(4))[0])
                    print(" |- audio ID", audioID)
                    sourceID = int(unpack("<I", file.read(4))[0])
                    if not streamed:
                        print(" |- source ID", sourceID)
                elif objType == 11:
                    print("+- type sfx")
                    effectSectionYN = ord(unpack("<c", file.read(1))[0])
                    numberOfEffect = ord(unpack("<c", file.read(1))[0])
                else: 
                    print("TODO: OBJECT TYPE", objType)
            file.close()
        else:
            print("\nError while opening file. This file might not exist.\nUsage instructions: python BnkExtract.py [path + name of file]\n")
    else:
        print("Usage instructions: python BnkExtract.py [path + name of file]\n")

READ_TOTAL_STRING = 0
READ_TEXT = 1
READ_SUB_DATA = 2
READ_SUB_DATA_IDS = 3
def extractDat(params):
    if len(params) > 1:
        print("Opening file... This may take a while depending on the size.")
        if os.path.isfile(params[1]):
            file = open(params[1], "rb")
            titles = []
            ids = []
            fileSize = os.path.getsize(params[1])
            print("size", fileSize)
            state = READ_TOTAL_STRING
            count = 0
            totalString = 0
            subDataLength = 0
            subDataCount = 0
            subDataIdLength = 0
            subDataIdCount = 0
            isSubDataReadId = False 
            zeroFlagDetected = False
            while file.tell()  < fileSize:
                position = file.tell()
                if state == READ_TOTAL_STRING: 
                    totalString = int(unpack("<I", file.read(4))[0])
                    count = 0
                    zeroFlagDetected = False
                    state = READ_TEXT
                if state == READ_TEXT:
                    count += 1
                    pdebug("stream pos for len", file.tell())
                    lengthStr = int(unpack("<I", file.read(4))[0]) 
                    print(lengthStr)
                    if lengthStr > 10000:
                        #this doesn make sense NOTE-ID: 0001
                        file.seek(-4, 1)
                        state = READ_SUB_DATA_IDS
                        continue
                    if lengthStr == 0:
                        zeroFlagDetected  = True
                        continue
                        #this doesnt make sense NOTE-ID: 0002
                    pdebug("stream pos for string", file.tell())
                    title = unpack('{}s'.format(lengthStr), file.read(lengthStr))[0].decode("ascii")
                    pdebug("current pos for id", file.tell())
                    id = int(unpack("<I", file.read(4))[0])
                    if title != "" : 
                        titles.append(title)
                        print(id, "-", title, "LENGTH", lengthStr)
                    pdebug("current stream pos", file.tell())
                    #check for subdata
                    if count >= totalString:
                        state = READ_TOTAL_STRING
                        #read sub data id guss?
                    if id < 10000 and id != 0:
                        pdebug("ËNTERING SUB DATA")
                        state = READ_SUB_DATA
                        subDataLength = id
                if state == READ_SUB_DATA:
                    subDataCount += 1
                    pdebug("stream pos for subdata len", file.tell())
                    length = int(unpack("<I", file.read(4))[0])
                    pdebug("subdata len", length)
                    try:
                        #check if readable string for 4 bytes?
                        title = unpack('{}s'.format(4), file.read(4))[0].decode("ascii")
                        if length > 10000: raise("not a valid char")
                        #test if all chars IS READABLE!
                        #for s in title:
                        #    continue if ord(s) >= 0x21 and ord(s) <= 0x7e else raise("")
                    except :
                        state = READ_SUB_DATA_IDS
                        file.seek(-12, 1)
                        subDataIdLength = int(unpack("<I", file.read(4))[0])
                        continue
                    file.seek(-4, 1)
                    pdebug("stream pos for subdata string", file.tell())
                    title = unpack('{}s'.format(length), file.read(length))[0].decode("ascii")
                    if title != "" : 
                        #titles.append(title)
                        print("tags: ", title)
                    if isSubDataReadId:
                        unknown = int(unpack("<I", file.read(4))[0]) #idk at cursor pos 910422
                    pdebug("current stream pos", file.tell())
                    
                    #check if finished reading subdata
                    if subDataCount >= subDataLength:
                        state = READ_TEXT
                        subDataCount = 0
                        isSubDataReadId = False
                        if count >= totalString:
                            state = READ_TOTAL_STRING

                if state == READ_SUB_DATA_IDS:
                    subDataIdCount += 1
                    pdebug("stream pos for subdata id", file.tell())
                    subDataId = int(unpack("<I", file.read(4))[0])
                    print("sub data id", subDataId)
                    
                    #check if finished reading subdata ids
                    if subDataIdCount >= subDataIdLength:
                        state = READ_TEXT
                        subDataIdCount = 0
                        if count >= totalString:
                            state = READ_TOTAL_STRING

            file.close()
            print("total strings collected", len(titles))
        else:
            print("\nError while opening file. This file might not exist.\nUsage instructions: python BnkExtract.py [path + name of file]\n")
    else:
        print("Usage instructions: python BnkExtract.py [path + name of file]\n")

"""if (len(sys.argv) > 1 ): extract(sys.argv)
else: extract([ "", "campaign_advice__bretonnia_owners.bnk"])
"""
if (len(sys.argv) > 1 ): extract(sys.argv)
#else: extractDat([ "", "event_data__tomb_kings_owners.dat"])
#else: extractDat([ "", "event_data__bretonnia_owners.dat"])
#else: extractDat([ "", "event_data__grand_campaign_owners.dat"])
#else: extractDat([ "", "event_data__blood_pack_owners.dat"])
else: extractDat([ "", "test_subject.dat"])
#else: extractDat([ "", "event_data__core.dat"])