#!/bin/sh -x

mkdir bin  # creates the bin folder in case it doesn't exist

rm -r bin/*  # remove contents of the bin folder

# creates folders in case they don't exist
mkdir bin/sav
mkdir bin/sav/backup
mkdir bin/out

cp -r csv bin/csv  # copy csv data to dist data folder
cp -r tax bin/tax  # copy csv data to dist data folder

cp README.md bin/README.md  # copy readme file to dist

cp build.spec src/launcher.spec  # copy spec file to sources folder

cd src  # cd to sources folder

pyinstaller launcher.spec --onefile --icon icon.ico --distpath ../bin --workpath ../tmp --clean  # create the executable
rm launcher.spec  # remove the temporary spec file

cd ..

rm -R tmp  # remove the work folder

pushd `dirname $0` > /dev/null
SCRIPTPATH=`pwd`
popd > /dev/null

gvfs-set-attribute -t string "bin/DiAnnotator" metadata::custom-icon file://${SCRIPTPATH}/ico/icon.png  # set the icon
