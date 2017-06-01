#!/bin/sh
cp *.gif ../
cd ../
gifsicle -i --batch --crop-transparency -O3 *.gif
