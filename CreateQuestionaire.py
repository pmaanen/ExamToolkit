#!/usr/bin/python

import sys, os
parse="/home/pmaanen/Schreibtisch/src/parse.py"
sdaps="/home/pmaanen/src/sdaps-1.1.7/sdaps.py"
def CreateIDlist(Name,Typ,N):
    f = open(Name+"_"+Typ+".IDlist", 'w')
    for i in range(N):
        ID = 1000 + int(Typ) + 7*i
        f.write(str(ID)+"\n")
    f.close()


def CreateTeXfile(Name,Typ):
    TeXfile = Name + "_" + Typ + ".tex"
    os.system("cp " + Name + "/header.tex " + TeXfile)
    f = open(TeXfile, 'a')
    for i in range(10):
        os.system(parse+" " + Name + "/A" + str(i+1) + " " + Typ + " " + str(i+1))
        if i % 3 == 1:
            f.write("\\newpage\\vspace*{-2.6cm}\n")
        f.write("\n    \\vspace*{2mm}\\section{}\\vspace*{-2mm}\n")
        f.write("\n    \\input{A"+str(i+1)+"_"+Typ +"}\n")
    f.write("\n  \\end{questionnaire}\n")
    f.write("\n\\end{document}\n")


# =================

Name  = sys.argv[1]
Typ   = sys.argv[2]
N     = sys.argv[3]

TypName = Name + "_" + Typ

print "rm -rf " + TypName
os.system("rm -rf " + TypName)

print "CreateTeXfile(%s,%s)" % (Name,Typ)
CreateTeXfile(Name,Typ)

print "SDAPS",TypName," setup_tex"
command = sdaps+" " + TypName + " setup_tex " + TypName + ".tex"
for i in range(10):
    command = command + " -a " + Name + "/A"+str(i+1)+"_" + str(Typ) + ".tex"
os.system(command)


CreateIDlist(Name,Typ,int(N))
os.system(sdaps+" "  + TypName + " stamp -f "  + TypName + ".IDlist -o " + TypName + "_A4.pdf" )

