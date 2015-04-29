#tell engine to use current directory
#$ -cwd


## the "meat" of the script

#just print the name of this machine

counter = 0
for (( i =1; i <= 100; i++))
do     
    echo Trial $i
    python nyt_scraper.py
done
