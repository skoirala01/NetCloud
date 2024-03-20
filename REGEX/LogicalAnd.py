import re
text = "I like apples and bananas."
regex = r"(?=. *apple)(?=. *banana)"
match = re.search(regex, text)
if match:
    print("Found both 'apple' and 'banana' on the same line.")
else:
    print("Did not find both 'apple' and 'banana' on the.")
