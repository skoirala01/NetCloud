def string_reverse(str1):
    '''testing
    llll'''
    '''hellow docstring'''

    #Returns the reversed String.

    #Parameters:
    #    str1 (str):The string which is to be reversed.

    #Returns:
    #    reverse(str1):The string which gets reversed.

    reverse_str1 = ''
    i = len(str1)
    while i > 0:
        reverse_str1 += str1[i - 1]
        i = i- 1
    return reverse_str1

def square(a):
    '''Returned argument a is squared.'''
    b = 1
    return b

print(string_reverse.__doc__)
print (square.__doc__)
