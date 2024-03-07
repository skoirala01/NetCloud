#single inheritance
class Animals:
def House(self):
print("lives in Jungle")

class Snakes(Animals):
def eats(self):
print("eats insects")

obj = Snakes()
obj.House()
obj.eats()
Output:
lives in Jungle
eats insects

#multiple inheritance
class Maths:
def Marks(self):
self.maths = 90

class English:
def Marks(self):
self.english = 85

class Result(Maths, English):
def __init__(self):
Maths.Marks(self)
English.Marks(self)


def result(self):
self.res = (self.maths + self.english) // 2
print("The result is : {}%".format(self.res))


obj = Result()
obj.result()





#multi-level inheritance
class Vehicle:
def __init__(self):
self.Type = "Commercial"
print("Vehicle Type : {}".format(self.Type))

class Name(Vehicle):
def __init__(self):
self.Name = "Ashok Leyland"
print("Vehicle Name: ".format(self.Name))

class Final(Name):
def __init__(self):
Name.__init__(self)
Vehicle.__init__(self)
self.Tyres = 8
print("Number of tyres is: {}".format(self.Tyres))


obj = Final()
