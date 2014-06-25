'''interact with the Prologix GPIB and E4407B
'''

import serial
import time
import numpy as np
import matplotlib.pyplot as plt

units = {'kHz':1.0E3,'MHz':1.0E6,'GHz':1.0E9}

class Prologix(object):
    """
    GPIB communication over prologix USB adapter
    """
    def __init__(self, serial_dev="/dev/tty.usbserial-PXHD6DZD",buffer_latency=0.2):
        """
        buffer_latency is the 'one size fits all'; whereas smaller buffer reads (e.g. :STAR) may allow shorter
        """
        self.ser = serial.Serial(port=serial_dev,
                                 baudrate=19200,
                                 parity=serial.PARITY_NONE,
                                 stopbits=serial.STOPBITS_ONE,
                                 bytesize=serial.EIGHTBITS,
                                 timeout=1)

        self.initialize_prologix(buffer_latency)

    def initialize_prologix(self,buffer_latency):
        """
        Issue a reset and put Prologix interface in control mode
        """
        print "Initializing Prologix USB-GPIB card"
        self.buffer_latency = buffer_latency
        self.cmd("++rst")
        print "Waiting 5 sec after Prologix reset..."
        time.sleep(5)
        prologix = self.cmd("++ver")
        print prologix

        self.cmd("++mode 1")
        self.cmd("++auto 1")

    def cmd(self,cmd_str,verbose=False):
        buff = self.get_buffer()   # check if anything in buffer before sending the command
        if len(buff)>0:    # got the stuff out of buffer
            print 'Cleared buffer:  '+buff   # cleared the junk

        self.write_buffer(cmd_str)
        buff = self.get_buffer()
        if verbose:
            print "sent: %s\nreply: %s" %(cmd_str, buff)
        buff = buff.strip()
        return buff

    def set_addr(self,addr):
        self.addr = addr
        self.write_buffer('++addr %d' % (self.addr))

    def write_buffer(self,cmd_str):
        cmd_str = cmd_str.strip()
        self.ser.write(cmd_str+'\n')

    def get_buffer(self):

        time.sleep(self.buffer_latency)
        output = ''
        data_in_buffer = self.ser.inWaiting()
        while data_in_buffer:
            output += self.ser.read(data_in_buffer)
            time.sleep(self.buffer_latency+2)
            data_in_buffer = self.ser.inWaiting()
        return output

        

class sa(object):
    """
    Spectrum analyzer
    """

    def __init__(self, addr=18, serial_dev="/dev/tty.usbserial-PXHD6DZD", buffer_latency=0.2):

        self.gpib = Prologix(serial_dev,buffer_latency)
        self.addr = addr
        self.gpib.set_addr(addr)
        self.gpib.cmd("*RST;*CLS")
        time.sleep(3.5)

        self.name = self.gpib.cmd('*IDN?')
        print self.name

        self.scpi = {'start' : [':SENS:FREQ:STAR','MHz',float],
                     'stop'  : [':SENS:FREQ:STOP','MHz',float],
                     'center': [':SENS:FREQ:CENT','MHz',float],
                     'span'  : [':SENS:FREQ:SPAN','MHz',float],
                     'pts'   : [':SENS:SWE:POIN',None,int],
                     'att'   : [':SENS:POW:RF:ATT',None,float],
                     'rbw'   : [':SENS:BWID:RES','kHz',float],
                     'vbw'   : [':SENS:BWID:VID','kHz',float]
            }



    def spec(self,unit='MHz',plot=True):

        a = self.gpib.cmd(':TRAC:DATA? TRACE1')
        start = self.gpib.cmd(':SENS:FREQ:START?')
        try:
            start = float(start)/units[unit]
        except ValueError:
            print 'Error in start: '+start
        stop = self.gpib.cmd(':SENS:FREQ:STOP?')
        try:
            stop = float(stop)/units[unit]
        except ValueError:
            print 'Error in stop:  '+stop

        pts = self.gpib.cmd(':SENS:SWE:POIN?')
        try:
            pts = int(pts)
        except ValueError:
            print 'Error in pts:  '+pts
            pts = 1
        step = (stop - start)/ pts   # resolution
        print '%f - %f %s (%d points)' % (start,stop,unit,pts) 
        b = a.split(',')
        spec = []
        for i,s in enumerate(b):
            freq = start + i*step
            spec.append([freq,float(s)])
        spec = np.array(spec)    # 2 cols 
        if plot:
            plt.plot(spec[:,0],spec[:,1])
            plt.xlabel('Freq [MHz]')
            plt.ylabel('dB')
            plt.show()
        return spec


    def getv(self,par,unit=None):
        s = self.gpib.cmd(self.scpi[par][0]+'?')    # scpi query of that 'par'
        if unit is None:
            unit = self.scpi[par][1]

        try:
            sa = self.scpi[par][2](s)      
        except ValueError:
            print 'Error reading '+par+':  '+s  
        if unit is not None:
            sa = sa/units[unit]
        return sa, unit


    def setv(self,par,value,unit=None):
        svalue = str(value)
        if unit is None:
            unit = self.scpi[par][1]
        if unit is not None:
            scpi = '%s %s %s' % (self.scpi[par][0],svalue,unit)
        else:
            scpi = '%s %s' % (self.scpi[par][0],svalue)
        s = self.gpib.cmd(scpi)   # output from sending the scpi
        sa = self.getv(par,unit=unit)   # confirm scpi command interacted with instrument
        if value is float or value is int:
            if abs(sa[0] - value)/value > 0.02:
                print 'Mismatch between set %s (%f) and sa %s (%f)' % (par,value,par,sa)
        return sa


def saveresult(sa_class, start_fq, stop_fq, unit_fq, atten, pts, rbw, unit_rbw):

    sa_class.setv('start', start_fq, unit_fq)
    sa_class.setv('stop', stop_fq, unit_fq)

    spec_start.setv('att', atten)
    spec_start.setv('pts', pts)
    spec_start.setv('rbw', rbw, unit_rbw)
    result_trace = sa_class.spec(plot=False)

    from datetime import datetime
    hdr = 'start_fq: %s %s, stop_fq: %s %s, \nattenuation: %s, number of points: %s, \nbandwidth resolution: %s %s, \n%s, \nFrequency [%s], dB' \
        %(str(start_fq), unit_fq, str(stop_fq), unit_fq, str(atten), str(pts), str(rbw), unit_rbw, str(datetime.now()), unit_fq) 

    foname = 'Trace%s%s-%s.csv' %(str(start_fq), str(stop_fq), str(datetime.now().time())[:5])
    np.savetxt(foname, result_trace, delimiter=',', header=hdr)
    print '---Saved %s.----' %foname
    

#========================================================
if __name__ == '__main__':
    spec_start = sa()
    freq_dict = {'range1': [100, 200, 'MHz'],
                    'range2': [120, 130, 'MHz'],
                    'range3': [155, 160, 'MHz'],
                    'range4': [165, 175, 'MHz']
                    }
    atten = 0
    pts = 801
    rbw = 100
    unit_rbw = 'kHz'


    while True:
        saveresult(spec_start, freq_dict['range1'][0], \
            freq_dict['range1'][1], freq_dict['range1'][2], atten, pts, rbw, unit_rbw)
        saveresult(spec_start, freq_dict['range2'][0], \
            freq_dict['range2'][1], freq_dict['range2'][2], atten, pts, rbw, unit_rbw)
        saveresult(spec_start, freq_dict['range3'][0], \
            freq_dict['range3'][1], freq_dict['range3'][2], atten, pts, rbw, unit_rbw)
        saveresult(spec_start, freq_dict['range4'][0], \
            freq_dict['range4'][1], freq_dict['range4'][2], atten, pts, rbw, unit_rbw)
        time.sleep(300)




