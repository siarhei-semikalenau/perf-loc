#!/usr/bin/env bash

URL=http://192.168.99.100:8080

if [[ "$#" -lt 1 ]]; then 
  echo $"Usage: $0 1|5"
  exit 1
fi

NUMCL=$1
case $NUMCL in
	1)
	CLIENTS=1
	RUNTIME=20s
	;;

	5)
	CLIENTS=5
	RUNTIME=120s
	;;

	*)
	echo $"Usage: $0 1|5"
 	exit 1
	;;

esac

SCRIPTPATH=$( cd "$(dirname "$0")" ; pwd -P )

DT=`date +%Y%m%d-%H%M%S`
LOGF=${SCRIPTPATH}/perf_add_comment_${DT}.log
CSVF=${SCRIPTPATH}/perf_add_comment_${DT}

locust --locustfile=${SCRIPTPATH}/locust-test.py --host=${URL} --no-web --clients=${CLIENTS} --hatch-rate=1 --run-time=${RUNTIME} --loglevel=ERROR --logfile=${LOGF} --only-summary --csv=${CSVF}
ret=$?

if [ $ret -ne 0 ]; then
	echo Fail
	exit 2
fi

f=$(grep '040\.' ${CSVF}_requests.csv | cut -d, -f6)
s=$(( ${f//$'\n'/+} ))
echo $s
if [ $s -lt 5000 ]; then
	echo Pass
	exit 0
else
	echo Fail
	exit 1
fi

