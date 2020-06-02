import os
import sys
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from geopy.distance import great_circle
from shapely.geometry import MultiPoint
from sortedcontainers import SortedDict

#credit to Geoff Boeing at https://geoffboeing.com/2014/08/clustering-to-reduce-spatial-data-set-size/ for the tutorial

#here coords should be a dictionary with key=ID and value=tuple of lat,long
#epsilon=max distance (in km) between points in a cluster
def dbscan_cluster(coords, epsilon, min_samples, out=None):
	kms_per_radian = 6371.0088

	points=coordsToMatrix(coords)
	
	#run DBSCAN
	eps=epsilon/kms_per_radian
	db=DBSCAN(eps=eps, min_samples=min_samples, algorithm='ball_tree', metric='haversine').fit(np.radians(points))
	
	#save cluster labels
	cluster_labels=db.labels_
	
	#build SortedDict to return
	popmap=SortedDict()
	i=0
	for k in coords.keys():
		pop="DB_"+str(cluster_labels[i])
		if pop not in popmap:
			l = [k]
			popmap[pop] = l
		else:
			popmap[pop].append(k)
		i+=1
	return(popmap)

#function to convert SortedDict of coordinates to a numpy matrix 
def coordsToMatrix(coords):
	return(pd.DataFrame([[coords[k][0], coords[k][1]] for k in coords], columns=["long", "lat"]).to_numpy())


#function to find the centroid of a set of points
#requires a SortedDict of coordinates and a SortedDict giving population IDs
"""Coords:
	key 	value
	SampleName	Tuple(Lat, Long)
	
	popmap:
	PopulationName	list(SampleName,...)
"""
def getClusterCentroid(coords, popmap, out=None):
	centroids=SortedDict()
	ofh=None
	if out:
		ofh=out+".clusterCentroids.txt"
	log=""
	for pop in popmap.keys():
		cluster=getPopCoordsMatrix(coords, popmap[pop])
		if len(cluster)<1:
			print("ERROR: getClusterCentroid(): No coordinates in cluster:",pop)
			sys.exit(1)
		
		#add cluster to logfile (if provided)
		log=log+"Population="+pop+"\n"
		log=log+str(cluster)+"\n"
		
		#get centroid point
		centroid = (MultiPoint(cluster).centroid.x, MultiPoint(cluster).centroid.y)
		log=log+"Centroid="+str(centroid)+"\n"
	
	if out:
		f=open(ofh, "w")
		f.write(log)
		f.close()
	
#returns a matrix of coordinates from a SortedDict of sample coordinates, given a list to subset
def getPopCoordsMatrix(d, l):
	return(pd.DataFrame([[d[k][0], d[k][1]] for k in d if k in l], columns=["long", "lat"]).to_numpy())

