#!/bin/bash
###--------------------------------------------------------
ver="1.2.0"
usage()
{
  cat << EOF
USAGE: 
  	MRS_tool.sh

	Version: $ver
	
	Extracts & sorts P-files

COMPULSORY:
	-d	[ Directory ] containing P-files
OR
	-pd	[ Parent directory ] containing directories of P-files
OR
	-f	[ P-file ]
	
OPTIONS:
	-s	[ Output directory ] Moves & sorts P-files into STIL ID folders
	-sr	[ Output directory ] Same as above but will remove folder after completion if empty
	-o	[ output csv ] Creates .csv file of P-file info, requires filename to create/use as argument
	-h	Shows this message
	-v	Displays version
example:
	MRS_tool.sh -d /Volume/Matt/4DFlow/05092017 -o pfiles.csv

EOF
}

if [[ $# -eq 0 ]];
then
	usage
	exit 1
fi
OPTIND=1
while [[ $# > 0 ]]; do
    case "$1" in
        -d|--Dir)
			shift
			if [[ $# > 0 ]];
			then
				D="Y"
				Dir=$1
			else
				echo "[ERROR]: No input directory"
				exit 1
			fi
			shift
            ;;
        -pd|--ParentDir)
			shift
			if [[ $# > 0 ]];
			then
				PD="Y"
				Dir=$1
			else
				echo "[ERROR]: No input directory"
				exit 1
			fi
			shift
            ;;
        -f|--File)
        	shift
        	if [[ $# > 0 ]];
        	then
        		F="Y"
        		File=$1
        	else
        		echo "[ERROR]: No input file"
        		exit 1
        	fi
        	shift
        	;;
        -s|--Sort)
			shift
			if [[ $# > 0 ]];
			then
				S="Y"
				out=$1
			else
				echo "[ERROR]: No ouput directory"
				exit 1
			fi
			shift
            ;;
		-o|--OutputCSV)
			shift
			if [[ $# > 0 ]];
			then
				O="Y"
				csv=$1
			fi
			shift
			;;
		-sr)
			shift
			if [[ $# > 0 ]];
			then
				S="Y"
				R="Y"
				out=$1
			else
				echo "[ERROR]: No ouput directory"
				exit 1
			fi
			shift
            ;;
        -h|--help)
            usage
            exit
            ;;
		-v|--version)
            echo "Version is: $ver"
            exit
            ;;
        *)
            usage
            exit
            ;;
    esac
done
###----------------------------------------------------------
if [[ ! $D = "Y" ]] && [[ ! $PD = "Y" ]] && [[ ! $F = "Y" ]];
then
	echo "[ERROR]: Directory/file required"
	exit 1
fi
if [[ $D = "Y" ]] && [[ $PD = "Y" ]];
then
	echo "[ERROR]: Please only input 1 directory (-d or -pd)"
	exit 1
fi
if [ ! -z $Dir ];
then
	if [ ! -d $Dir ];
	then
		echo "[ERROR]: $Dir is not a directory"
		exit 1
	else
		dir=$(realpath $Dir)
	fi
elif [ ! -z $File ];
then
	if [ -f $File ];
	then
		file=$(realpath $File)
	else
		echo "[ERROR]: $File is not a file"
		exit 1
	fi
else
	echo "[ERROR]: Directory/File required"
	exit 1
fi
if [ ! -z $S ];
then
	if [ ! -d $out ];
	then
		echo "Creating output directory $out"
		mkdir -p $out
	fi
	output=$(realpath $out)
fi
###----------------------------------------------------------

##-----------------------------------------------------------
currentDir=$PWD
cd $dir
##---Assigns array with p file names----
if [[ $PD = "Y" ]];
then
	i=0
	for folder in $dir/*
	do
		for file in $folder/*
		do
			if [[ $file == *.7 ]];
			then
				pf=$(echo $file)
				pn=$(basename $file)
				printf -v "pfile[$i]" "$pf" #name including directory
				printf -v "pname[$i]" "$pn" #just name
				((i++))
			fi
		done
	done
	n=$(($i-1))
fi

if [[ $D = "Y" ]];
then
	i=0
	for file in $dir/*
	do
		if [[ $file == *.7 ]];
		then
			pf=$(echo $file)
			pn=$(basename $file)
			printf -v "pfile[$i]" "$pf" #name including directory
			printf -v "pname[$i]" "$pn" #just name
			((i++))
		fi
	done
	n=$(($i-1))
fi
##--------------------------------------

PulseSequenceName()
{ 
	rdgehdr $1 | grep -w -a "Pulse sequence name:" | cut -d ' ' -f 4
}
DateOfScan()
{ 
	dateline=$(rdgehdr $1 | grep -a "Allocation image date")
	echo ${dateline#*:}
}
Names()
{ 
	nameline=$(rdgehdr $1 | grep -w -a "Patient name")
	echo ${nameline#*:}
}
ExamNumber(){ 
	rdgehdr $1 | grep -w -a "Exam number:" | cut -d$'\n' -f 1 | cut -d ' ' -f 3
}
DateOfBirth(){ 
	rdgehdr $1 | grep -w -a "Date of birth:" | cut -d ' ' -f 4
}
PulseEchoTime(){ 
	rdgehdr $1 | grep -w -a "Pulse echo time" | cut -d ' ' -f 5 | head -c 2
}
ROI(){ 
	rdgehdr $1 | grep -a "ROI" | cut -d ' ' -f 6 | sed 's/[()]//g'
}
SeriesNumber(){ 
	rdgehdr $1 | grep -w -a "Series number:" | cut -d ' ' -f 3
}
if [[ $F = "Y" ]];
then
	echo "Pulse Sequence: $(PulseSequenceName $file)"
	echo "STIL ID: $(MRS_redcap.py -e $(ExamNumber $file) -d $(DateOfBirth $file) -stil_id)"
	echo "Date of Birth: $(DateOfBirth $file)"
	echo "Date of Scan: $(DateOfScan $file)"
	echo "Patient Name: $(Names $file)"
	echo "Exam Number: $(ExamNumber $file)"
	echo "Echo Time: $(PulseEchoTime $file)"
	echo "ROI: $(ROI $file)"
	echo "Series Number: $(SeriesNumber $file)"
	exit
fi
if [[ $D = "Y" ]] || [[ $PD = "Y" ]];
then
	##---Finds pulse sequence names---------
	i=0
	for file in "${pfile[@]}"
	do
		psn=$(PulseSequenceName $file)
		printf -v "pseq[$i]" "$psn"
		((i++))
	done
	##--------------------------------------
	
	##---Finds Date of Scan-----------------
	i=0
	for file in "${pfile[@]}"
	do
		psd=$(DateOfScan $file)
		printf -v "pdos[$i]" "$psd"
		((i++))
	done
	##--------------------------------------
	
	##---Finds first and last name----------
	i=0
	for file in "${pfile[@]}"
	do
		ppn=$(Names $file)
		ppln=$(echo $ppn | cut -d ' ' -f 1)
		ppfn=$(echo $ppn | cut -d ' ' -f 2)
		printf -v "pfname[$i]" "$ppfn"
		printf -v "plname[$i]" "$ppln"
		((i++))
	done
	##---------------------------------------
	
	##---Finds Exam number-------------------
	i=0
	for file in "${pfile[@]}"
	do
		ppe=$(ExamNumber $file)
		printf -v "penum[$i]" "$ppe"
		((i++))
	done
	##---------------------------------------
	
	##---Finds Date of Birth-----------------
	i=0
	for file in "${pfile[@]}"
	do
		ppd=$(DateOfBirth $file)
		printf -v "pdob[$i]" "$ppd"
		((i++))
	done
	##---------------------------------------
	
	##---Finds STIL ID-----------------------
	i=0
	for file in "${pfile[@]}"
	do
		if [[ ${pseq[$i]} == "PROBE-P" ]];
		then
			ids=$(MRS_redcap.py -e ${penum[$i]} -d ${pdob[$i]} -stil_id -redcap_id)
			ppid=$(echo $ids | cut -d ' ' -f 1)
			prid=$(echo $ids | cut -d ' ' -f 2)
			printf -v "pstil[$i]" "$ppid"
			printf -v "predid[$i]" "$prid"
			echo "Found STIL ID: $ppid, redcap id: $prid"
		fi
		((i++))
	done
	##---------------------------------------
	
	##---Finds pulse echo time---------------
	i=0
	for file in "${pfile[@]}"
	do
		pet=$(PulseEchoTime $file)
		printf -v "petime[$i]" "$pet"
		((i++))
	done
	##---------------------------------------
	
	##---Finds ROI---------------------------
	i=0
	for file in "${pfile[@]}"
	do
		pdsc=$(ROI $file)
		printf -v "pdesc[$i]" "$pdsc"
		((i++))
	done
	##--------------------------------------
	
	##---Finds Series number----------------
	i=0
	for file in "${pfile[@]}"
	do
		psnumber=$(SeriesNumber $file)
		printf -v "psnum[$i]" "$psnumber"
		((i++))
	done
	##--------------------------------------
	
	##---Write to CSV-----------------------
	if [[ $O = "Y" ]];
	then
		cd $currentDir
		if [ ! -f $csv ];
		then
			echo "STIL ID, P-file, Pulse sequence, Echo time, Series #, ROI" >> $csv
		fi
	
		i=0
		while [ $i -lt ${#pfile[*]} ];
		do
			echo "${pstil[$i]}, ${pname[$i]}, ${pseq[$i]}, 0.0${petime[$i]}, ${psnum[$i]}, ${pdesc[$i]}" >> $csv
			((i++))
		done
	else
		i=0
		echo "STIL ID | P file | Pulse sequence | Echo time | Series # | ROI"
		while [ $i -lt ${#pfile[*]} ];
		do
			echo "${pstil[$i]} | ${pname[$i]} | ${pseq[$i]} | 0.0${petime[$i]} | ${psnum[$i]} | ${pdesc[$i]}"
			((i++))
		done
	fi
	##-------------------------------------
	
	##---Create sorted folders-------------
	if [[ $S = "Y" ]];
	then
		cd $currentDir
		if [ ! -d $output/Misc ];
		then
			mkdir $output/Misc
		fi
		i=0
		while [ $i -lt ${#pfile[*]} ];
		do
			if [[ ${pseq[$i]} = "PROBE-P" ]] && [[ ! -z ${pstil[$i]} ]];
			then
				if [ -d $output/"${pstil[$i]}" ];
				then
					if [ ! -f $output/"${pstil[$i]}/${pstil[$i]}_${petime[$i]}ms_${pdesc[$i]}_${pname[$i]}" ];
					then
						echo "moving ${pname[$i]} to ${pstil[$i]}, TE: ${petime[$i]}ms ${pdesc[$i]}"
						mv $dir/${pname[$i]} $output/"${pstil[$i]}/${pstil[$i]}_${petime[$i]}ms_${pdesc[$i]}_${pname[$i]}"
					else
						echo "${pname[$i]} is duplicate, moving to misc"
						mv $dir/${pname[$i]} $output/"Misc/${pstil[$i]}_${petime[$i]}ms_${pdesc[$i]}_DUPLICATE_${pname[$i]}"
					fi
				else
					echo "making directory '${pstil[$i]}'"
					mkdir -p $output/"${pstil[$i]}"
					echo "moving ${pname[$i]} to ${pstil[$i]}, TE: ${petime[$i]}ms ${pdesc[$i]}"
					mv $dir/${pname[$i]} $output/"${pstil[$i]}/${pstil[$i]}_${petime[$i]}ms_${pdesc[$i]}_${pname[$i]}"
				fi
			else
				echo "${pname[$i]} is Pulse sequence: ${pseq[$i]}, moving to misc"
				mv $dir/${pname[$i]} $output/"Misc/${pfname[$i]}_${plname[$i]}_${pseq[$i]}_${pname[$i]}"
			fi
			if [ ! -f $output/${pstil[$i]}/${pstil[$i]}.txt ];
			then
				echo "${predid[$i]}" >> $output/${pstil[$i]}/${pstil[$i]}.txt
			fi
			((i++))
		done
		if [[ $R = "Y" ]];
		then
			shopt -s nullglob dotglob # To include hidden files
			files=($dir/*)
			if [ ${#files[@]} -eq 0 ];
			then
				echo "removing folder $dir"
				rm $dir
			else
				echo "did not delete $dir as it contains files"
			fi
	echo "---------Done----------------"
		fi
	fi
fi
##------------------------------------------
