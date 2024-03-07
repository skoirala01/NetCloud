class Animals:
def species(self, x):
self.x = x
print("species of the animal is : {}".format(self.x))

class Snakes(Animals):
def species(self):
print("Species is Reptiles")

#calling the parent class method
obj = Animals()
obj.species("Amphibian")

#calling the class object overrides the parent class method
obj1 = Snakes()
obj1.species()
