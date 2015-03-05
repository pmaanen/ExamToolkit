#!/usr/bin/python
import sys, os, subprocess, glob, StringIO, collections, math
from ROOT import gROOT, TCanvas, TH1F, TH2F, gStyle

def ReadCorrectMarkFiles(ProjectBase,Typ):
    for i in range(1,11):
        QuestionMarks = []
        ifile = open(ProjectBase+"/A"+str(i)+"_"+Typ+".pat",  "r")
        lines = ifile.readlines()
        ifile.close()
        for line in lines:
            QuestionMarks.append(line.split())
        CorrectMarks.append(QuestionMarks)

def CheckCSVheader(line):

    ColumnHeaders = line[0:-2].split(",")

    def CheckColumn(iColumn,text):
        if ColumnHeaders[iColumn] != text:
            print "ERROR Column %d is not |%s| but |%s|" % (iColumn,text,ColumnHeaders[iColumn])
            return -1
        return 0

    CheckColumn(0,"questionnaire_id")
    CheckColumn(1,"global_id")

    # Questionnaire Header (FreeForm Text Fields):
    for i in range(1,5+1):
        if CheckColumn(1+i,"0_"+str(i)+"_0") != 0:
            return -1

    # Questionnaire Header (PruefNr):
    for i in range(4):
        for j in range(9):
            if CheckColumn(5+2+9*i+j,"0_6_"+str(i+1)+"_"+str(j)) != 0:
                return -1

    # Questionnaire Header (FreeForm Sicht-Korrektur-Feld):
    if CheckColumn(1+5+4*9+1,"0_7_0") != 0:
        return -1

    # Questionnaire with 10 Problems x 4 Questions with N options 
    i = 2+5+4*9+1
    for P in range(10):
        for Q in range(4):
            for O in range(len(CorrectMarks[P][Q])):
                text = str(P+1)+"_"+str(Q+1)+"_"+str(O) if Q<2 else str(P+1)+"_"+str(Q+1)+"_1_"+str(O)
                if CheckColumn(i,text) != 0:
                    return -1
                i += 1
    return 0

def GetPruefNr(Columns):

    global PruefNr
    PruefNr = ""

    def GetDigit(i,Columns):
        Digit = "-"
        CheckedMarks = collections.defaultdict(list)
        for O in range(9):
            # count all filled in mark types :
            # 1: empty
            # 2: crossed
            # 3: filled
            # negative: detection probability < 0.575
            CheckedMark = Columns[O]
            CheckedMarks[CheckedMark].append(O+1)

        if len(CheckedMarks["2"]) == 1:
            return str(CheckedMarks["2"][0])

        if len(CheckedMarks["2"]) > 1:
            return "X"

        if len(CheckedMarks["-3"])+len(CheckedMarks["-2"])+len(CheckedMarks["-1"])+len(CheckedMarks["3"]) == 0:
            return "-"

        if len(CheckedMarks["-3"])+len(CheckedMarks["-2"])+len(CheckedMarks["-1"])+len(CheckedMarks["3"]) == 1:
            return str((CheckedMarks["-3"]+CheckedMarks["-2"]+CheckedMarks["-1"]+CheckedMarks["3"])[0])

        if len(CheckedMarks["-3"])+len(CheckedMarks["-2"])+len(CheckedMarks["-1"]) == 1:
            return str((CheckedMarks["-3"]+CheckedMarks["-2"]+CheckedMarks["-1"])[0])

        return "?"
        
    BadPruefNr = False
    GoodDigits = "123456789" 
    for i in range(4):
        Digit = GetDigit(i,Columns[9*i:9*(i+1)])
        PruefNr = PruefNr + Digit
        if not Digit in GoodDigits:
            BadPruefNr = True

    global GUIcheck
    if PruefNr == "----" :
        print >>GUIcheck, "Bad PruefNr for QID",int(GradeLine.split()[0]),PruefNr



def CheckSichtKontrolle(Columns):

    global GUIcheck
    if Columns[0] == '1':
        print >>GUIcheck, "SichtKontrolle for QID",int(GradeLine.split()[0])


def GradeQuestion(P,Q,Columns):

    global GradeLine
    global Warnings
    global GUIcheck

    if DEBUG > 1:
        print "\nGradeQuestion P,Q =",P+1,Q+1,
        print "Correct:",CorrectMarks[P][Q],
        print "Checked:",Columns[0:len(CorrectMarks[P][Q])],

    CheckCounters = collections.Counter()
    for O in range(len(CorrectMarks[P][Q])):
        # count all filled in mark types :
        # 1: empty
        # 2: crossed
        # 3: filled
        # negative: detection probability < 0.575
        CheckedMark = Columns[O]
        CheckCounters[CheckedMark] += 1

    SingleBadBox = (CheckCounters["-1"]+CheckCounters["-2"]+CheckCounters["-3"]==1) and (CheckCounters["2"]==0)
    if SingleBadBox:
        print >>Warnings, "single bad  box for QID,P,Q",int(GradeLine.split()[0]),P+1,Q+1

    SingleBadOrFilledBox = (CheckCounters["-1"]+CheckCounters["-2"]+CheckCounters["-3"]+CheckCounters["3"]==1) and (CheckCounters["2"]==0)
    if SingleBadOrFilledBox:
        print >>Warnings, "single bad or filled box for QID,P,Q",int(GradeLine.split()[0]),P+1,Q+1

    StrictGradeCounters = collections.Counter()
    SloppyGradeCounters = collections.Counter()

    AutoCorrected = False

    for O in range(len(CorrectMarks[P][Q])):

        CheckedMark = Columns[O]
        if (SingleBadBox and int(CheckedMark)<0) or (SingleBadOrFilledBox and CheckedMark!="1") :
            # Auto Correct to "checked"
            CheckedMark = "2"
            AutoCorrected = True

        # count all grading pattern types - except "?"
        CorrectMark =  CorrectMarks[P][Q][O][0]
        # ?: does not matter
        # O: must be empty
        # X: must be crossed
        # A,B,... OptionGroups, must be crossed
        if CorrectMark != "?":

            StrictGradeCounters[CorrectMark] += 1
            SloppyGradeCounters[CorrectMark] += 1


            # subtract correct choices, so counter==0 for correct pattern

            # strict grading:
            strict_cross = (CheckedMark=="2")
            strict_empty = (CheckedMark=="1" or CheckedMark=="3")

            if CorrectMark=="O":
                if strict_empty:                               # "O"        must be empty, or filled
                    StrictGradeCounters[CorrectMark] -= 1
                if not strict_cross:                           # "O"        must not be crossed
                    SloppyGradeCounters[CorrectMark] -= 1
            else: 
                if strict_cross:                               # "X,A,B..." must be crossed
                    StrictGradeCounters[CorrectMark] -= 1
                if not strict_empty:                           # "X,A,B..." must not be empty
                    SloppyGradeCounters[CorrectMark] -= 1


    # evaluate patterns
    # "X", "O"   - if present - must all be correct
    # "A", "B".. - if present - need at least 1 correct alternative
    XOcounter = 0
    ABpresent = 0

    StrictXOcorrect = 0
    StrictABcorrect = 0
    GradePattern = "Strict: "
    for pat in StrictGradeCounters:
        
        GradePattern += pat
        GradePattern += "+" if StrictGradeCounters[pat]==0 else "-"

        if pat=="X" or pat=="O":
            XOcounter += 1
            if StrictGradeCounters[pat]==0:
                StrictXOcorrect += 1
        else:
            ABpresent = 1
            if StrictGradeCounters[pat]==0:
                StrictABcorrect += 1


    SloppyXOcorrect = 0
    SloppyABcorrect = 0
    GradePattern += "    Sloppy: "
    for pat in SloppyGradeCounters:
        
        GradePattern += pat
        GradePattern += "+" if SloppyGradeCounters[pat]==0 else "-"

        if pat=="X" or pat=="O":
            if SloppyGradeCounters[pat]==0:
                SloppyXOcorrect += 1
        else:
            if SloppyGradeCounters[pat]==0:
                SloppyABcorrect += 1


    if DEBUG>1:
        print GradePattern,

    if StrictXOcorrect==XOcounter and StrictABcorrect>=ABpresent:
        strict_result = " 1"
    else:
        strict_result = " 0"

    if SloppyXOcorrect==XOcounter and SloppyABcorrect>=ABpresent:
        sloppy_result = " 1"
    else:
        sloppy_result = " 0"

    if CheckCounters["2"]+CheckCounters["3"]+CheckCounters["-3"]+CheckCounters["-2"] == 0:
        strict_result = " -"

    GradeLine += strict_result

    # check for Problems:
    if CheckCounters["2"] == 0 and strict_result == " 0" and not AutoCorrected:
        if CheckCounters["3"]+CheckCounters["-1"]+CheckCounters["-2"]+CheckCounters["-3"] > 1:
            print >>GUIcheck, "only bad boxes for QID,P,Q",int(GradeLine.split()[0]),P+1,Q+1
    if sloppy_result == " 1" and strict_result == " 0":
        print >>GUIcheck, "sloppy point   for QID,P,Q",int(GradeLine.split()[0]),P+1,Q+1
    if sloppy_result == " 0" and strict_result == " 1":
        print >>GUIcheck, "sloppy wrong   for QID,P,Q",int(GradeLine.split()[0]),P+1,Q+1

    if CheckCounters["-1"] > 0:
        print >>Warnings, "low -1 detection probability for QID,P,Q",int(GradeLine.split()[0]),P+1,Q+1
    if CheckCounters["-2"] > 0:
        print >>Warnings, "low -2 detection probability for QID,P,Q",int(GradeLine.split()[0]),P+1,Q+1
    if CheckCounters["-3"] > 0:
        print >>Warnings, "low -3 detection probability for QID,P,Q",int(GradeLine.split()[0]),P+1,Q+1


    return -1 if strict_result == " -" else int(strict_result)

def GradeProblem(P,Columns):
    if DEBUG > 3:
        print "GradeProblem P =",P

    global GradeLine
    GradeLine += "    "
    C = 0
    S = 0
    T = False 
    for Q in range(4):
        G  = GradeQuestion(P,Q,Columns[C:])
        if G >= 0:
            S += G
            T = True
        C += len(CorrectMarks[P][Q])

    if DEBUG>1:
        print "C:",C

    global PPoints
    PPoints[P] = S if T else -1

    return C

def GradeQID(Columns):

    global Warnings
    global GUIcheck

    GetPruefNr(Columns[5:4*9+5])
    global GradeLine
    GradeLine = GradeLine + " " + PruefNr

    CheckSichtKontrolle(Columns[5+4*9:5+4*9+1])

    iCol   = 5+4*9+1
    for P in range(10):
        if DEBUG>3:
            print "GradeQID P,iCol =",P,iCol
        iCol  += GradeProblem(P,Columns[iCol:])

    QID = int(GradeLine.split()[0])
    Typ = (QID-1000)%7
    Sum = sum(filter(lambda p: p>=0,PPoints))
    global DHistos, SHistos
    SHistos[Typ].Fill(Sum)
    for P in range(10):
        if PPoints[P] >= 0:
            DHistos[Typ][P].Fill(Sum,PPoints[P])

    Problems = Warnings.getvalue()
    if len(Problems)>0:
        print "Warnings for QID",GradeLine.split()[0]
        print Problems
        Warnings.truncate(0)

    Problems = GUIcheck.getvalue()
    if len(Problems)>0:
        QID = GradeLine.split()[0]
        Typ = str((int(QID)-1000)%7)

        print ""
        print "---------------------------------"
        print "GUIcheck for QID/TYP",QID,Typ
        print Problems
        GUIcheck.truncate(0)
        command = "./sdaps.py " + ProjectBase + "_" + Typ + " gui -f \"questionnaire_id=='" + QID + "'\""
        if DEBUG == 0:
            os.system(command)
    
def GradeCSV(CSVfile):

    global DEBUG

    print "grade file",CSVfile

    ifile = open(CSVfile,  "r")
    lines = ifile.readlines()
    ifile.close()

    if len(lines)<2:
        print "ERROR empty csv file ", CSVfile
        sys.exit(-1)

    if CheckCSVheader(lines[0]) != 0:
        print "ERROR in header of csv file ", CSVfile
        sys.exit(-1)

    global GradeLine
    for line in lines[1:]:
        QID = line[0:-2].split(",")[0]

#        if line[0:-2].split(",")[12] != "0":
#            print "Grade QID ",QID
#            DEBUG = 2
#        else:
#            DEBUG = 0

        GradeLine = QID
        GradeQID(line[0:-2].split(",")[2:])

        print GradeLine,"   Sum:",sum(filter(lambda p: p>=0,PPoints))

# ============================

ProjectBase = sys.argv[1]

Dirs  = glob.glob(ProjectBase+"_?")

GradeLine = ""
DEBUG = -1
if len(sys.argv)>2:
    DEBUG = int(sys.argv[2])

PPoints = range(10)  # list with 10 entries
SHistos = []
DHistos = []
PruefNr = ""

for Typ in range(2):

    hname  = "S_"+str(Typ)
    htitle = "Total Points for Typ "+str(Typ)
    SHistos.append ( TH1F( hname, htitle, 41, -0.5 , 40.5 ) )
    
    DHistos.append([])
    for Problem in range(10):
        hname  = "D_"+str(Problem+1)+"_"+str(Typ)
        htitle = "Discrimination of Problem "+str(Problem+1)+" Typ "+str(Typ)
        DHistos[Typ].append( TH2F( hname, htitle, 41, -0.5 , 40.5, 5, -0.5, 4.5 ) )



Warnings = StringIO.StringIO()
GUIcheck = StringIO.StringIO()

for Dir in Dirs:
    Typ = Dir.split("_")[1]

    CorrectMarks = []
    ReadCorrectMarkFiles(ProjectBase,Typ)

    CSVfile = sorted(glob.glob(os.path.join(Dir,"*.csv")))[-1]
    GradeCSV(CSVfile)

Warnings.close()
GUIcheck.close()

c1 = TCanvas()
gStyle.SetOptStat(1110)

SumHisto =  TH1F( "Total Points", "Total Points", 41, -0.5 , 40.5 )
SumHisto.Add(SHistos[0],SHistos[1])
SumHisto.Draw()
c1.Print("GradeStats.pdf(","pdf")
c1.Clear()

for i in range(10):

    c1.Divide(2,2)
    c1.cd(1)
    DHistos[0][i].Draw("colz")
    c1.cd(3)
    DHistos[1][i].Draw("colz")
    c1.cd(2)
    Projection = DHistos[0][i].ProjectionY()
    Projection.SetMinimum(0)
    Projection.Draw()
    c1.cd(4)
    Projection = DHistos[1][i].ProjectionY()
    Projection.SetMinimum(0)
    Projection.Draw()
    c1.Print("GradeStats.pdf","pdf")
    c1.Clear()
    
    N = DHistos[0][i].GetEntries()
    R = DHistos[0][i].GetCorrelationFactor()
    if N>2:
        eR = math.sqrt(1-R*R)/math.sqrt(N-2) 
    else:
        eR = 0.0
    print "Problem",i+1," Typ 0 N,R,eR:", N,R,eR

    N = DHistos[1][i].GetEntries()
    R = DHistos[1][i].GetCorrelationFactor()
    if N>2:
        eR = math.sqrt(1-R*R)/math.sqrt(N-2) 
    else:
        eR = 0.0
    print "Problem",i+1," Typ 1 N,R,eR:", N,R,eR
    print " "


c1.Print("GradeStats.pdf)","pdf")

