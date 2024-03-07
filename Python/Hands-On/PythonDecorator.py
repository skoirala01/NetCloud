def myWrapper(func):
  def myInnerFunc():
    print("Inside wrapper.")
    func()
  return myInnerFunc

@myWrapper
def myFunc():
  print("Hello, World!")

myFunc()
print(myFunc())
