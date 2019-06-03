# Write the memory information to a file
echo -e "/proc/meminfo:\n" > ~/exp2_result.log
cat /proc/meminfo >> ~/exp2_result.log
