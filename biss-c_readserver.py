
"""
### BEGIN NODE INFO
[info]
name = BISSCREADER
version = 1.0
description = Server for the Biss-C reading arduino and dac
[startup]
cmdline = %PYTHON% %FILE%
timeout = 
[shutdown]
message = 
timeout = 
### END NODE INFO
"""
from labrad.server import setting, Signal
from labrad.devices import DeviceServer,DeviceWrapper
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet import reactor, defer
import labrad.units as units
from labrad.types import Value
import numpy as np
import time
#from exceptions import IndexError

TIMEOUT = Value(5,'s')
BAUD    = 115200

def mapfourbyte(b):
    return 256*256*256*b[3] + 256*256*b[2] + 256*b[1] + b[0]

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

class BISSCWrapper(DeviceWrapper):
    @inlineCallbacks
    def connect(self, server, port):
        """Connect to a device."""
        print('connecting to "%s" on port "%s"...' % (server.name, port), end=' ')
        self.server = server
        self.ctx = server.context()
        self.port = port
        p = self.packet()
        p.open(port)
        p.baudrate(BAUD)
        p.read()  # clear out the read buffer
        p.timeout(TIMEOUT)
        print(" CONNECTED ")
        yield p.send()

    def packet(self):
        """Create a packet in our private context."""
        return self.server.packet(context=self.ctx)

    def shutdown(self):
        """Disconnect from the serial port when we shut down."""
        return self.packet().close().send()

    @inlineCallbacks
    def write(self, code):
        """Write a data value."""
        yield self.packet().write(code).send()

    @inlineCallbacks
    def read(self):
        p=self.packet()
        p.read_line()
        ans=yield p.send()
        returnValue(ans.read_line)

    @inlineCallbacks
    def readByte(self,count):
        p=self.packet()
        p.readbyte(count)
        ans=yield p.send()
        returnValue(ans.readbyte)

    @inlineCallbacks
    def in_waiting(self):
        p = self.packet()
        p.in_waiting()
        ans = yield p.send()
        returnValue(ans.in_waiting)

    @inlineCallbacks
    def reset_input_buffer(self):
        p = self.packet()
        p.reset_input_buffer()
        ans = yield p.send()
        returnValue(ans.reset_input_buffer)

    @inlineCallbacks
    def timeout(self, time):
        yield self.packet().timeout(time).send()

    @inlineCallbacks
    def query(self, code):
        """ Write, then read. """
        p = self.packet()
        p.write_line(code)
        p.read_line()
        ans = yield p.send()
        returnValue(ans.read_line)

class BISSCREAD_Server(DeviceServer):
    deviceName = 'BISSC_ARDUINO'
    name = 'BISSC_SERVER'
    deviceWrapper = BISSCWrapper
    @inlineCallbacks
    def initServer(self):
        print('loading config info...', end=' ')
        self.reg = self.client.registry()
        yield self.loadConfigInfo()
        print('done.')
        print(self.serialLinks)
        yield DeviceServer.initServer(self)

    @inlineCallbacks
    def loadConfigInfo(self):
        """Load configuration information from the registry."""
        reg = self.reg
        yield reg.cd([ 'Servers', 'BISS-C_SERVER', 'Links'], True)
        dirs, keys = yield reg.dir()
        p = reg.packet()
        for k in keys:
            p.get(k, key=k)
        ans = yield p.send()
        self.serialLinks = dict((k, ans[k]) for k in keys)

    @inlineCallbacks
    def findDevices(self):
        """Find available devices from list stored in the registry."""
        devs = []
        for name, (serServer, port) in self.serialLinks.items():
            if serServer not in self.client.servers:
                continue
            server = self.client[serServer]
            ports = yield server.list_serial_ports()
            if port not in ports:
                continue
            devName = '%s - %s' % (serServer, port)
            devs += [(devName, (server, port))]
        returnValue(devs)

    @setting(100)
    def connect(self,c,server,port):
        dev=self.selectedDevice(c)
        yield dev.connect(server,port)
    
    @setting(500, returns='s')
    def IDN(self, c):
        """
        Returns the ID BISS-C_READER.
        """
        dev = self.selectedDevice(c)
        yield dev.write("*IDN?\r")
        ans = yield dev.read()
        returnValue(ans)

    @setting(501, returns='s')
    def RDY(self, c):
        """
        Returns Ready when serial is available.
        """
        dev = self.selectedDevice(c)
        yield dev.write("*RDY?\r")
        ans = yield dev.read()
        returnValue(ans)
        
    @setting(502, returns='**v[]')
    def startRecRun(self, c):
        """
        Toggles the recording of position and time data on, for one run. Returns run data in an 2xN array (time, position)
        """
        data = b''
        dev = self.selectedDevice(c)
        bytes = []
        transdat = []
        try:
            nbytes = 0
            abrk = False
            yield dev.write("BUFFLAG\r")
            while(True):
                ans = yield dev.read()
                if(ans == "*ON"):
                        while(True):
                            bytestoread = yield dev.in_waiting()
                            if bytestoread > 0:
                                    tmp = yield dev.readByte(bytestoread)
                                    data = data + tmp
                                    nbytes = nbytes + bytestoread
                                    if(data[-5:] == b'OFF\r\n'): #last 5 elements after nothing is received.
                                        yield dev.write("BUFFLAG\r")
                                        abrk = True
                                        break
                if(abrk):
                    data = list(data)
                    bytes = list(chunks(data[:(len(data)-8)], 4))
                    transdat = list(map(mapfourbyte, bytes))
                    break
        except Exception as e:
            print(e)
            print("Exception occured")

        try:
            yield dev.read()
        except:
            print("Error clearing the serial buffer after reading.")

        returnValue([transdat[::2], transdat[1::2]])

        

    @setting(503, returns='s')
    def setZeroHere(self, c):
        """
        Calibrates the current position as the zero position for the dac voltage
        """
        dev = self.selectedDevice(c)
        yield dev.write("ZERO\r")
        ans = yield dev.read()
        returnValue(ans)
    
    @setting(504, ran='v[]', returns='s')
    def TravelRANGE(self, c, ran):
        """
        Calibrates the travel range for the DAC in mm, centered at the zero position. 
        """
        dev = self.selectedDevice(c)
        yield dev.write("TRANGE,%f\r"%(ran))
        ans = yield dev.read()
        returnValue(ans)
    
    @setting(505, maxva='v[]', returns='s')
    def MAXVEL(self, c, maxva):
        """
        Sets the maxvel for DAC measurements. 
        """
        dev = self.selectedDevice(c)
        yield dev.write("MAXVEL,%f\r"%maxva)
        ans = yield dev.read()
        returnValue(ans)

    @setting(506, returns='s')
    def getEncPos(self, c):
        """
        Returns the absolute position of the encoder in encoder units. Useful for debugging.
        """
        st = b''
        dev = self.selectedDevice(c)
        yield dev.write("GETPOS\r")
        ans = yield dev.read()
        returnValue(ans)
        
    @setting(507, millis= 'i',returns='s')
    def setDelay(self, c, millis):
        """
        Sets the delay inbetween loops by this number of milliseconds.
        """
        dev = self.selectedDevice(c)
        yield dev.write("SETDELAY,%i\r"%(millis))
        ans = yield dev.read()
        returnValue(ans)

    @setting(508,returns='s')
    def toggleDAC(self, c):
        """
        Toggles dac voltage updating on or off.
        """
        dev = self.selectedDevice(c)
        yield dev.write("DACTOGGLE\r")
        ans = yield dev.read()
        returnValue(ans)

    @setting(509,returns='**v[]')
    def getConfig(self, c):
        """
        Gets the values of [maxvel, range, zeropos] on the arduino for usage with dac. (mm/s, cm, encoder units). To translate encoder units multiply by 50nm.
        Gets absolute position, somewhere around 5.5m (111540638 in enc units).
        """
        dev = self.selectedDevice(c)
        yield dev.write("CONFIG\r")
        ans = yield dev.read()
        indexs = [i for i in range(len(ans)) if ans[i] == ';']
        arrfl = []
        indexs.insert(0,-1)
        for l in range(len(indexs)-1):
            arrfl.append(float(ans[(indexs[l]+1):indexs[l+1]]))
        returnValue(arrfl)
    
    @setting(510,mm = 'v[]',returns='s')
    def setZeroAt(self, c, mm):
        """
        Calibrates the given mm as the zero position for the dac voltage
        """
        dev = self.selectedDevice(c)
        yield dev.write("ZEROMM,%f\r"%(mm))
        ans = yield dev.read()
        returnValue(ans)

    
    


__server__ = BISSCREAD_Server()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)