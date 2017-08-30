'''
Created on 7 Aug 2017

@author: qvi61384
'''
from __future__ import division
import math

# m is number of parameters

def kursawe(x):
    f0 = 0
    for i in range(2):
        f0 = f0 + -10 * math.exp(-0.2 * math.sqrt(x[i] ** 2 + x[i+1] ** 2))
    f1 = 0
    for i in range(3):
        f1 = f1 + abs(x[i]) ** 0.8 + 5 * math.sin(x[i] ** 3)
    return [f0,f1]


def T1(x):
    
    m = len(x)
    f1 = x[0]
    sum = 0
    for i in range(1,m):
        sum += x[i]/(m-1)
    g = 1 + 9*sum
    h = 1 - math.sqrt(f1/g)
    f2 = g*h
    
    return [f1,f2]

def T2(x):
    
    m = len(x)
    f1 = x[0]
    sum = 0
    for i in range(1,m):
        sum += x[i]/(m-1)
    g = 1 + 9*sum
    h = 1 - (f1/g)**2
    f2 = g*h
    
    return [f1,f2]

def T3(x):
    
    m = len(x)
    f1 = x[0]
    sum = 0
    for i in range(1,m):
        sum += x[i]/(m-1)
    g = 1 + 9*sum
    h = 1 - math.sqrt(f1/g) - (f1/g)*math.sin(10*math.pi*f1)
    f2 = g*h
    
    return [f1,f2]

def T4(x):
    
    m = len(x)
    f1 = x[0]
    sum = 0
    for i in range(1,m):
        sum += (x[i]**2 - 10*math.cos(4*math.pi*x[i]))
    g = 1 + 10*(m-1) + sum
    h = 1 - math.sqrt(f1/g)
    f2 = g*h
    
    return [f1,f2]

def T6(x):
    
    m = len(x)
    f1 = 1 - math.exp(-4*x[0])*(math.sin(6*math.pi*x[0])**6)
    sum = 0
    for i in range(1,m):
        sum += x[i]/(m-1)
    g = 1 + 9*(sum**0.25)
    h = 1 - (f1/g)**2
    f2 = g*h
    
    return [f1,f2]