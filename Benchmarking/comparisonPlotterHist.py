'''
Historgram plotter
@authors: Greg Henderson
'''
import csv
import numpy
import matplotlib.pyplot as plot
import matplotlib.patches as mpatches
def extractData(fileName):
    rawData = []
    f = open(fileName, 'r')
    wr = csv.reader(f)
    for row in wr:
        rawData.append(row)
    data = [[float(j[i]) for j in rawData] for i in range(6)]
    return data

#extracting data
data1 = []
data1.append(extractData('mopsoConvergenceDataHist.csv'))
data1.append(extractData('mosaConvergenceDataHist.csv'))
data1.append(extractData('nsga2ConvergenceDataHist.csv'))
for i in data1[2]:
    del i[0]
titles = ['MOPSO', 'MOSA', 'NSGA2']
labels = ['metric1', 'metric2', 'metric3']
print data1[2][3]
#Now begin the plot
plot.subplot(3,3,1)
plot.hist(data1[0][0])
plot.title(titles[0])
plot.xlabel(labels[0])
plot.ylabel('Density')
plot.subplot(3,3,2)
plot.hist(data1[0][1])
plot.title(titles[0])
plot.xlabel(labels[1])
plot.ylabel('Density')
plot.subplot(3,3,3)
plot.hist(data1[0][2])
plot.title(titles[0])
plot.xlabel(labels[2])
plot.ylabel('Density')
plot.subplot(3,3,4)
plot.hist(data1[1][0])
plot.title(titles[1])
plot.xlabel(labels[0])
plot.ylabel('Density')
plot.subplot(3,3,5)
plot.hist(data1[1][1])
plot.title(titles[1])
plot.xlabel(labels[1])
plot.ylabel('Density')
plot.subplot(3,3,6)
plot.hist(data1[1][2])
plot.title(titles[1])
plot.xlabel(labels[2])
plot.ylabel('Density')
plot.subplot(3,3,7)
plot.hist(data1[2][0])
plot.title(titles[2])
plot.xlabel(labels[0])
plot.ylabel('Density')
plot.subplot(3,3,8)
plot.hist(data1[2][1])
plot.title(titles[2])
plot.xlabel(labels[1])
plot.ylabel('Density')
plot.subplot(3,3,9)
plot.hist(data1[2][2])
plot.title(titles[2])
plot.xlabel(labels[2])
plot.ylabel('Density')
plot.show()
