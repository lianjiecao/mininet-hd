#! /bin/bash
workers=(cap31 cap32 cap33 cap35 cap36)
for w in ${workers[@]}; do
    echo $w
    ssh $w "sudo reboot"
done
sudo reboot
