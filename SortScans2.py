#!/usr/bin/python
import sys, os, subprocess, glob, StringIO, time

from multiprocessing import Pool

def PDF2TIFF(name):

    Pass = name[0]
    Page = name[1:-1]
    Side = name[-1:]

    if Side == "R":
        Geom = "'20.9cm 0cm 0cm 0cm'"
    else:
        Geom = "'0cm 0cm 20.9cm 0cm'"

    os.system("pdfjam -q --trim "+Geom+" --clip true /tmp/SDAPS/Pass"+Pass+"/"+Page+".pdf --outfile /tmp/SDAPS/"+Pass+Side+".pdf")
    os.system("gs -dNOPAUSE -q -r300 -sDEVICE=tiff12nc -dBATCH -sCompression=pack -sOutputFile=/tmp/SDAPS/"+Pass+Side+".tif /tmp/SDAPS/"+Pass+Side+".pdf")
    os.system("convert -colors 4 -compress zip /tmp/SDAPS/"+Pass+Side+".tif /tmp/SDAPS/"+Pass+Side+"c.tif")

    if Pass+Side == "AR":
        os.system("gs -dNOPAUSE -q -r300 -sDEVICE=tiffgray -dBATCH  -sOutputFile=/tmp/SDAPS/"+Pass+Side+"gray.tif /tmp/SDAPS/"+Pass+Side+".pdf")
        os.system("convert -threshold 75% /tmp/SDAPS/"+Pass+Side+"gray.tif /tmp/SDAPS/"+Pass+Side+"bw.tif")



def NumberOfPdfPages(pdf_file):
    ShellOutputLines = os.popen("pdfinfo "+pdf_file+" | grep Pages").read().split("\n") 
    return int(ShellOutputLines[0].split()[1])


def GetBarCodes(file):
    BarCodes = []
    ShellOutputLines = os.popen("zbarimg  -q "+file+" 2> /dev/null ").read().split("\n") 
    for line in ShellOutputLines[0:-1]:
        typ = line.split(":")[0]
        val = line.split(":")[1]
        if typ == "CODE-128":
            if len(val) < 6:
                BarCodes = BarCodes + [ val ]
            else:
                BarCodes = [ val ] + BarCodes
    return BarCodes

def StoreQID(QID):
    TYP = (QID-1000) % 7

    dir = "/tmp/SDAPS/TYP_"+str(TYP)
    if not os.path.exists(dir):
        os.makedirs(dir)

    name = str(QID)+".tif"
    ndup = 0
    while os.path.exists(os.path.join(dir,name)):
        ndup += 1
        print "Error: Duplicate QID ", QID,str(ndup)
        name = QID+"_DUP_"+str(ndup)+".tif"

    rc = os.system("cp /tmp/SDAPS/A4.tif "+os.path.join(dir,name))


def StartTimer():
    global timer
    timer = int(round(time.time() * 1000))

def StopTimer(text):
    dt = int(round(time.time() * 1000)) - timer 
    print "%-10s %5d ms" % (text,dt)

def PDFtoTIFF(iA,iB):

    StartTimer()

    #StartTimer()
    Pages = ["A"+str(iA)+"R","A"+str(iA)+"L","B"+str(iB)+"R","B"+str(iB)+"L"]
    p = Pool(4)
    p.map(PDF2TIFF,Pages)
    p.close()
    #StopTimer("convert PDF -> TIFF:")



    Rotated = False

    # StartTimer()
    # check for QID Barcodes on AR.pdf
    os.system("tiffcrop -E l -U px -X 500 -Y 400 -m 3200,100,0,0 /tmp/SDAPS/ARbw.tif /tmp/SDAPS/QID.tif")
    BarCodes = GetBarCodes("/tmp/SDAPS/QID.tif")
    if len(BarCodes)==0:
        # try upside-down:
        os.system("mv /tmp/SDAPS/QID.tif /tmp/SDAPS/QID_.tif")
        os.system("tiffcrop -E r -U px -X 400 -Y 400 -m 0,0,3200,160 /tmp/SDAPS/ARbw.tif /tmp/SDAPS/QID.tif")
        BarCodes = GetBarCodes("/tmp/SDAPS/QID.tif")
        Rotated = True
        if len(BarCodes)==0:
            print "ERROR no QID BarCode found in Right-Half of /tmp/SDAPS/PassA/"+str(iA)+".pdf"
            sys.exit(-1)
    QID = int(BarCodes[0])

    if not Rotated:
        os.system("tiffcrop -E r -U px -X 600 -Y 400 -m 3200,0,0,200 /tmp/SDAPS/ARbw.tif /tmp/SDAPS/SID.tif")
    else:
        os.system("tiffcrop -E l -U px -X 600 -Y 400 -m 0,150,3200,0 /tmp/SDAPS/ARbw.tif /tmp/SDAPS/SID.tif")
    BarCodes = GetBarCodes("/tmp/SDAPS/SID.tif")
    if len(BarCodes)==0:
        print "ERROR no SID BarCode found in Right-Half of /tmp/SDAPS/PassA/"+str(iA)+".pdf"
        sys.exit(-1)
    SID = int(BarCodes[0][ 0:10])
    PID = int(BarCodes[0][10:14])

    #StopTimer("Read QID/SID BarCodes:")


    if not Rotated:
        if PID == 1:
            PageOrder = ["AR","BL","BR","AL"]
        else:
            PageOrder = ["BR","AL","AR","BL"]
    else:
        if PID == 4:
            PageOrder = ["AL","BR","BL","AR"]
        else:
            PageOrder = ["BL","AR","AL","BR"]



    #StartTimer()
    command = "tiffcrop"
    if Rotated:
        command = command + " -R 180"
    for Page in PageOrder:
        command = command + " /tmp/SDAPS/"+Page+"c.tif"
    command = command + " /tmp/SDAPS/A4.tif"
    os.system(command)
    #StopTimer("cat/rotate A4TIFFs into QID.tif:")

    #StartTimer()
    StoreQID(QID)
    #StopTimer("cp QID.tif to TYPdir:")

    
    print "%2d  SID: %10d     QID: %4d.%1d" %(iA,SID,QID,PID),
    StopTimer(" ")

# ============================
os.system("rm -rf /tmp/SDAPS/*")

Project = sys.argv[1]
ScanNumber = sys.argv[2]
if len(sys.argv)>3:
    ScanPasses = sys.argv[3:]
else:
    ScanPasses = [""]

PageCount = 0
NpagesPerFile = 0
timer = 0

if len(ScanPasses)==2:

    pdf_fileA = Project+"_Scans/Scan_"+ScanNumber+"A.pdf"
    if not os.path.exists(pdf_fileA):
        print "ERROR input file not found",pdf_fileA
        sys.exit(-1)

    pdf_fileB = Project+"_Scans/Scan_"+ScanNumber+"B.pdf"
    if not os.path.exists(pdf_fileB):
        print "ERROR input file not found",pdf_fileB
        sys.exit(-1)

    NpagesA = NumberOfPdfPages(pdf_fileA)  
    NpagesB = NumberOfPdfPages(pdf_fileB)  
    if NpagesA != NpagesB:
        print "ERROR PDF page number mismatch:",pdf_fileA,pdf_fileB,NpagesA,NpagesB
        sys.exit(-1)

    NQ = NpagesA
    print "Sort PDFs Npages =",NQ

    os.system("mkdir /tmp/SDAPS/PassA")
    os.system("pdftk "+pdf_fileA+" burst output /tmp/SDAPS/PassA/%d.pdf")
    os.system("mkdir /tmp/SDAPS/PassB")
    os.system("pdftk "+pdf_fileB+" burst output /tmp/SDAPS/PassB/%d.pdf")

    for iQ in range(1,NQ+1):
        PDFtoTIFF(iQ,NQ-iQ+1)

    
