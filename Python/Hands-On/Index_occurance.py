myList=["cat", "dog", "cat", "rat"]

#find the indexes of all occuremce of "cat" in myList
indList=[ind for ind, val in enumerate(myList) if val=="cat"]

print(indList)
