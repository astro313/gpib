'''interact with the Prologix GPIB and E4407B'''
import serial
import time, sys, numpy as n


class PrologixGpibChat(object):
    '''
    GPIB communication over prologix USB adapter
    '''
    def __init__(self, serial_dev):
        # track the current device address
        self.active_addr = None

        self.ser = serial.Serial(port=serial_dev,
                                 baudrate=115200,
                                 parity=serial.PARITY_NONE,
                                 stopbits=serial.STOPBITS_ONE,
                                 bytesize=serial.EIGHTBITS,
                                 timeout=10)
        #print 'a list of baudrate supported by the Serial Port', self.ser.getSupportedBaudrates() 
        self.ser.flushInput()
        self.ser.flushOutput()
        #sys.exit(1)

        self.initialize_prologix()

    def send_single(self, cmd_str, wait=0.5):
        '''
        send a Prologix or SCPI command and read the reply from Prologix if any
        '''

        self.ser.write(cmd_str + "\r\n")
        time.sleep(0.5)
        self.ser.flush()

        self.ser.write("++read eoi\r\n")
        time.sleep(1)

        output = ''
        while self.ser.inWaiting():
                print 'In waiting: %d' %self.ser.inWaiting()    # num of char waiting
                output += self.ser.read(self.ser.inWaiting())
                time.sleep(3)
                self.ser.inWaiting()
        if len(output) != 0:
            print "sent: %s, reply: %s" %(cmd_str, output)
        else:
            print "Send: %s" %cmd_str
        time.sleep(wait)
        return output

    def initialize_prologix(self):
        '''
        Issue a reset and put Prologix interface in control mode
        '''
        print "Initializing Prologix USB-GPIB card..."

        self.send_single("++rst")
        print "Waiting 5 sec after Prologix reset..."
        time.sleep(5)

        self.ser.flushInput()     # clears input buffer, 
        self.ser.flushOutput()    # clears output buffer,

        self.send_single("++mode 1")
        self.send_single("++auto 1")


    def gpib_addr(self, addr):
        '''
        send a command to a GPIB adddress and wait for reply
        '''
        if addr != self.active_addr:
            self.send_single("++addr %s" %addr)
            self.active_addr = addr


    def gpib_measure_call(self, cmd_str):
        '''
        Return a list of data if ask for trace,
        convert to float
        '''

        self.ser.write(cmd_str + "\r\n")
        time.sleep(0.5)
        self.ser.flush()
        self.ser.write("++read eoi\r\n")

        output = ''  
        time.sleep(5)

        if self.ser.inWaiting == 0:
            time.sleep(3)

        while self.ser.inWaiting():
            print 'In waiting: %d' %self.ser.inWaiting()    # num of char waiting
            output += self.ser.read(self.ser.inWaiting())
            time.sleep(3)
            self.ser.inWaiting()
        print "sent: %s, reply: %s" %(cmd_str, output)

        data_vals = []
        raw_vals = output.split(",")
        for raw_data in raw_vals[0:-2]:
            data_vals.append(float(raw_data))
        return data_vals


class Automation(object):
    '''handle all communication'''
    def __init__(self, serial_dev, meter_addr="18"):
        self.meter_addr = meter_addr
        self.gpib_bus = PrologixGpibChat(serial_dev)

    def setup_config(self):
        '''configuring spectrum analyzer'''
        self.gpib_bus.send_single("*RST;*CLS", wait=3.5)
        print("Setting start freq to 100 MHz...")
        self.gpib_bus.send_single(":SENS:FREQ:STAR 100 MHz")
        print("Setting stop freq to 200 MHz...")
        self.gpib_bus.send_single(":SENS:FREQ:STOP 200 MHz")
#        print("# of points -> 801")
#        self.gpib_bus.gpib_call(":SENS:SWE:POIN 801")
        print("Attenuation -> 0 dBm")
        self.gpib_bus.send_single(":SENS:POW:RF:ATT 0 dB", wait=1.5)
        #print("Setting bandwidth...")
        #self.gpib_bus.gpib_call(":SENS:BWID:RES 1 kHz", wait = 150)
        time.sleep(2)
        trace = self.gpib_bus.gpib_measure_call(":TRAC:DATA? TRACE1")
        #print("PRESS System then press SAVE NOW on Spectrum analyzer")
        #time.sleep(10)
        #checksave()

        #self.zoom_config1()

    def zoom_config1(self):
        '''
        Zoom in 120-130 MHz with the rest of the config same as setup_config
        '''
        print("Setting start freq to 120 MHz...")
        self.gpib_bus.gpib_call(":SENS:FREQ:STAR 120 MHz", 
                                addr=self.meter_addr)
        print("Setting stop freq to 130 MHz...")
        self.gpib_bus.gpib_call(":SENS:FREQ:STOP 130 MHz", 
                                addr=self.meter_addr)
        print("PRESS System then press SAVE NOW on Spectrum analyzer")
        time.sleep(10)
        checksave()

        self.zoom_config2()
        
    def zoom_config2(self):
        '''
        Zoom in 165-175 MHz with the rest of the config same as setup_config
        '''
        print("Setting start freq to 165 MHz...")
        self.gpib_bus.gpib_call(":SENS:FREQ:STAR 165 MHz")
        print("Setting stop freq to 175 MHz...")
        self.gpib_bus.gpib_call(":SENS:FREQ:STOP 175 MHz")
        print("PRESS System then press SAVE NOW on Spectrum analyzer")
        time.sleep(10)
        checksave()

        self.zoom_config3()


    def zoom_config3(self):
        '''
        Zoom in 133-136 MHz with the rest of the config same as setup_config
        '''
        print("Setting start freq to 155 MHz...")
        self.gpib_bus.gpib_call(":SENS:FREQ:STAR 155 MHz")
        print("Setting stop freq to 160 MHz...")
        self.gpib_bus.gpib_call(":SENS:FREQ:STOP 160 MHz")
        print("PRESS System then press SAVE NOW on Spectrum analyzer")
        time.sleep(10)
        checksave()
        print ("\t---> Going back to 100 - 200MHz in 2 minutes <---\n")
        time.sleep(120)
        self.setup_config()


def checksave():
    wait_save_done = raw_input("USER_INPUT: press y to continue \
        if data is saved: ")
    while wait_save_done != 'y':
        wait_save_done = raw_input("USER_INPUT: press y to continue if \
            data is saved: ")
    print ("Continue to next set")

#######================= ####### TRACE NOT WORKING #########==================
#        self.gpib_bus.gpib_call(":MMEM:STOR:RES 'C:filename000.CSV'", addr=self.meter_addr)
#        self.gpib_bus.gpib_call(":MMEM:STOR:TRAC TRACE1,'C:mytrace00.CSV'", addr=self.meter_addr)
#        self.gpib_bus.gpib_call(":TRAC:DATA? TRACE1", addr=self.meter_addr)
#        self.gpib_bus.gpib_call("SYST:ERR?", addr=self.meter_addr)
#        self.gpib_bus.gpib_call("++read eoi", addr=self.meter_addr)
#        self.gpib_bus.gpib_call(":MMEM:CAT? 'C:'", addr=self.meter_addr)
        #self.gpib_bus.gpib_call(":FORM:DATA ACI ", addr=self.meter_addr)
        #file_out = open('123123.csv', "w")
#=============================================================================


if __name__ == "__main__":
    sa = Automation("/dev/tty.usbserial-PXHD6DZD")
    #while True:
    sa.setup_config()