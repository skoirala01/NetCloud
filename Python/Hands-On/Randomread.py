import random
def read_random(fname):
lines = open(fname).read().splitlines()
return random.choice(lines)
print(read_random('hello.txt'))
