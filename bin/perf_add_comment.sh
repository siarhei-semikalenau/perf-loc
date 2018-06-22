#!/usr/bin/env bash

HOST=http://192.168.99.100:8080

SCRIPTPATH=$( cd "$(dirname "$0")" ; pwd -P )

DT=`date +%Y%m%d-%H%M%S`

usage () {
	echo "Usage: $0 1|5 [base|compare]"
	echo "	1|5 - number of virtual users"
	echo "	base - generate baseline file"
	echo "	compare - comparing current test with baseline and output results"
	echo "		1st column - request name"
	echo "		2nd column - baseline response time (in ms)"
	echo "		3rd column - test response time (in ms)"
	echo "		4th column - difference (in ms). Negative better than baseline, positive - worse"
	exit 0
}

if [[ "$#" -lt 1 ]]; then 
  usage
fi

NUMCL=$1
case $NUMCL in
	1)
		CLIENTS=1
		RUNTIME=20s
		shift
		;;

	5)
		CLIENTS=5
		RUNTIME=120s
		shift
		;;

	*)
 		usage
		;;

esac

OP=$1
case "$OP" in
	base)
		CSVF=${SCRIPTPATH}/perf_add_comment_${CLIENTS}_base
		LOGF=${SCRIPTPATH}/perf_add_comment_${CLIENTS}_base.log
		;;

	compare|"")
		CSVF=${SCRIPTPATH}/perf_add_comment_${CLIENTS}_${DT}
		BASEF=${SCRIPTPATH}/perf_add_comment_${CLIENTS}_base
		LOGF=${SCRIPTPATH}/perf_add_comment_${CLIENTS}_${DT}.log
		;;

	*)
		usage
		;;
esac

locust --locustfile=${SCRIPTPATH}/locust-test.py --host=${HOST} --no-web --clients=${CLIENTS} --hatch-rate=1 --run-time=${RUNTIME} --loglevel=ERROR --logfile=${LOGF} --only-summary --csv=${CSVF}
ret=$?

if [ $ret -ne 0 ]; then
	echo Fail
	exit 2
fi

if [[ "$OP" == "compare" ]]; then
	if [[ ! -r ${BASEF}_requests.csv ]]; then
		echo Baseline file doesn''t exist or not readable
	else 
		paste -d, <(cut -d, -f2,6 <(tail -n +2 <(head -n -1 ${BASEF}_requests.csv))) <(cut -d, -f6 <(tail -n +2 <(head -n -1 ${CSVF}_requests.csv))) | awk -F, '{OFS=","; print $1,$2,$3,$3-$2}' > ${CSVF}_compare.csv
		cat ${CSVF}_compare.csv
	fi
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
