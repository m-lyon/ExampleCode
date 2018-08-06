#!/bin/bash
###----------------------------------------------------------
ver="2.0.0"
usage()
{
  cat << EOF
USAGE: 
  	list_checker.sh

	Checks if entries in list 1 are contained in list 2
COMPULSORY:
	-l1	List 1

	-l2	List 2

	-b	List of entries contained in BOTH list 1 and list 2
OR
	-i	List of entries contained ONLY in list 1
OR
	-o	List of entries contained ONLY in list 2

OPTIONAL:
	-t	Outputs text file

	-v	Displays version number

	-h	Displays this message

example:
	list_checker.sh -l1 IDs.txt -l2 ID_check.txt -b -t output.txt

EOF
}

if [[ $# -eq 0 ]];
then
	usage
	exit 1
fi
OPTIND=1
while [[ $# > 0 ]];
do
	case "$1" in
		-l1|--List1)
		shift
		if [[ $# > 0 ]];
		then
			if [ -f $1 ];
			then
				list1=$(realpath $1)
			else
				echo "[ERROR]: $1 file not found"
				exit 1
			fi
		else
			echo "[ERROR]: No ouput directory"
			exit 1
		fi
		shift
        ;;
		-l2|--List2)
		shift
		if [[ $# > 0 ]];
		then
			if [ -f $1 ];
			then
				list2=$(realpath $1)
			else
				echo "[ERROR]: $1 file not found"
				exit 1
			fi
		else
			echo "[ERROR]: No ouput directory"
			exit 1
		fi
		shift
        ;;
		-b)
		B="Y"
		shift
		;;
		-i)
		I="Y"
		shift
		;;
		-o)
		O="Y"
		shift
		;;
		-t)
		shift
		if [[ $# > 0 ]];
		then
			T="Y"
			output=$1
		else
			echo "[ERROR]: No output file"
			exit 1
		fi
		shift
		;;
        -h|--help)
            usage
            exit 1
            ;;
		-v|--version)
            echo "Version is: $ver"
            exit
            ;;
        *)
            usage
            exit 1
            ;;
	esac
done

###----------------------------------------------------------
if [[ ! $B = "Y" ]] && [[ ! $I = "Y" ]] && [[ ! $O = "Y" ]];
then
	echo "[ERROR]: Please select either B, I, or O"
	exit 1
fi

if { [ "$B" = "Y" ] && [ "$I" = "Y" ]; } || { [ "$B" = "Y" ] && [ "$O" = "Y" ]; } || { [ "$O" = "Y" ] && [ "$I" = "Y" ]; };
then
	echo "[ERROR]: Please only select one of B, I, & O"
	exit 1
fi
###----------------------------------------------------------

if [ "$B" = "Y" ];
then
	echo "---Entries contained in both $list1 and $list2---"
elif [ "$I" = "Y" ];
then
	echo "---Entries contained ONLY in $list1---"
elif [ "$O" = "Y" ];
then
	echo "---Entries contained ONLY in $list2---"
fi

if [[ $B = "Y" ]] || [[ $I = "Y" ]];
then
	while read -r subject
	do
		if grep -q $subject $list2;
		then
			if [[ $B = "Y" ]];
			then
				if [[ $T = "Y" ]];
				then
					printf "$subject\n" >> $output
				else
					printf "$subject\n"
				fi
			fi
		else
			if [[ $I = "Y" ]];
			then
				if [[ $T = "Y" ]];
				then
					printf "$subject\n" >> $output
				else
					printf "$subject\n"
				fi
			fi
		fi
	done < $list1
fi

if [[ $O = "Y" ]];
then
	while read -r subject
	do
		if ! grep -q $subject $list1
		then
			if [[ $T = "Y" ]];
			then
				printf "$subject\n" >> $output
			else
				printf "$subject\n"
			fi
		fi
	done < $list2
fi
