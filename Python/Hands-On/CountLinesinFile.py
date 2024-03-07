def file_count(fname):
    with open(fname) as f:
        for i, _ in enumerate(f):
            pass
    return i + 1

print("Total number of lines in the text file:",
file_count("file.txt"))
