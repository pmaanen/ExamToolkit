#!/bin/bash

Printer="1b-28c210-1-bw"

Name=$1
Typ=$2
I=$3

Offset=$(( 4 * $I ))
P1=$(( $Offset - 0 ))
P2=$(( $Offset - 3 ))
P3=$(( $Offset - 2 ))
P4=$(( $Offset - 1 ))

pages=$P1","$P2","$P3","$P4

pdfjam $Name"_"$Typ"_A4.pdf" "$pages" --nup 2x1 --a3paper --landscape --outfile A3tmp.pdf
# lpr -P$Printer -o MediaSize=A3 A3tmp.pdf

let "IM1 =   $I - 1"
let "QID = $IM1 * 7"
let "QID = $QID + $Typ"
let "QID = $QID + 1000"

if [ $? -eq 0 ]; then
    echo ""
    echo "lpr OK   for QID = $QID" `date`
    echo "lpr OK   for QID = $QID" `date` >> $Name.printlog
else
    echo ""
    echo "lpr FAIL for Name/Typ/I $Name $Typ $I   QID = $QID" `date`
fi

# rm A3tmp.pdf

exit 0
