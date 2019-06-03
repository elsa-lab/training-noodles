# Write the CPU information to a file
echo -e "/proc/cpuinfo:\n" > ~/exp1_result.log
cat /proc/cpuinfo >> ~/exp1_result.log
