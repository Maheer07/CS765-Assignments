import numpy as np
import random
# ref article bitcoin and bitcoincash: network analysis
def MakeConnections(l, snodes, fnodes, min_edges,zeta, slow_param = 1, fast_param = 3):
	# l is a list of ids(0,1,2,3....n-1),snodes is list of ids of slow noes and fnodes is list of ids of fast nodes
	# m is the minimum number of edges for each peer
	# slow_param isthe strength of slow peer and fast param is the strength of fast peer
	connections = {}
	for x in range(0, min_edges+1): # for first m+1 peers, we are ensuring full connectivity among themselves
		temp = []
		for y in range(0, min_edges+1):
			if x != y:
				temp.append(l[y])
		connections[l[x]] = temp
	for x in range(min_edges+1, len(l)):
		connections[l[x]] = []
	for x in range(min_edges+1,len(l)): 
		# for peers after (m+1) th peer we are calculating the probability of picking m peers from the existing network
		# the probability is caliculated as such (param(i)*degree(i))/sum_of(param*degree)
		# then np.random.choice is used to choose m peers
		nk = {}
		for y in connections:
			k = len(connections[y])
			n = fast_param
			if(y in snodes):
				n = slow_param
			nk[y] = n*k
		nk_key_array = np.array(list(nk.keys()))
		nk_val_array = np.array(list(nk.values()))
		nk_val_array = nk_val_array/sum(nk_val_array)
		top_m = np.random.choice(nk_key_array, min_edges, replace = False, p = nk_val_array)
		connections[l[x]] = list(top_m)
		for y in top_m:
			temp2 = connections[y]
			temp2.append(l[x])
			connections[y] = temp2
	# to increase the randomness, all the fast nodes are shuffled among themselves and 
	# all the slow nodes are shufflesd among themselves
	slowc = snodes.copy()
	fastc = fnodes.copy()
	random.shuffle(slowc)
	random.shuffle(fastc)
	smap={}
	fmap={}
	for i in range(len(snodes)):
		smap[snodes[i]]=slowc[i]
	for i in range(len(fnodes)):
		fmap[fnodes[i]]=fastc[i]
	connections2={}
	for x in connections:
		temp3=connections[x].copy()
		temp4=[]
		for k in temp3:
			if(k in snodes):
				temp4.append(smap[k])
			else:
				temp4.append(fmap[k])
		if(x in snodes):
			connections2[smap[x]]=temp4
		else:
			connections2[fmap[x]]=temp4

	ind = np.random.choice(l,int(zeta*(len(l))),replace = False)
	connections2[len(l)+1]=list(ind)

	for i in ind:
#		np.append(connections2[i],len(l)+1)
		#print(type(connections2[i]))
		connections2[i].append(len(l) + 1)
	return connections2