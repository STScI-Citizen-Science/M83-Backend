#!/bin/bash
#
#shell script to generate mp4 videos for the m83 tiff pics.
#uses ffmpeg applicaiton and creates four different videos
#for the four resolutions (100px, 200px, 300px and 400px)
#Output format: m83video[res]px.mp4 eg. m83video100px.mp4
#

#executes ffmpeg for the 100px pics 
ffmpeg -f image2 -r 1 -pattern_type glob -i '*100pix*.tiff' m83video100px.mp4
#for 200px pics
ffmpeg -f image2 -r 1 -pattern_type glob -i '*200pix*.tiff' m83video200px.mp4
#for 300px pics
ffmpeg -f image2 -r 1 -pattern_type glob -i '*300pix*.tiff' m83video300px.mp4
#for 400px pics
ffmpeg -f image2 -r 1 -pattern_type glob -i '*400pix*.tiff' m83video400px.mp4