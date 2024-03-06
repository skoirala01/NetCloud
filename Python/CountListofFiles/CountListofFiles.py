import os

file = os.listdir()
batch_count = 0
for list in file:
    if 'Cmd' in list:
        batch_count = batch_count + 1

print(batch_count)
