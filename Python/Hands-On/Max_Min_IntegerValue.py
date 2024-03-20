try:
    import sys
except:
    import sys
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'sys'])
    import sys



import sys
print(sys.maxsize)
#2147483647

import sys
print(-sys.maxsize - 1)
#-2147483648


def findmax(xyz):
    maxnum = max(xyz)
    return maxnum

def main():
	some_list = [1, 3, 2, 1, 4, 3, 1, 0, 1, 3]
	maxnum = findmax(some_list)
	print(f'''The max number from the given list {some_list} is {maxnum}''')


if __name__ == "__main__":
	main()
