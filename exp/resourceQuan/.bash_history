python resource_regr.py 4coreAT2.39GHz-cap32.data,4coreAT1.86GHz-cap32.data,4coreAT1.20GHz-cap32.data,2coreAT2.39GHz-cap33.data,2coreAT1.86GHz-cap33.data,2coreAT1.20GHz-cap33.data
ls -lt
mv 2coreAT1.20GHz-cap33.data.png all-cores-orig.png
python resource_regr.py 4coreAT2.39GHz-cap32.data,4coreAT1.86GHz-cap32.data,4coreAT1.20GHz-cap32.data,2coreAT2.39GHz-cap33.data,2coreAT1.86GHz-cap33.data,2coreAT1.20GHz-cap33.data
ls -lt
mv 2coreAT1.20GHz-cap33.data.png all-cores-mod.png
python resource_regr.py 4coreAT2.39GHz-cap32.data,4coreAT1.86GHz-cap32.data,4coreAT1.20GHz-cap32.data
python resource_regr.py 4coreAT2.39GHz-cap32.data,4coreAT1.86GHz-cap32.data,4coreAT1.20GHz-cap32.data,2coreAT2.39GHz-cap33.data,2coreAT1.86GHz-cap33.data,2coreAT1.20GHz-cap33.data
vim 4coreAT2.39GHz-cap32.data
python resource_regr.py 4coreAT1.86GHz-cap32.data
cd MaxiNet/MaxiNet/Frontend/examples/
python resource_regr.py 4coreAT1.20GHz-cap32.data,4coreAT1.86GHz-cap32.data,4coreAT2.39GHz-cap32.data
python resource_regr.py 4coreAT1.86GHz-cap32.data
python resource_regr.py 2coreAT1.20GHz-cap33.data,2coreAT1.86GHz-cap33.data,2coreAT2.39GHz-cap33.data,4coreAT2.39GHz-cap32.data,4coreAT1.86GHz-cap32.data,4coreAT1.20GHz-cap32.data
cd MaxiNet/MaxiNet/Frontend/examples/
python resource_regr.py 2coreAT1.20GHz-cap33.data,2coreAT1.86GHz-cap33.data,2coreAT2.39GHz-cap33.data,4coreAT2.39GHz-cap32.data,4coreAT1.86GHz-cap32.data,4coreAT1.20GHz-cap32.data
ssh cap34 "sudo reboot"
python resource_regr.py 2coreAT1.86GHz-cap33.data,2coreAT2.39GHz-cap33.data,4coreAT2.39GHz-cap32.data,4coreAT1.86GHz-cap32.data
exit
cd MaxiNet/MaxiNet/Frontend/examples/
ls -lt
python exp_resource.py 2coreAT1.86GHz-cap33.data
python resource_regr.py 
python resource_regr.py 2coreAT1.86GHz-cap33.data
python resource_regr.py 2coreAT1.86GHz-cap33.data,4coreAT1.86GHz-cap32.data
ls -lt *.data
python resource_regr.py 4coreAT2.39GHz-cap32.data,4coreAT1.20GHz-cap32.data,2coreAT2.39GHz-cap33.data,2coreAT1.20GHz-cap33.data
python
cd MaxiNet/MaxiNet/Frontend/examples/
python resource_regr.py 2coreAT2.39GHz-cap33.data,2coreAT1.20GHz-cap33.data
python resource_regr.py 4coreAT2.39GHz-cap32.data,4coreAT1.20GHz-cap32.data
exit
cd MaxiNet/MaxiNet/Frontend/examples/
ls -lt
python resource_regr.py 2coreAT1.86GHz-cap33.data,4coreAT1.86GHz-cap32.data
python resource_regr.py 2coreAT1.20GHz-cap33.data,2coreAT2.39GHz-cap33.data,4coreAT1.20GHz-cap32.data,4coreAT2.39GHz-cap32.data
python resource_regr.py 2coreAT1.86GHz-cap33.data,4coreAT1.86GHz-cap32.data
python resource_regr.py 2coreAT1.20GHz-cap33.data,2coreAT2.39GHz-cap33.data,4coreAT1.20GHz-cap32.data,4coreAT2.39GHz-cap32.data
ls -al
mv .MaxiNet.cfg .MaxiNet.cfg.6pm
mv .MaxiNet.cfg.bak .MaxiNet.cfg
vim .MaxiNet.cfg
exit
ls -lt
vim rebootMaxiNet.sh 
vim startMaxiNet.sh 
./startMaxiNet.sh 
exit
cd MaxiNet/MaxiNet/Frontend/examples/
ls -lt
tail -f 4coreAT1.86GHz-cap32-.data
ls -lt
tail -100f 4coreAT1.86GHz-cap32-256B.data
cat 4coreAT1.86GHz-cap32-256B.data
cat 4coreAT1.86GHz-cap32-64B.data
cat 4coreAT1.86GHz-cap32-256B.data
vim 4coreAT1.86GHz-cap32.data
ls -lt
cat 4coreAT1.86GHz-cap32-1024B.data
tail -f 4coreAT1.86GHz-cap32-1024B.data
ls -lt
python resource_regr.py 2coreAT1.20GHz-cap33.data,2coreAT2.39GHz-cap33.data,4coreAT1.20GHz-cap32.data,4coreAT2.39GHz-cap32.data
ls -lt
cat 4coreAT1.86GHz-cap32-1024B.data
cat 4coreAT1.86GHz-cap32-256B.data
ls -lt
cat 4coreAT1.86GHz-cap32-512B.data
python resource_regr.py 2coreAT1.20GHz-cap33.data,2coreAT2.39GHz-cap33.data,4coreAT1.20GHz-cap32.data,4coreAT2.39GHz-cap32.data
python resource_regr.py 2coreAT1.86GHz-cap33.data,4coreAT1.86GHz-cap32.data
python resource_regr.py 2coreAT1.20GHz-cap33.data,2coreAT2.39GHz-cap33.data,4coreAT1.20GHz-cap32.data,4coreAT2.39GHz-cap32.data
python resource_regr.py 2coreAT1.86GHz-cap33.data,4coreAT1.86GHz-cap32.data
python resource_regr.py 2coreAT1.20GHz-cap33.data,2coreAT2.39GHz-cap33.data,4coreAT1.20GHz-cap32.data,4coreAT2.39GHz-cap32.data
python resource_regr.py 2coreAT1.86GHz-cap33.data,4coreAT1.86GHz-cap32.data
cd MaxiNet/MaxiNet/Frontend/examples/
ls -lt
vim runResourceExp.sh 
bash runResourceExp.sh
ls -lt
mv 4coreAT1.86GHz-cap32-.data 4coreAT1.86GHz-cap32-64B.data
vim 4coreAT1.86GHz-cap32-64B.data
bash runResourceExp.sh
ls -lt
python resource_regr.py 4coreAT1.86GHz-cap32.data,4coreAT1.86GHz-cap32-512B.data
ls -lt
cp 2coreAT1.20GHz-cap33.data 2coreAT1.20GHz-1250B-cap33.data
cp 2coreAT1.86GHz-cap33.data 2coreAT1.86GHz-1250B-cap33.data
cp 2coreAT2.39GHz-cap33.data 2coreAT2.39GHz-1250B-cap33.data
cp 4coreAT1.20GHz-cap32.data 4coreAT1.20GHz-1250B-cap32.data
cp 4coreAT1.86GHz-cap32.data 4coreAT1.86GHz-1250B-cap32.data
cp 4coreAT2.39GHz-cap32.data 4coreAT2.39GHz-1250B-cap32.data
ls -lt
cp 4coreAT1.86GHz-cap32-512B.data 4coreAT1.86GHz-512B-cap32.data
ls -lt
python resource_regr.py 2coreAT1.86GHz-1250B-cap33.data,4coreAT1.86GHz-1250B-cap32.data,4coreAT1.86GHz-512B-cap32.data
python resource_regr.py Mbps 2coreAT1.86GHz-1250B-cap33.data,4coreAT1.86GHz-1250B-cap32.data,4coreAT1.86GHz-512B-cap32.data
cd MaxiNet/MaxiNet/Frontend/examples/
ls -lt
ls
cd MaxiNet/MaxiNet/Frontend/examples/
ls -lt
vim screenlog.0 
screen -L -m bash runResourceExp.sh
vim rebootMaxiNet.sh 
./rebootMaxiNet.sh 
cd MaxiNet/MaxiNet/Frontend/examples/
ls -lt
tail 4coreAT1.86GHz-64-cap32.data
cd MaxiNet/MaxiNet/Frontend/examples/
ls -lt
rm 4coreAT1.86GHz-{pktSize[@]}-cap32.data
screen -L -m bash runResourceExp.sh
tail screenlog.
tail screenlog.0
tail -100 screenlog.0
ps -ef
screen -L -m bash runResourceExp.sh
./startMaxiNet.sh 
cd MaxiNet/MaxiNet/Frontend/examples/
python exp_resource.py 17 1000 1250 cap32 test-delay-100ms.data
ls -lt
cat test-delay-100ms.data
ls /tmp/maxinet_logs/2016-07-30_14\:37\:59/maxinet_mem_1_\(cap32\).log 
cat /tmp/maxinet_logs/2016-07-30_14\:37\:59/maxinet_mem_1_\(cap32\).log 
sudo atop 1
python exp_resource.py 17 1000 1250 cap32 test-delay-100ms.data
vim /tmp/maxinet_logs/2016-07-30_14\:42\:53/maxinet_mem_1_\(cap32\).log 
python exp_resource.py 17 1000 1250 cap32 test-delay-100ms.data
cd
ls -al
mv .MaxiNet.cfg .MaxiNet.cfg.3pm
mv .MaxiNet.cfg.6pm .MaxiNet.cfg
exit
sudo atop 1
ls
ls -lt
exit
ls
ls -lt
cd MaxiNet/
ls
cd MaxiNet
ls
cd Frontend
ls
cd examples/
ls
ls -lt
ls -lt *.py
vim exp_resource.py
exit
ls
exit
cd MaxiNet/MaxiNet/Frontend/examples/
ls
ls -lt *.py
vim resource_regr.py
ls -lt *.data
vim resource_regr.py
vim 4coreAT2.39GHz-cap32.data
cat 2coreAT1.20GHz-cap33.data
cat 4coreAT1.20GHz-cap32.data
ls -lt *.data
python resource_regr.py Mbps 2coreAT1.20GHz-cap33.data
python resource_regr.py Mbps 2coreAT1.20GHz-cap33.data,2coreAT2.39GHz-cap33.data
python resource_regr.py Mbps 2coreAT1.20GHz-cap33.data,2coreAT2.39GHz-cap33.data,4coreAT1.20GHz-cap32.data,4coreAT2.39GHz-cap32.data
python resource_regr.py Mbps 2coreAT1.20GHz-cap33.data,2coreAT1.86GHz-cap33.data,2coreAT2.39GHz-cap33.data,4coreAT1.20GHz-cap32.data,4coreAT1.86GHz-cap32.data,4coreAT2.39GHz-cap32.data
ls
cd MaxiNet/MaxiNet/Frontend/examples/
ls
mpstat 
lscpu
cpufreq-info
ls ~/
vim ~/startMaxiNet.sh 
vim ~/ .MaxiNet.cfg
vim ~/.MaxiNet.cfg
exit
ps -ef
ls
vim startMaxiNet.sh 
vim .MaxiNet.cfg
ls -al
vim .MaxiNet.cfg.3pm
mv .MaxiNet.cfg .MaxiNet.cfg.6pm
ls -al
cp .MaxiNet.cfg.3pm .MaxiNet.cfg
vim .MaxiNet.cfg
exit
ls
vim startMaxiNet.sh 
./startMaxiNet.sh 
cd MaxiNet/MaxiNet/Frontend/examples/
ls
ls *.sh
vim runResourceExp.sh 
ls -lt
vim resource_exp_22-sw_iperf_4core_2.39GHz.out
ls /tmp/
python exp_resource.py 
ls *.sh
vim startMaxiNet.sh 
vim runResourceExp.sh
python exp_resource.py 
ls /tmp/maxinet_logs/2016-12-06_20\:10\:46/ -ls
vim /tmp/maxinet_cpu_0_(cap31).log
vim /tmp/maxinet_cpu_0_\(cap31\).log 
cd ..
ls
cd ..
ls
cd Frontend
ls
vim maxinet.py 
cd ..
ls
sudo make install
cd MaxiNet/Frontend/examples/
ls
ssh cap32
ssh cap33
ls
ls *.sh
vim rebootMaxiNet.sh 
./rebootMaxiNet.sh 
cd MaxiNet/MaxiNet/Frontend/examples/
ls
./startMaxiNet.sh 
ls /tmp/
python exp_resource.py
vim /tmp/maxinet_logs/2016-12-06_20\:24\:38/maxinet_cpu_1_\(cap32\).log 
grep all /tmp/maxinet_logs/2016-12-06_20\:24\:38/maxinet_cpu_1_\(cap32\).log 
vim /tmp/maxinet_logs/2016-12-06_20\:24\:38/maxinet_cpu_1_\(cap32\).log 
head -20 /tmp/maxinet_logs/2016-12-06_20\:24\:38/maxinet_cpu_1_\(cap32\).log 
python
ls -lt
vim bwm-out-cap32.log
grep 1481073883 maxinet_cpu_1_\(cap32\).log 
ls /tmp/maxinet_logs/2016-12-06_20\:24\:38/maxinet_*
vim /tmp/maxinet_logs/2016-12-06_20\:24\:38/maxinet_mem_1_\(cap32\).log 
cd
pip install --user git+ssh://git@github.com/xybu/python-resmon.git
vim .pip/pip.log 
man pip
git clone git@github.com:xybu/python-resmon.git
ls
exit
python
exi
exit
vim MaxiNet/MaxiNet/Frontend/examples/resource_regr.py 
cd MaxiNet/MaxiNet/Frontend/examples/
ls
cd
git clone git@github.com:xybu/python-resmon.git
ls
cd ls
ls
cd python-resmon/
pip install -r requirements.txt
sudo apt install python3-dev
pip install -r requirements.txt
wget -O- https://bootstrap.pypa.io/get-pip.py | sudo python3
pip install -r requirements.txt
sudo pip install -r requirements.txt
./setup.py install --user
cd
ls
cd python-resmon/
ls
cd resmon/
ls
./resmon.py 
./resmon.py --nic xxx
exit
sudo atop 1
scp -r python-resmon/ cap32:~/
scp -r python-resmon/ cap33:~/
scp -r python-resmon/ cap34:~/
scp -r python-resmon/ cap35:~/
scp -r python-resmon/ cap36:~/
ssh cap32
ssh cap33
ssh cap34
ssh cap35
ssh cap36
ifconfig
./resmon.py --nic em1
cd python-resmon/
cd resmon/
./resmon.py --nic em1
ls
vim netstat.em1.csv 
./resmon.py --nic em1 --nic-outfile net.out
ls -lt
vim net.out 
rm net.out netstat.em1.csv 
ls
pwd
cd
cd MaxiNet/MaxiNet/Frontend/examples/
python exp_resource.py
./rebootMaxiNet.sh 
cd MaxiNet/MaxiNet/Frontend/examples/
./startMaxiNet.sh 
python exp_resource.py
ls -lt
ls /tmp/
vim bwm-out-cap33.log
python exp_resource.py
ls -lt
ifconfig
/home/cao/python-resmon/resmon/resmon.py --nic s1-eth1,s1-eth2,em1 --nic-outfile test-resmon-veth.log
ls
ls -lt
vim test-resmon-veth.log
exit
ls -lt
vim test-resmon-veth.log
/home/cao/python-resmon/resmon/resmon.py --nic s1-eth1,s1-eth2,em1 --nic-outfile test-resmon-veth.log
vim test-resmon-veth.log
ifconfig
/home/cao/python-resmon/resmon/resmon.py --nic s1-eth1 --nic-outfile test-resmon-veth.log
ifconfig
vim test-resmon-veth.log
ls
ls -lt
ls /tmp/ -lt
vim net-out-cap31.log
vim /tmp/net-out-cap31.log
/home/cao/python-resmon/resmon/resmon.py --nic em1,lo --nic-outfile test-resmon-veth.log
vim /tmp/net-out-cap31.log
ls -lt
vim test-resmon-veth.log
/home/cao/python-resmon/resmon/resmon.py --nic em1,lo
ls -lt
vim netstat.em1.csv
cd ~/MaxiNet/MaxiNet/Frontend/examples
ls
python exp_resource.py
ls -lt
ls -lt *.log
vim resmon-out-cap32.log
sudo mn
python exp_resource.py
vim resmon-out-cap31.log
python exp_resource.py
sudo mn
python exp_resource.py
ls /tmp/
ls /tmp/ -lt
vim /tmp/net-out-cap31.log
ls -lt
python exp_resource.py
ls /tmp/ -lt
python
python exp_resource.py
ps -ef
./rebootMaxiNet.sh 
sudo atop 1
exit
python
python-resmon/setup.py install --user
cd python-resmon/ 
./setup.py install --user
cd
cd MaxiNet/MaxiNet/Frontend/examples
ls
python exp_resource.py
./startMaxiNet.sh 
python exp_resource.py
ls -lt
vim resmon-out-cap32.log
python exp_resource.py
vim resmon-out-cap31.log
vim net-out-cap32.s2-eth1.log
python exp_resource.py
ps -ef
./rebootMaxiNet.sh 
cd MaxiNet/MaxiNet/Frontend/examples/cpu_unset/
cd ..
ls
ls -lt
ls *.log
ls *.log -lt
ls resmon*.log -lt
vim resmon-out-cap31.log
head -5 resmon-out-cap31.log
head -5 net-out-cap31.s1-eth1.log
head -5 resmon
head -5 net-out-cap32.s6-eth1.log 
python
pip install pandas
sudo pip install pandas
python
python3
python
python3
python
cd MaxiNet/MaxiNet/Frontend/examples/
ls
ls -lt
python
ls -lt *.log
ls
cd MaxiNet/MaxiNet/Frontend/examples/
ls
ls -lt *.log
vim net-out-cap32.s6-eth2.log
head -3 net-out-cap32.s6-eth2.log
head -3 resmon-out-cap33.log
cat net-out-cap32.s2*
cd MaxiNet/MaxiNet/Frontend/examples/
python exp_resource.py
./startMaxiNet.sh 
python exp_resource.py
ls -lt
vim resource_exp_output.out
ls 4coreAT*
ls 4coreAT*.data -ls
vim 4coreAT2.39GHz-cap32.data
vim 4coreAT1.20GHz-cap32.data
vim runResourceExp.sh 
cat resource_exp_output.out
python exp_resource.py
ls -lt
cat resource_exp_output.out
date
ls -ls *.csv
rm *.csv
python exp_resource.py
ls -lt
cat resource_exp_output.out
cd MaxiNet/MaxiNet/Frontend/examples/
ls
python exp_resource.py -h
python exp_resource.py --throughput 1000
ls -lt
cat resource_exp_output.out
ls -lt .*
cp .MaxiNet.cfg.6pm .MaxiNet.cfg
vim .MaxiNet.cfg
exit
cd MaxiNet/MaxiNet/Frontend/examples/
ls
ls -lt
python resource_regr.py pps 2coreAT1.20GHz-cap33.data,2coreAT2.39GHz-cap33.data,4coreAT1.20GHz-cap32.data,4coreAT2.39GHz-cap32.data
ls -lt
vim resource_regr.py 
python resource_regr.py pps 2coreAT1.20GHz-cap33.data,2coreAT2.39GHz-cap33.data,4coreAT1.20GHz-cap32.data,4coreAT2.39GHz-cap32.data
vim resource_regr.py 
python resource_regr.py pps 2coreAT1.20GHz-cap33.data,2coreAT2.39GHz-cap33.data,4coreAT1.20GHz-cap32.data,4coreAT2.39GHz-cap32.data
vim resource_regr.py 
python resource_regr.py pps 2coreAT1.20GHz-cap33.data,2coreAT2.39GHz-cap33.data,4coreAT1.20GHz-cap32.data,4coreAT2.39GHz-cap32.data
vim resource_regr.py 
python resource_regr.py pps 2coreAT1.20GHz-cap33.data,2coreAT2.39GHz-cap33.data,4coreAT1.20GHz-cap32.data,4coreAT2.39GHz-cap32.data
sudo atop 1
sudo hping3 -2 -q -p 8889 -i --flood -I em1 -d 64 128.10.130.152
sudo hping3 -2 -q -p 8889 --flood -I em1 -d 64 128.10.130.152
tc qdisc add dev eth0 root tbf rate 512kbit
tc qdisc add dev eth0 root tbf rate 512kbit burst 600
tc qdisc add dev eth0 root tbf rate 512kbit burst 1540 latency 0
tc qdisc add dev eth0 root tbf rate 512kbit latency 0 burst 1540
tc qdisc add dev em1 root tbf rate 512kbit latency 50ms burst 1540
sudo tc qdisc add dev em1 root tbf rate 512kbit latency 0ms burst 1540
sudo tc qdisc add dev em1 root tbf rate 512kbit latency 1ms burst 1540
sudo hping3 -2 -q -p 8889 -i --flood -I em1 -d 64 128.10.130.152
sudo hping3 -2 -q -p 8889 -i --flood -I em1 -d 64 128.10.130.153
ps -ef
sudo hping3 -2 -q -p 8889 --flood -I em1 -d 64 128.10.130.152
sudo hping3 -2 -q -p 8889 -i 100 -I em1 -d 64 128.10.130.152
sudo hping3 -2 -q -p 8889 -i u100 -I em1 -d 64 128.10.130.152
tc
ifconfig
tc qdisc show dev eth0
tc qdisc show dev em1
tc qdisc del dev em1 root
sudo tc qdisc del dev em1 root
tc qdisc show dev em1
sudo tc qdisc show dev em1
sudo tc -s qdisc ls dev em1
tc qdisc add dev em1 root tbf rate 1mbit burst 10kb latency 1ms
sudo tc qdisc add dev em1 root tbf rate 1mbit burst 10kb latency 1ms
sudo tc -s qdisc ls dev em1
sudo tc qdisc del dev em1 root
sudo tc -s qdisc ls dev em1
ls -al
ps -ef
ls
cat startMaxiNet.sh 
MaxiNetFrontendServer -h
man MaxiNetFrontendServer
MaxiNetFrontendServer --help
MaxiNet -h
MaxiNet --help
MaxiNetStatus -h
ls -al
vim .MaxiNet.cfg
exit
ls -lt
sudo atop 1
sudo dpkg -i libiperf0_3.1.3-1_amd64.deb iperf3_3.1.3-1_amd64.deb
exit
iperf3 -c 192.168.3.21 -l 1250 -t 15 -M 1250
iperf3 -c 128.10.130.154 -l 1250 -t 15 -M 1250
df -h
ls -lht
exit
ls
ls -lht
mkdir hpe-images
pwd
exit
cd hpe-images/
ls -lht
exit
ls -lht
vim .ssh/authorized_keys 
cat .ssh/id_rsa.pub 
exit
vim .ssh/authorized_keys 
df -h
ls
ls -lht
cd hpe-images/
ls -lht
cd hpe-images/
ls -lht
df -h
ls -lht
exit
cd hpe-images/
ls -lht
ls
cd ..
mkdir hpe-testbed-backup
ls
mv hpe-images/ hpe-testbed-backup/
cd hpe-testbed-backup/
ls -lht
mkdir ctl
cd ctl
pwd
ls
cd nfv/
ls -lht
cd ..
ls
cd ..
ls
mkdir cn1
cd cn1/
pwd
ls -al
cd nfv/
ls
ls -al
cd ..
ls
rm -r etc/
cd ..
ls
mkdir cn2
mkdir nn
mkdir ids-ctl
ls
cd cn2
ls
pwd
df -h
ls
cd etc/
ls -lht
cd init.d/
ls -lht
date
cd ..
cd systemd/
ls -lht
cd system/
ls
cd ..
cd udev/
ls
cd rules.d/
ls
cd ..
ls
vim ntp.conf 
cd ../..
ls
cd nn
ls
df -h
cd ..
ls -lht
df -h
ls
df -h
cd ctl/
ls
cd nfv/
ls
pwd
cd ..
ls
cd nfv/
vim .bash_history 
cd ..
cd .
cd ..
ls
ls -lht
ls ctl
ls ids-1
ls ids-ctl
ls cn1
ls cn2
ls nn
ls -lht
cd MaxiNet/
ls
cd MaxiNet
ls
cd Frontend
ls
cd examples/
ls
ls -lht
vim .bash_history 
history 
ls
ls -lht
vim resource_regr.py
python resource_regr.py pps 2coreAT1.20GHz-cap33.data,2coreAT2.39GHz-cap33.data,4coreAT1.20GHz-cap32.data,4coreAT2.39GHz-cap32.data
ls -lht
scp scaledCPU.eps cap34:~/mininet-hd/
vim resource_regr.py
python resource_regr.py pps 2coreAT1.20GHz-cap33.data,2coreAT2.39GHz-cap33.data,4coreAT1.20GHz-cap32.data,4coreAT2.39GHz-cap32.data
scp scaledCPU.eps cap34:~/mininet-hd/
exit
ls -lht
cd MaxiNet/
ls
cd MaxiNet
ls
cd MaxiNet/
ls
cd MaxiNet
ls
cd Frontend
ls
cd examples/
ls
ls -lht
vim resource_regr.py
cd MaxiNet/MaxiNet
ls
cd Frontend/examples/
ls -lht
vim resource_regr.py
vim 2coreAT1.20GHz-cap33.data
vim resource_regr.py
ls -al
rm .resource_regr.py.swp
vim resource_regr.py
ls
cd MaxiNet/MaxiNet
ls
cd Frontend/examples/
ls -lht
vim resource_regr.py
ls -al
rm .resource_regr.py.swp
vim resource_regr.py
