nodes=(cap31 cap32 cap33 cap34 cap35 cap36)
freq=("2.4ghz" "1.2ghz" "2.4ghz" "2.4ghz" "2.4ghz" "1.2ghz")
# (METIS US-METIS UC-MKL)

### Set Frequency ###
for n in `seq 0 $((${#nodes[@]}-1))`; do
    echo ${nodes[n]}
    n_core=`ssh cao@${nodes[n]} 'cpufreq-info | grep "current CPU frequency" -c'`
    for c in `seq 0 $((n_core-1))`; do
        ssh cao@${nodes[n]} "sudo cpufreq-set -c $c -f ${freq[n]}"
    done
    ssh cao@${nodes[n]} 'cpufreq-info | grep "current CPU frequency"'
done

### Start MaxiNet ###
# ssh cao@${nodes[0]} "./startMaxiNet.sh"
screen -d -m -S MaxiNetFrontend MaxiNetFrontendServer
sleep 3
#workers=(cap34 cap35 cap36)
for w in ${nodes[@]}; do
    echo $w
    ssh $w "screen -d -m -S MaxiNetWorker sudo MaxiNetWorker"
done
sleep 3
MaxiNetStatus
