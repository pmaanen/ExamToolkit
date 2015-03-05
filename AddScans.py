#!/usr/bin/python
import sys, os, subprocess, glob, StringIO


# ============================

ProjectBase = sys.argv[1]
#if sys.argv<4:
sdaps="sdaps"
#else:
#	sdaps=sys.argv[2]
ScansDir = ProjectBase+"_Scans"

os.system("cp /tmp/SDAPS/*.log "+ScansDir+"/")

Dirs  = glob.glob("/tmp/SDAPS/TYP_?")

for Dir in Dirs:
    Typ = Dir.split("_")[1]
    Files = glob.glob(os.path.join(Dir,"*.tif"))
    for FilePath in Files:

        File = os.path.basename(FilePath)
        QID  = File[0:4]
        ndup = 0
        while os.path.exists(os.path.join(ScansDir,File)):
            ndup += 1
            print "Error: Duplicate QID ",QID,str(ndup)
            File = QID+"_DUP_"+str(ndup)+".tif"

        os.system("cp "+FilePath+" "+os.path.join(ScansDir,File))
        os.system(sdaps+" "+ProjectBase+"_"+Typ+" add --no-copy "+os.path.join(ScansDir,File)+" > /dev/null")


