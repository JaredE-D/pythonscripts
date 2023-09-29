
import numpy as np
import os as os
import matplotlib.pyplot as plt 
import h5py as hp
import scipy.optimize as opt
from scipy.fft import rfft, rfftfreq
from scipy.interpolate import CubicSpline


def zero(arr):
    l = np.array(arr)
    return l - l[0]

def findClosest(arr, n):
    dif = np.abs(arr - n)
    return dif.argmin()
    
def mmtodelay(arr):
    return arr/3 * 20
 
def linear(x, m, b):
    return m*x + b

def normalizecurr(arr):
    return np.array(arr)/max(arr)

fig, ax = plt.subplots(2,1, sharex=True)
plt.xlabel("Delay (ps)")

file = open('OneDrive/Desktop/BissC10data/thzrun.txt', 'r')
f = hp.File('OneDrive/Desktop/BissC10data/00012.hdf5', 'r')
f2 = hp.File('OneDrive/Desktop/BissC10data/00013.hdf5', 'r')
f3 = hp.File('OneDrive/Desktop/BissC10data/00014.hdf5', 'r')


lines = file.readlines()
starts = []
stops = []
for i, line in enumerate(lines):
    if(line == "Recording: 1\n"):
        starts.append(i)
    if(line == "Recording: 0\n"):
        stops.append(i)
times = []
poss = []
for i in range(len(starts)):
    times.append(lines[(starts[i]+1):stops[i]:2])
    poss.append(lines[(starts[i]+2):stops[i]:2])

newtimes = []
newposs = []
for timex in times:
    arr = []
    for l in timex:
        arr.append(float(l))
    arr = np.array(arr)
    newtimes.append(arr)
for posx in poss:
    arr = []
    for l in posx:
        arr.append(float(l))
    arr = np.array(arr)
    newposs.append(arr)
    
for i in range(len(newtimes)):
    newtimes[i] /= 1000.0 #seconds
    newposs[i] = newposs[i]*50.0/1000000.0 #mm

#for i in range(len(newtimes)):
#    plt.scatter(newtimes[i],newposs[i],s=2)


print(f.keys())
thz = f['DataVault']
thz2 = f2['DataVault']
thz3 = f3['DataVault']
#print(thz.shape)
pos1 = (newposs[0])
tim1 = (newtimes[0])
pos2 = (newposs[2])
tim2 = (newtimes[2])
pos3 = (newposs[4])
tim3 = (newtimes[4])

testposthz = []
posthz = []
curthz = []
testposthz2 = []
posthz2 = []
curthz2 = []
testposthz3 = []
posthz3 = []
curthz3 = []

motorthz = []
for i in thz:
    motorthz.append(i[5])
    if(i[5]<3.3):
        posthz.append(i[0])
        curthz.append(i[3])
for i in thz2:
    if(i[5]<3.3):
        posthz2.append(i[0])
        curthz2.append(i[3])
for i in thz3:
    if(i[5]<3.3):
        posthz3.append(i[0])
        curthz3.append(i[3])

scale1 = float(len(pos1))/float(len(posthz))
scale2 = float(len(pos2))/float(len(posthz2))
scale3 = float(len(pos3))/float(len(posthz3))

#for i in range(len(posthz)):
#    testposthz.append(pos1[round(i*scale1)])
#for i in range(len(posthz2)):
#    testposthz2.append(pos2[round(i*scale2)])
#for i in range(len(posthz3)):
#    testposthz3.append(pos3[round(i*scale3)])
tim1 = zero(tim1)
tim2 = zero(tim2)
tim3 = zero(tim3)

tottime1 = newtimes[0][-1]-newtimes[0][0]
timearray1 = np.arange(0,1,1.0/len(posthz))
timearray1 *= tottime1
for l in timearray1:
    testposthz.append(pos1[findClosest(tim1, l)])
  
tottime2 = newtimes[2][-1]-newtimes[2][0]
timearray2 = np.arange(0,1,1.0/len(posthz2))
timearray2 *= tottime2
for l in timearray2:
    testposthz2.append(pos2[findClosest(tim2, l)])
  
tottime3 = newtimes[4][-1]-newtimes[4][0]
timearray3 = np.arange(0,1,1.0/len(posthz3))
timearray3 *= tottime3
for l in timearray3:
    testposthz3.append(pos3[findClosest(tim3, l)])
  


posthz = zero(posthz)
testposthz = zero(testposthz)


posthz2 = zero(posthz2)
testposthz2 = zero(testposthz2)


posthz3 = zero(posthz3)
testposthz3 = zero(testposthz3)

posthz = np.arange(0,10, 10.0/len(posthz))
posthz2 = np.arange(0,10, 10.0/len(posthz2))
posthz3 = np.arange(0,10, 10.0/len(posthz3))

curthz = normalizecurr(curthz)
curthz2 = normalizecurr(curthz2)
curthz3 = normalizecurr(curthz3)

#'''
posthz = mmtodelay(posthz)
posthz2 = mmtodelay(posthz2)
posthz3 = mmtodelay(posthz3)
testposthz = mmtodelay(testposthz)
testposthz2 = mmtodelay(testposthz2)
testposthz3 = mmtodelay(testposthz3)
#'''
motorthz = np.array(motorthz)
print(len(posthz))
#print(motorthz[0].dtype)
ax[0].plot(posthz, curthz, label = 'Set1')
ax[1].plot(testposthz, curthz, label = 'Set1')

ax[0].plot(posthz2, curthz2, linestyle = 'dashed', label = 'Set 2')
ax[1].plot(testposthz2, curthz2, linestyle = 'dashed', label = 'Set 2')

ax[0].plot(posthz3, curthz3, linestyle = 'dashdot', label = 'Set 3')
ax[1].plot(testposthz3, curthz3, linestyle = 'dashdot', label = 'Set 3')
ax[1].legend()
ax[0].legend()
ax[0].set_ylabel('Original Current (amps)')
ax[1].set_ylabel('Updated Current (amps)')
def dx(poso, tima): 
    vel = np.ones(len(poso))
    for i in range(len(poso)-1):
        vel[i] = ((poso[i+1] - poso[i])/(tima[i+1]-tima[i]))
    vel[len(poso)-1] = 0
    return vel

'''
ax[2].plot(testposthz, curthz,linestyle='dashed', label = 'Old')
ax[2].plot(posthz, curthz, label = 'Updated')
ax[2].legend()
ax[2].set_ylabel("Set1 Current")
'''
'''
plt.figure()
plt.plot(testposthz, curthz,linestyle='dashed', label = 'Old')
plt.plot(posthz, curthz, label = 'Updated')
plt.ylabel("Photocurrent (1e-10amps)")
plt.xlabel("Delay (ps)")
plt.legend()
#'''
print(np.sqrt(np.sum((posthz-testposthz)**2)/(len(posthz)-1)))

'''
newfig, newax = plt.subplots(3,1, sharex=True)
newax[0].plot(posthz,curthz,linestyle='dashed', label = 'Old')
newax[0].plot(testposthz,curthz, label = 'Updated')
newax[1].plot(posthz2,curthz2,linestyle='dashed', label = 'Old')
newax[1].plot(testposthz2,curthz2, label = 'Updated')
newax[2].plot(posthz3,curthz3,linestyle='dashed', label = 'Old')
newax[2].plot(testposthz3,curthz3, label = 'Updated')
newax[0].legend()
newax[0].set_ylabel('Photocurrent')
newax[1].set_ylabel('Photocurrent')
newax[2].set_ylabel('Photocurrent')
plt.xlabel("Delay (ps)")
#'''

'''
plt.figure()
plt.xlabel("Time (s)")
plt.ylabel("Delay Measured - Expected (mm)")
par, cov = opt.curve_fit(linear, (tim1[0], tim1[-1]), (5568.0329, 5578.0329))
dif = -linear(tim1, *par) + np.array(newposs[0])
plt.plot(tim1, dif)
#'''
'''
plt.figure()
plt.xlabel("Delay (ps)")
plt.ylabel("Delay Measured - Expected (ps)")
par, cov = opt.curve_fit(linear, posthz, testposthz)
dif = -linear(posthz, *par) + np.array(testposthz)
plt.plot(posthz, dif)
#'''

'''
plt.figure()
plt.xlabel("Delay (ps)")
plt.ylabel("Delay Measured - Expected (ps)")
plt.plot(posthz, testposthz-posthz)
#'''




va = [posthz[curthz.argmax()],posthz2[curthz2.argmax()] ,posthz3[curthz3.argmax()]]
vb = [testposthz[curthz.argmax()],testposthz2[curthz2.argmax()] ,testposthz3[curthz3.argmax()]]

vc = [va[1]-va[0], va[2]-va[1]]
vd = [vb[1]-vb[0], vb[2]-vb[1]]

cs = CubicSpline(posthz,curthz)
cs2 = CubicSpline(posthz2,curthz2)
cs3 = CubicSpline(posthz3,curthz3)

def search(arr, x):
    for i in range(len(arr)):
        if(arr[i][0] == x):
            return i
    return -1
def getUniqueCur(arr):
    l = []
    [l.append(x) for i, x in enumerate(arr) if search(arr, x[0]) == i]
    l.sort()
    return l

#'''
testsort = list(set(testposthz))
print(len(testsort))
testsort = sorted(testsort)
cursort = getUniqueCur(list(zip(testposthz, curthz)))
#plt.figure()
#plt.plot(range(len(cursort)),cursort)
cs4 = CubicSpline(testsort, cursort)
#'''

'''
plt.figure()
fig1, ax1 = plt.subplots(3,1)
ax1[0].plot(testposthz, curthz - cs(testposthz))
ax1[1].plot(testposthz2, curthz2 - cs2(testposthz2))
ax1[2].plot(testposthz3, curthz3 - cs3(testposthz3))
#'''
print(np.array(va)-np.array(vb))
print(np.average(vc))
print(np.average(vd))

#'''
#timasd = np.linspace(0, len(curthz)*,)
T = (posthz[-1]-posthz[0])/(len(curthz)*10**12)
adsa = list(zip(*cs4(posthz)))[1]
freq1 = rfft(curthz)
freq2 = rfft(adsa)
fr12 = rfftfreq(len(curthz), T)
plt.figure()

plt.plot(fr12, np.abs(freq1))
plt.plot(fr12, np.abs(freq2))

#'''

plt.show()




