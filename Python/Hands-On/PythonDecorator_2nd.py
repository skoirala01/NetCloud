def decorateFun(func):
    def sumOfSquare(x, y):
        return func(x**2, y**2)
    return sumOfSquare

@decorateFun
def addTwoNumbers(a, b):
    c = a+b
    return c

c = addTwoNumbers(4,5)
print("Addition of two numbers=", c)
