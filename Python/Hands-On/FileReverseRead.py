filename = "class_example.txt"
with open(filename, "r") as file:
    lines = file.readlines()

for line in reversed(lines):
    print(line.rstrip())
