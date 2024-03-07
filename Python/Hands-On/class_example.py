class Human:
    def __init__(self, age):
        self.age = age
    def say(self):
        print('Hello, my age is', self.age)
h = Human(22)
h.say()




class WriteDict:
    def writefun(self, x):
        #self.x = x
        with open('class_example.txt','w') as file:
            for k, m in x.keys(), x.values():
                file.write((k + '\t' + m +'\n'))

def main():
    xx = {'name': 'youname', 'SSN': 'yourSSN'}
    callclass = WriteDict()
    callclass.writefun(xx)


if __name__ == "__main__":
    print(1)
    main()








