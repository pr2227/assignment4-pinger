#from msilib import sequence
from socket import *
import os
from statistics import stdev
import sys
import struct
import time
import select
import binascii
# Should use stdev

ICMP_ECHO_REQUEST = 8


def checksum(string):
    # print('Entering checksum')
    csum = 0
    countTo = (len(string) // 2) * 2
    count = 0

    while count < countTo:
        thisVal = (string[count + 1]) * 256 + (string[count])
        csum += thisVal
        csum &= 0xffffffff
        count += 2

    if countTo < len(string):
        csum += (string[len(string) - 1])
        csum &= 0xffffffff

    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer



def receiveOnePing(mySocket, ID, timeout, destAddr):
    #print('Entering receiveOnePing')
    timeLeft = timeout

    while True:
        startedSelect = time.time() * 1000
        #print('startedSelect is ', end = '')
        #print(startedSelect)
        whatReady = select.select([mySocket], [], [], timeLeft)
        #howLongInSelect = (time.time() - startedSelect)
        if whatReady[0] == []:  # Timeout
            return "Request timed out."

        # Calc the Round Trip Time
        recPacket, addr = mySocket.recvfrom(1024) 
        timeReceived = time.time() * 1000
        #print('timereceived:', end = ' ')
        #print(timeReceived)
        delay = timeReceived - startedSelect
        #print('delay:', end = ' ')
        #print(format(delay,".2f"))

        # Fill in start
        # Ignore the ipHeader[0:19] and grab the contents of the icmpHeader.
        # icmpHeader = recPacket[20:28]
        # break our the header into the ICMP header fields
        type, code, checksum, identifier, sequenceNum = struct.unpack("bbHHh",recPacket[20:28])
        #print('type:', end = ' ')
        #print(type)
        #print('code:', end = ' ')
        #print(code)
        #print('checksum:', end = ' ')
        #print(checksum)
        #print('identifier:', end = ' ')
        #print(identifier)
        #print('sequenceNum:', end = ' ')
        #print(sequenceNum)

        # Fetch the ICMP header from the IP packet
        # If Echo Reply
        if type == 0:
            return delay
        #packedTime = struct.unpack("d", recvPacket[28:28 + bytes])[0]
        # Fill in end
        #timeLeft = timeLeft - howLongInSelect
        if timeLeft <= 0:
            return "Request timed out."


def sendOnePing(mySocket, destAddr, ID):
    # Header is type (8), code (8), checksum (16), id (16), sequence (16)
    #print('Entering sendOnePing')
    myChecksum = 0
    # Make a dummy header with a 0 checksum
    # struct -- Interpret strings as packed binary data
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    data = struct.pack("d", time.time())
    # Calculate the checksum on the data and the dummy header.
    myChecksum = checksum(header + data)

    # Get the right checksum, and put in the header

    if sys.platform == 'darwin':
        # Convert 16-bit integers from host to network  byte order
        myChecksum = htons(myChecksum) & 0xffff
    else:
        myChecksum = htons(myChecksum)


    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    packet = header + data

    mySocket.sendto(packet, (destAddr, 1))  # AF_INET address must be tuple, not str

    # Both LISTS and TUPLES consist of a number of objects
    # which can be referenced by their position number within the object.

def doOnePing(destAddr, timeout):
    #print('Entering doOnePing')
    icmp = getprotobyname("icmp")

    # SOCK_RAW is a powerful socket type. For more details:   https://sock-raw.org/papers/sock_raw
    mySocket = socket(AF_INET, SOCK_RAW, icmp)

    myID = os.getpid() & 0xFFFF  # Return the current process i
    sendOnePing(mySocket, destAddr, myID)
    delay = receiveOnePing(mySocket, myID, timeout, destAddr)
    mySocket.close()
    return delay


def ping(host, timeout=1):
    #print('Entering ping')
    # timeout=1 means: If one second goes by without a reply from the server,  	
    # the client assumes that either the client's ping or the server's pong is lost
    dest = gethostbyname(host)
    print("Pinging " + dest + " using Python:")
    print("")
    
    #Send ping requests to a server separated by approximately one second
    #Add something here to collect the delays of each ping in a list so you can calculate vars after your ping
    listOfDelay = []
    for i in range(0,4): #Four pings will be sent (loop runs for i=0, 1, 2, 3)
        delay = doOnePing(dest, timeout)
        print(delay)
        time.sleep(1)  # one second
        listOfDelay.append(delay)


    packet_min =min(listOfDelay)
    #print('packet_min is:' + str(packet_min))
    packet_avg = sum(listOfDelay) / len(listOfDelay)
    #print('packet_avg is:' + str(packet_avg))
    packet_max = max(listOfDelay)
    #print('packet_max is:' + str(packet_max))
    stdev_var = (sum((x-(sum(listOfDelay) / len(listOfDelay)))**2 for x in listOfDelay) / (len(listOfDelay)-1))**0.5
    #print('stdev is ' + str(stdev_var))

        
    #You should have the values of delay for each ping here; fill in calculation for packet_min, packet_avg, packet_max, and stdev
    vars = [str(round(packet_min, 8)), str(round(packet_avg, 8)), str(round(packet_max, 8)),str(round(stdev_var, 8))]

    return vars

if __name__ == '__main__':
    ping("google.com")