#!/bin/bash

DONOR_FOLDER=$2
VASP_ROOT_FOLDER=$1

GRID_SWIFT="/net/people/plgjakubmj/grid-swift"

if [ -d "$VASP_ROOT_FOLDER" ]; then
    # DIRECTORY EXISTS
    echo "DIRECTORY $VASP_ROOT_FOLDER exists"
else 
    echo "DIRECTORY $VASP_ROOT_FOLDER does not exist... Created"
    mkdir $VASP_ROOT_FOLDER
fi

ION_RELAX="$VASP_ROOT_FOLDER/ION_RELAX"
ELECTRON_RELAX="$VASP_ROOT_FOLDER/ELECTRON_RELAX"
NON_COLINEAR="$VASP_ROOT_FOLDER/NON_COLINEAR"

shopt -s extglob
for FOLDER in $ION_RELAX $ELECTRON_RELAX $NON_COLINEAR; do
    mkdir $FOLDER
    cp ${DONOR_FOLDER%%+(/)}${DONOR_FOLDER:+/}{INCAR,POSCAR,POTCAR,KPOINTS} $FOLDER
done 


# for ION RELAX make sure ICHARG is 2 and NSW is 10
sed -i -r -e 's/ICHARG\s+=\s+[0-9]+/ICHARG = 2/g' -e 's/NSW\s+=\s+[0-9]+/NSW = 10/g' $ION_RELAX/INCAR 

#SBATCH -J bigRUN
#SBATCH -p plgrid
#SBATCH -N 1
#SBATCH --tasks-per-node=16
#SBATCH --time=4:00:00
#SBATCH -p plgrid
module load plgrid/apps/vasp/5.4.4

ION_RELAX=$SLURM_SUBMIT_DIR/$ION_RELAX
ELECTRON_RELAX=$SLURM_SUBMIT_DIR/$ELECTRON_RELAX
NON_COLINEAR=$SLURM_SUBMIT_DIR/$NON_COLINEAR

cd $ION_RELAX
date
$VASP_RUN
date
cd .. 

cp $ION_RELAX/CHGCAR $ELECTRON_RELAX

# remove ION relaxation for ELECTRON RELAX and start from CHGCAR
sed -i -r -e 's/ICHARG\s+=\s+[0-9]+/ICHARG = 1/g' -e 's/NSW\s+=\s+[0-9]+/NSW = 0/g' $ELECTRON_RELAX/INCAR 

cd $ELECTRON_RELAX
date
$VASP_RUN
date
cd ..

cp $ELECTRON_RELAX/CHGCAR $NON_COLINEAR

# for non-colinear create kpoints path
sed -i -r -e 's/ICHARG\s+=\s+[0-9]+/ICHARG = 11/g' -e 's/NSW\s+=\s+[0-9]+/NSW = 0/g' $NON_COLINEAR/INCAR 
python3 $GRID_SWIFT/vasp_kpoints.py -s $NON_COLINEAR -p GHNGP

cd $NON_COLINEAR
date
$VASP_NONCOLLINEAR_RUN
date 

echo "FINISHED YO"



