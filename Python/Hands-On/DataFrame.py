A dataframe refers to a two dimensional mutable data structure or data aligned in the tabular form with labeled axes(rows and column).

Syntax:

1
pandas.DataFrame( data, index, columns, dtype)
data:It refers to various forms like ndarray, series, map, lists, dict, constants and can take other DataFrame as Input.
index:This argument is optional as the index for row labels will be automatically taken care of by pandas library.
columns:This argument is optional as the index for column labels will be automatically taken care of by pandas library.
Dtype: refers to the data type of each column.


How do you identify missing values and deal with missing values in Dataframe?
Identification:

isnull() and isna() functions are used to identify the missing values in your data loaded into dataframe.


missing_count=data_frame1.isnull().sum()
Handling missing Values:

There are two ways of handling the missing values :

Replace the  missing values with 0


df[‘col_name’].fillna(0)
Replace the missing values with the mean value of that column


df[‘col_name’] = df[‘col_name’].fillna((df[‘col_name’].mean()))
94. How do you split the data in train and test dataset in python?
This can be achieved by using the scikit machine learning  library and importing train_test_split function in python as shown below:

from sklearn.model_selection import train_test_split

# test size = 30% and train = 70%
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random
