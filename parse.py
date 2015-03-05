#!/usr/bin/python


# todo
#
# eval (LaTeXCalc) 
# - replace only variable names containing "{"
# - unit conversion in python - not LaTeX


import sys, os, StringIO, random

from math import log10, floor, pow

suffixes = { "deg" : "(\\pi/180)",
             "kmh" : "(1/3.6)",
               "d" : "0.1",
               "c" : "0.01",
               "m" : "0.001",
              "mu" : "10^{-6}",
               "n" : "10^{-9}",
               "p" : "10^{-12}",
               "f" : "10^{-15}",
               "h" : "100",
               "k" : "1000",
               "M" : "10^{6}",
               "G" : "10^{9}",
               "T" : "10^{12}",
               "P" : "10^{15}"
           }


def roundc_to_n(v,n):
    print v,
    # split into digits + exponent:
    digits = ""
    sign = ""
    d = 0
    e = 0 
    numbers = "123456789"
    i = 0
    if v[0] == "-":
        sign = "-"
        i = 1
    while i < len(v):
        c = v[i]
        if c in numbers:
            digits = digits + c
            numbers = "0123456789"
            e = e - d
        elif c == ".":
            d = 1
        elif c == "0":
            e = e - d
        elif c == "e":
            e = e + int(v[i+1:])
            break
        i = i + 1

    # round to n digits, adjust exponent:
    if len(digits) > n:
        en = e + len(digits) - n
        dn = digits[0:n]
        if digits[n] in "56789":
            dn = str(int(dn)+1)
            if len(dn)>n:
                dn = dn[0:n]
                en = en + 1
        
    # shift to engineering exponent i*3
    e3 = 0
    while -en >= n:
        en = en + 3
        e3 = e3 - 3
    while en > 0:
        en = en - 3
        e3 = e3 + 3
    result = sign+dn[0:n+en]+"."+dn[n+en:]
    if e3 != 0:
        result = result + "e" + str(e3)

    return result

def round_to_n(v,n):
    sign = "" 
    if v.lstrip()[0] == "-":
        sign = "-"
    x = abs(float(v))
    if x > 0.0:
        e3 = int(floor(log10(x)/3))
        if e3>0 and n > int(floor(log10(x))):
            e3=0
        m = x / pow(10,3*e3)
        format = "%." + str(int(n-1-floor(log10(m)))) + "f"
    else:
        e3 = 0
        m = 0.0
        format = "%." + str(n-1) + "f"
    output = StringIO.StringIO()
    output.write(format % m)
    if e3 != 0:
        output.write("${\cdot}10^{" + str(3*e3) + "}$")
    result = sign+output.getvalue()
    output.close()
    return result


def eval(exp,werte):

    exp_ = str(exp)
    ofile = open("eval.tex" , "w")
    ofile.write("\\begin{document}\n")
    for i,arg in enumerate(werte):
        var = arg.split("=")[0]
        val = arg.split("=")[1]
        suf = val.split("%")[-1]

        if suf == "dB":
            val = "10^{" + val.split("%")[0] + "/10}" 
        elif suf == "Bel":
            val = "10^{" + val.split("%")[0] + "}" 
        elif suf == "dBn":
            val = "e^{" + val.split("%")[0] + "/10}" 
        elif suf in suffixes:
            val = val.split("%")[0] + "*" + suffixes[suf]

        if len(var) == 1:
            var_ = var
        else:
            var_ = "\\Upsilon_"+chr(i+97)
            exp_ = exp_.replace(var,var_)

        ofile.write("$ "+var_+" = \\varcalc{"+var_+"}{"+val.replace(",",".")+"}$\n")

    suf = exp_.split("%")[-1]
    if suf == "dB":
        exp_ = "10*\log(" + exp_.split("%")[0] + ")"
    elif suf == "Bel":
        exp_ = "\log(" + exp_.split("%")[0] + ")"
    elif suf == "dBn":
        exp_ = "10*\ln(" + exp_.split("%")[0] + ")"
    elif suf in suffixes:
        exp_ = "(" + exp_.split("%")[0] + ")/" + suffixes[suf]
    ofile.write("$ \solver{" + exp_.replace(",",".") + " }$ = \\answer\n")
    ofile.write("\\panswer\n")

    ofile.write("\\end{document}\n")

    ofile.close()

    latexcalc = os.popen("latexcalc eval.tex").read().split("\n") 
    result = latexcalc[-3]
    return result


def shuffle(patterns):
    shuffled_index = []
    indices = []
    ilast = -1
    for i,pat in enumerate(patterns):
        if pat[-1] == "v":
            ilast = i
            patterns[i] = patterns[i][0:-1]
        elif pat != "-":
            indices.append(i)
    while len(indices) > 0:
        i = random.randint(0,len(indices)-1)
        shuffled_index.append(indices[i])
        del indices[i]
    if ilast != -1:
        shuffled_index.append(ilast)
    return shuffled_index

def Dummy(line):
    return ""

def Add_Variable(line):
    tag = line.split()[0]
    if tag != "INIT" and tag != "EXIT":
        #print("Add tag/values: " + line),
        tag = line.split("=")[0].split()[0]
        values = line.split("=")[1]
        variables[tag] = values.split()

def Replace_Variables(line):
    newline = line
    while newline.find("\\value{") >= 0:
        i1 = newline.find("\\value{")
        i2 = newline.find("}",i1)
        tag = newline[i1+7:i2].split()[0]
        val = variables[tag][type]
        newline = newline[0:i1]+val+newline[i2+1:]
        print "replace:",tag," =",val
    return newline

def Add_Text(line):
    tag = line.split()[0]
    if tag == "INIT":
        texfile.write("\\vspace*{-0.0cm}\n")
    elif tag == "EXIT":
        texfile.write("\n")
    else:
        texfile.write(Replace_Variables(line))

def Add_Ansatz(line):
    global patterns,ansaetze
    tag = line.split()[0]
    if tag == "INIT":
        ansaetze = []
        texfile.write("\\vspace*{-0.2cm}\n")
        texfile.write("\\begin{multicols}{2}\n\n")
        texfile.write("\\begin{choicequestion}[1]{Ansatz:\\vspace*{-0.2cm}}\n")
    elif tag == "EXIT":
        for i in shuffle(patterns):
            print patterns[i],ansaetze[i]
            texfile.write("  \\choiceitem["+patterns[i]+"]{"+ansaetze[i]+"}\n")
            patfile.write(" "+patterns[i]+str(i))
        patfile.write("\n")
        texfile.write("\\end{choicequestion}\n")
    else:
        mark  = line.split()[0]
        formula = line[0:-1].split(" ",1)[-1]
        ansaetze.append(formula)
        patterns.append(mark)

def Add_EndFormel(line):
    global patterns, endformeln
    tag = line.split()[0]
    if tag == "INIT":
        endformeln =  []
        texfile.write("\n\\begin{choicequestion}[1]{Endformel:\\vspace*{-0.2cm}}\n")
    elif tag == "EXIT":
        for i in shuffle(patterns):
            print patterns[i],endformeln[i]
            texfile.write("  \\choiceitem["+patterns[i]+"]{"+endformeln[i]+"}\n")
            patfile.write(" "+patterns[i]+str(i))
        patfile.write("\n")
        texfile.write("\\end{choicequestion}\n")
        texfile.write("\n")
        texfile.write("\\end{multicols}\n")
    else:
        mark  = line.split()[0]
        formula = line[0:-1].split(" ",1)[-1]
        endformeln.append(formula)
        patterns.append(mark)
        if mark == "-":
            print mark+" "+formula

def Add_Werte(line):
    global precision, patterns, zahlenwerte,comments
    tag = line.split()[0].split(":")[0]
    if tag == "INIT":
        zahlenwerte = []
        comments = []
        precision = 4
        if len(line.split()[0].split(":")) > 1:
            precision = int(line.split()[0].split(":")[1])
        unit = line[0:-1].split(" ",1)[-1]
        texfile.write("\\begin{choicegroup}{Zahlenwert")
        if unit != "INIT":
            texfile.write(" " + unit)
        texfile.write(":\\vspace*{-1.0cm}}\n")
    elif tag == "EXIT":
        for i in shuffle(patterns):
            print patterns[i],zahlenwerte[i].replace(".",","),comments[i]
            texfile.write("  \\groupaddchoice["+patterns[i]+"]{\\hspace*{-0.1cm}"+zahlenwerte[i].replace(".",",")+"\\hspace*{-0.1cm}}\n")
            patfile.write(" "+patterns[i]+str(i))
        patfile.write("\n")
        texfile.write("  \\choiceline{}\n")
        texfile.write("\\end{choicegroup}\n")
    else:
        mark  = line.split()[0]
        wert = line[0:-1].split()[1]
        comment = ""
        if wert == "Formel":
            iform = line[0:-1].split()[2].split("%")[0]
            unit  = line[0:-1].split()[2].split("%")[-1]
            #print "iform: " + iform
            formel = endformeln[int(iform)-1]
            if unit != iform:
                formel = formel + "%" + unit
            wertepaare = []
            for paar in line[0:-1].split()[3:]:
                nam = paar.split("=")[0]
                tag = paar.split("=")[1].split("%")[0]
                suf = paar.split("=")[1].split("%")[-1]

                val = tag
                for v in variables:
                    val = val.replace(v,variables[v][type])

#                if tag in variables:
#                    val =  variables[tag][type]
#                else:
#                    val = tag

                # print " nam tag suf val " + nam + " " + tag + " " + suf + " " + val
                if suf != tag:
                    wertepaare.append(nam+"="+val+"%"+suf)
                else:
                    wertepaare.append(nam+"="+val)
            wert = eval(formel,wertepaare)
            comment = wert + " " + " ".join(wertepaare) + " " +formel
            wert = round_to_n(wert,precision)
        zahlenwerte.append(wert)
        comments.append(comment)
        patterns.append(mark)


def Add_Einheiten(line):
    global patterns, einheiten
    tag = line.split()[0]
    if tag == "INIT":
        einheiten = []
        texfile.write("\\begin{choicegroup}{Einheit:\\vspace*{-1.0cm}}\n")
    elif line == "EXIT":
        for i in shuffle(patterns):
            print patterns[i],einheiten[i]
            texfile.write("  \\groupaddchoice["+patterns[i]+"]{\\hspace*{-0.1cm}"+einheiten[i]+"\\hspace*{-0.1cm}}\n")
            patfile.write(" "+patterns[i]+str(i))
        texfile.write("  \\choiceline{}\n")
        texfile.write("\\end{choicegroup}\n")
    else:
        mark  = line.split()[0]
        unit  = line[0:-1].split(" ",1)[1]
        einheiten.append(unit)
        patterns.append(mark)


def Add_Loesung(line):
    tag = line.split()[0]
    if tag == "INIT":
        mltexfile.write("\n")
    elif tag == "EXIT":
        mltexfile.write("\n")
    else:
        mltexfile.write(line)


#-------------------------------------------------------------------

basename = sys.argv[1]
type =  int(sys.argv[2])
seed =   int(sys.argv[3])

random.seed(10*seed+type)

texfile = open(basename+"_"+str(type)+".tex", "w")
patfile = open(basename+"_"+str(type)+".pat", "w")
mltexfile = open(basename+"_"+str(type)+"_ML.tex", "w")


ifile = open(basename+".in",  "r")
lines = ifile.readlines()
ifile.close()

process = {"END" :       Dummy,
           "Variablen" : Add_Variable,
           "Text" :      Add_Text,
           "Ansatz" :    Add_Ansatz,
           "EndFormel" : Add_EndFormel,
           "Wert" :      Add_Werte,
           "Einheit" :   Add_Einheiten,
           "Loesung" :   Add_Loesung
          }

variables = {}
ansaetze = []
endformeln = []
zahlenwerte = []
comments = []
einheiten = []
patterns = []

precision = 4

mode = "END"
for line in lines:

    if line.lstrip() == "" or line.split()[0] == "#":
        continue

    if line[0] == "#":
        process[mode]("EXIT")
        mode = line[1:].split()[0].split(":")[0]
        sufx = line[1:].split()[0].split(":")[1]
        unit = line.split(" ",1)[1] if len(line.split()) > 1 else ""
        tag = "INIT"
        patterns = []
        if sufx != "":
            tag = tag + ":" + sufx
        tag = tag + " " + unit
        print ("\n%s" % line),
        process[mode](tag)
        continue

    process[mode](line)

texfile.write("\\vspace*{-0.5cm}\n")
texfile.close()
patfile.write("\n")
patfile.close()
