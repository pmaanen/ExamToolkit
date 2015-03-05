#!/bin/bash


Name=$1
NTyp=$2
I1=$3
I2=$4
Nmax=$(( $NTyp - 1 ))

echo $Name  $NTyp $Nmax $I1 $I2

for i in `seq $I1 $I2`
do
   for typ in `seq 0 $Nmax`
   do 
      ./src/A3print.bash $Name $typ $i 
      sleep 12
   done
done

echo -e "\007"
sleep 1
echo -e "\007"
sleep 1
echo -e "\007"


exit 0
