Python Class – 2,  Python Casting, Strings, Operators & Conditions

#casting
=========================
x = 2
y = str(x)
z = str(2)
print type(y)
print type(z)

p = 4.5
q = int(p)
print q


#Python Array
#=========================
#cars = [ "ford", "toyota"]
#print cars[1]


#Python String
=============================
cc = '23, 2,5,7'
print cc[0]
print cc[1:2]
print cc[2:]

hey = "Can you read my last 4 characters?"
yes = hey[:-4]
print yes #No you can`t?

aahgotit=hey[:4]
print aahgotit  #you are damn

ohno = hey[-4:]
print ohno  #now you got it, keep hard work!



a = " Hello, World! what is my name?"
print(a.strip()) #removes white spaces at beginning and end
#removes white lines

a = "Hello, World!"
print(len(a))

a = "Hello, World!"
print(a.lower())


a = "Hello, World!"
print(a.upper())

a = "Hello, World!"
print(a.replace("Hello", "J"))
print(a.replace("o", "J"))

a = "we are in python class!"
b = (a.split()) # returns ['Hello', ' World!']
b = a.split(‘p’)
print b[1]


print("Enter your name:")
x = input()
print("Hello, " + x)


Python divides the operators in the following groups:
==============================================
Arithmetic operators
+,-,*
y = 5
x = y+1
print x

Assignment operators
x = 5
x = -2

Comparison operators
x == y
x > y
x >= y

Logical operators
x or y
x and y

Identity operators
is or is not

Membership operators
in, not in

Bitwise operators
AND, OR, XOR, NOT


Python Conditions and If statements
==========================================
If else

Python Loops
===========================================
while loops
for loops
Functions
