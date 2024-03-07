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
