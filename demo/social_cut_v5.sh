#!/bin/bash
# Continuous social cut (≈88 s): The post (0:08–0:20) · How + whole live check (0:46–1:38) · Results (2:18–2:34) · DappGo (2:50–2:58)
set -e
in="$1"; out="$2"
ffmpeg -v error -y -i "$in" -filter_complex "
[0:v]trim=8:20,setpts=PTS-STARTPTS[v0];[0:a]atrim=8:20,asetpts=PTS-STARTPTS[a0];
[0:v]trim=46:96,setpts=PTS-STARTPTS[v1];[0:a]atrim=46:96,asetpts=PTS-STARTPTS[a1];
[0:v]trim=138:154,setpts=PTS-STARTPTS[v2];[0:a]atrim=138:154,asetpts=PTS-STARTPTS[a2];
[0:v]trim=170:178,setpts=PTS-STARTPTS[v3];[0:a]atrim=170:178,asetpts=PTS-STARTPTS[a3];
[v0][a0][v1][a1][v2][a2][v3][a3]concat=n=4:v=1:a=1[v][a]" -map "[v]" -map "[a]" -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -c:a aac -b:a 256k -movflags +faststart "$out"
ffprobe -v error -show_entries format=duration -of csv=p=0 "$out"
