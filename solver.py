import PyIndi
import numpy as np
from astropy import wcs
from astropy.wcs import WCS
from astropy.table import Table
from astropy.io import fits
import photutils
import time
import sys
import threading
import os
import subprocess as subp
import math
     
class IndiClient(PyIndi.BaseClient):
    def __init__(self):
        super(IndiClient, self).__init__()
    def newDevice(self, d):
        pass
    def newProperty(self, p):
        pass
    def removeProperty(self, p):
        pass
    def newBLOB(self, bp):
        global blobEvent
        blobEvent.set()
        pass
    def newSwitch(self, svp):
        pass
    def newNumber(self, nvp):
        pass
    def newText(self, tvp):
        pass
    def newLight(self, lvp):
        pass
    def newMessage(self, d, m):
        pass
    def serverConnected(self):
        pass
    def serverDisconnected(self, code):
        pass

# Set variables
debug=1
exposure=5.0
telescope="Telescope Simulator"
device_telescope=None
telescope_connect=None
ccd="CCD Simulator"
solveOk=0
maxDeviation = 30 # In ArcSecs

# connect the server
indiclient=IndiClient()
indiclient.setServer("localhost",7624)
 
if (not(indiclient.connectServer())):
     print("No indiserver running on "+indiclient.getHost()+":"+str(indiclient.getPort())+" - Try to run")
     print("  indiserver indi_simulator_telescope indi_simulator_ccd")
     sys.exit(1)
 
# get the telescope device
device_telescope=indiclient.getDevice(telescope)
while not(device_telescope):
    time.sleep(0.5)
    device_telescope=indiclient.getDevice(telescope)
     
# wait CONNECTION property be defined for telescope
telescope_connect=device_telescope.getSwitch("CONNECTION")
while not(telescope_connect):
    time.sleep(0.5)
    telescope_connect=device_telescope.getSwitch("CONNECTION")
 
# if the telescope device is not connected, we do connect it
if not(device_telescope.isConnected()):
    # Property vectors are mapped to iterable Python objects
    # Hence we can access each element of the vector using Python indexing
    # each element of the "CONNECTION" vector is a ISwitch
    telescope_connect[0].s=PyIndi.ISS_ON  # the "CONNECT" switch
    telescope_connect[1].s=PyIndi.ISS_OFF # the "DISCONNECT" switch
    indiclient.sendNewSwitch(telescope_connect) # send this new value to the device

# We want to set the ON_COORD_SET switch to engage tracking after goto
# device.getSwitch is a helper to retrieve a property vector
telescope_on_coord_set=device_telescope.getSwitch("ON_COORD_SET")
while not(telescope_on_coord_set):
    time.sleep(0.5)
    telescope_on_coord_set=device_telescope.getSwitch("ON_COORD_SET")

# the order below is defined in the property vector
telescope_on_coord_set[0].s=PyIndi.ISS_ON  # TRACK
telescope_on_coord_set[1].s=PyIndi.ISS_OFF # SLEW
telescope_on_coord_set[2].s=PyIndi.ISS_OFF # SYNC
indiclient.sendNewSwitch(telescope_on_coord_set)


# Set up CCD camera 
device_ccd=indiclient.getDevice(ccd)
while not(device_ccd):
    time.sleep(0.5)
    device_ccd=indiclient.getDevice(ccd)   
 
ccd_connect=device_ccd.getSwitch("CONNECTION")
while not(ccd_connect):
    time.sleep(0.5)
    ccd_connect=device_ccd.getSwitch("CONNECTION")
if not(device_ccd.isConnected()):
    ccd_connect[0].s=PyIndi.ISS_ON  # the "CONNECT" switch
    ccd_connect[1].s=PyIndi.ISS_OFF # the "DISCONNECT" switch
    indiclient.sendNewSwitch(ccd_connect)
 
ccd_exposure=device_ccd.getNumber("CCD_EXPOSURE")
while not(ccd_exposure):
    time.sleep(0.5)
    ccd_exposure=device_ccd.getNumber("CCD_EXPOSURE")
 
# Ensure the CCD driver snoops the telescope driver
ccd_active_devices=device_ccd.getText("ACTIVE_DEVICES")
while not(ccd_active_devices):
    time.sleep(0.5)
    ccd_active_devices=device_ccd.getText("ACTIVE_DEVICES")
ccd_active_devices[0].text=telescope
indiclient.sendNewText(ccd_active_devices)
 
# we should inform the indi server that we want to receive the
# "CCD1" blob from this device
indiclient.setBLOBMode(PyIndi.B_ALSO, ccd, "CCD1")
ccd_ccd1=device_ccd.getBLOB("CCD1")
while not(ccd_ccd1):
    time.sleep(0.5)
    ccd_ccd1=device_ccd.getBLOB("CCD1")

###############################################################
## M A I N                                                   ##
###############################################################

while (1):        # Loop forever
    # Update coordinates 
    telescope_radec=device_telescope.getNumber("EQUATORIAL_EOD_COORD")
    while not(telescope_radec):
        time.sleep(0.5)
        telescope_radec=device_telescope.getNumber("EQUATORIAL_EOD_COORD")      

    if (telescope_radec.s==PyIndi.IPS_BUSY):
        if debug:
             print("Scope Moving ", telescope_radec[0].value, "  ", telescope_radec[1].value)
             time.sleep(5)
        solveOk=False  # We'll need to do a solve after the motion stops
        if debug:
            print("Scope moving no solve required.")
    else:
        # Scope is not moving - are we finished or do we need another image?
        if solveOk:
            continue
        # See if User wants a solve by creating a solve.requested file
        if os.path.exists('solve.requested'):
            os.remove('solve.requested')
            solveOk = False

        if debug:
            print("Scope tracking solve required.")
 
        # Initiate an image on the camera
        blobEvent=threading.Event()
        blobEvent.clear()
        ccd_exposure[0].value=exposure
        indiclient.sendNewNumber(ccd_exposure)
        blobEvent.wait()
        blobEvent.clear()
        if debug:
            print("name: ", ccd_ccd1[0].name," size: ", ccd_ccd1[0].size," format: ", ccd_ccd1[0].format)
        ccdimage=ccd_ccd1[0].getblobdata()

        # Write the image to disk - disabled because astap won't solve ccd simulator images
#       filehandle = open('solve.fits', 'wb')
#       filehandle.write(ccdimage)
#       filehandle.close()

        # Remove plate solve results
        if os.path.exists('solve.ini'):
           os.remove('solve.ini')
        if os.path.exists('solve.wcs'):
           os.remove('solve.wcs')

        # Do a plate solve on the fits data
        cmd="/usr/local/bin/astap -r 50 -f solve.fits >solve.err 2>&1"
        if (debug): 
            print("Solving...")
            print(cmd)
        # Create a process to call the solver and wait for completion 
        timeout=0 
        os.system(cmd)
        while not os.path.exists('solve.wcs'):
            if debug:
                print ("Sleeping...")
            time.sleep(0.5)
            timeout=timeout+0.5
            if (timeout==10):
                print ("Error, solve not completed in 10s!")
                exit()

        # Load the wcs FITS hdulist using astropy.io.fits
        #with fits.open('solve.wcs', mode='readonly', ignore_missing_end=True) as fitsfile:
        #    w = WCS(fitsfile[0].header) 
        #    solveRa=w.wcs.crval[0]
        #    solveDec=w.wcs.crval[1]
        # Kludge because wcs file keeps bombing with corrupt file error, doh!
        os.system("cat solve.wcs | grep CRVAL1 | cut -b12-30 > solve.kludge")
        os.system("cat solve.wcs | grep CRVAL2 | cut -b12-30 >> solve.kludge")
        kludgefile=open("solve.kludge","r")
        rastr=kludgefile.read(19)
        decstr=kludgefile.read(1) # ignore the CR 
        decstr=kludgefile.read(19)
        if debug:
            print("Kludge coords: ",rastr," ",decstr)
        kludgefile.close()
        solveRa=float(rastr)
        solveDec=float(decstr)
        
        if (debug): 
            print("Solved RA= ",solveRa," Dec=",solveDec)

        # Load the ccd image FITS hdulist using astropy.io.fits
        with fits.open('solve.fits', mode='readonly', ignore_missing_end=True) as fitsfile:
            w = WCS(fitsfile[0].header) 
            ccdRa=w.wcs.crval[0]
            ccdDec=w.wcs.crval[1]
        if (debug): 
           print("CCD RA= ",solveRa," Dec=",solveDec)
            
        # Compare the plate solve to the current RA/DEC, convert to arcsecs
        deltaRa = (solveRa - ccdRa)*60*60 
        deltaDec = (solveDec - ccdDec)*60*60
        if (debug): 
           print("Delta RA= ",deltaRa," Delta Dec=",deltaDec)
        
        # If within the threshold arcsecs move the scope set solveOk and continue
        if ((deltaRa < 5) or (deltaDec < 5)):
            if debug:
                print("Deviation < 25 arcsecs, ignoring")
            solveOk=True
            continue;
        if debug:
            print("Deviation ",math.sqrt(deltaRa**2+deltaDec**2),"arcsecs compared to max ",maxDeviation," arcsecs")
        if math.sqrt(deltaRa**2+deltaDec**2) > maxDeviation:
           if debug:
               print("Moving scope to computed coordinates ",ccdRa+deltaRa," ",ccdDec+deltaDec)
           # Otherwise set the desired coordinate and slew
           telescope_radec=device_telescope.getNumber("EQUATORIAL_EOD_COORD")
           while not(telescope_radec):
               time.sleep(0.5)
           telescope_radec=device_telescope.getNumber("EQUATORIAL_EOD_COORD")
           telescope_radec[0].value=ccdRa+deltaRa
           telescope_radec[1].value=ccdDec+deltaDec
           indiclient.sendNewNumber(telescope_radec)
        else:
           solveOk=True

