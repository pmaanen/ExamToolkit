#!/usr/bin/python

import sys, os

def CreateTeXfile(Name,Ntyp):
    TeXfile = Name + "_ML.tex"
    os.system("cp " + Name + "/mlheader.tex " + TeXfile)
    f = open(TeXfile, 'a')
    for i in range(10):
        f.write("\\newpage\\vspace*{-2.6cm}\n")
        f.write("\n    \\vspace*{2mm}\\section{}\\vspace*{-2mm}\n")
        for j in range(int(Ntyp)):
            f.write("\n    \\input{../"+Name+"/A"+str(i+1)+"_"+str(j)+"}\n")
            f.write("\n    \\vspace*{5mm}\n")
        f.write("\n    \\input{../"+Name+"/A"+str(i+1)+"_0_ML}\n")
    f.write("\n  \\end{questionnaire}\n")
    f.write("\n\\end{document}\n")


# =================

Name  = sys.argv[1]
NTyp  = sys.argv[2]

TypName = Name + "_ML"

print "rm -rf " + TypName
os.system("rm -rf " + TypName)

print "CreateTeXfile(%s,%s)" % (Name,NTyp)
CreateTeXfile(Name,NTyp)

print "SDAPS",TypName," setup_tex"
command = "sdaps " + TypName + " setup_tex " + TypName + ".tex"
os.system(command)

os.system("cp "+Name+"_ML/questionnaire.pdf "+Name+"_ML_A4.pdf")
