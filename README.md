# EXECUTIVE REPORT

### Introduction 
This program is all 

### 1. Libraries used
- 'pandas': used for managing the DataFrame
- 're': used for splitting strings and detecting re patterns
- 'matplotlib.pyplot': drawing plots
- 'seaborn': drawing plots
- 'os': used for detecting whether the csv already exists
- 'warnings': to ignore certain warnings concerning data types
- 'fpdf': to work with pdfs. Specifically draw our own

### 2. ETL
#### 1) Extract
We simply read the csvs with the names on the list 'file_names' with the 'read_csv' function from pandas, controlling whether the separation is ',' or ';'

#### 2) Transform
We get rid of some of the nans and drop the column 'time', as we are not going to use it. The function 'limpieza_de_datos' takes care of cleaning the dataframe. Once the dataframes are clean, we proceed to obtaining the different dataframes that we need for plotting

The most important function for creating the dashboard is, perhaps, 'obtain_dfs_plots'. It 
puts together different data obtained from our study to generate the different Dataframes that I have determined are useful for the study of Maven Pizzas. These contain the following data:
- 'df_pizzas_anuales': yearly pizza orders, which is used for the basic barploot and the pie chart
- 'df_pizzas_semanales': weekly pizza orders, which is used for the time evolution of the top 5 pizzas
- 'df_pizzas_weekdays': pizzas ordered by day of the week
We use the DateTime Function, with whom we get the day of the week from a formatted time.

#### 3) Load
Within this section, we include plot and Load. 

First, we have to plot the differemt plots we have seen fit for the study. These include: a pie chart and barplot on the pizzas ordered yearly, a table and a time evolution on the most requested pizzas and a barplot on the amount of pizzas ordered each day of the week. 

All of them are used with seaborn, except for the pie chart, which I obtained with MatplotLib, and the Table, which I got with a pandas built-in function 'pd.plotting.table'.

Finally, we loaded the images in a certain distribution in a pdf using the libray 'fpdf', mentioned eearlier on. For the Dashboard's title, we have created a class PDF. We organise the different photos using the 'image' function. To create the file we use 'output' with the desired file name as argument. 