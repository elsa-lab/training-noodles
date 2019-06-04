# Write the CPU information to a file
echo -e "/proc/cpuinfo on $NOODLES_SERVER_NAME:\n" > ~/exp1_result.log
cat /proc/cpuinfo >> ~/exp1_result.log
