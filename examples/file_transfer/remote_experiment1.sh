# Write the CPU information to a file
echo -e "/proc/cpuinfo on server1:\n" > ~/exp1_result.log
cat /proc/cpuinfo >> ~/exp1_result.log
