#!/bin/bash
set -e

trap "exit" INT TERM ERR
trap "kill 0" EXIT

sleep 10
cd /home/pi/Documents/cv-birdfeeder
ifconfig > /home/pi/Documents/ip.txt
ssh -R 80:localhost:8000 localhost.run >> /home/pi/Documents/ip.txt &

current_date=$(date)
echo "Started camera and server at $current_date" >> /home/pi/Documents/log.txt

python server_classification.py
wait
