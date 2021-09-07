from numpy import add
from utils import *
from genral_tree import *
from connections import *
import random
import simpy
import numpy as np
import os
from datetime import datetime
from datetime import time


#All these variables are defined in main function
connected = {}
txn_id = None
transactions = []
num_peers = 5
peer2peer = None
env = None
start_time = None
longest_chain = None
trees = None
blocknumbers = None

file_txn = "Transactions.txt"
file_block = "Blocks.txt"


#Took this class from https://www.geeksforgeeks.org/priority-queue-in-python/ with a change in delete function because of unfamiliarity with python data structures
class PriorityQueue(object): #This is the priority queue that will store all our events in the network
    def __init__(self):
        self.queue = []
  
    def __str__(self):
        return ' '.join([str(i) for i in self.queue])
  
    def isEmpty(self):
        return len(self.queue) == 0
  
    def insert(self, data):
        self.queue.append(data)

  
    def delete(self):
        try:
            max = 0
            for i in range(len(self.queue)):
                if self.queue[i] > self.queue[max]:
                    max = i
            item = self.queue[max]
            del self.queue[max]
            return item
        except IndexError:
            exit()

class transaction:
    #This class represents a transaction
    #Consider X pays Y Z bitcoins
    def __init__(self,src,dest,amt,id):
        self.src = src  #X, the sender
        self.dest = dest #Y, the reciever
        self.amt = amt #Z, the amount sent
        self.id = id # Unique transaction ID
        self.included = False #Is the transaction included in any block
        self.forwarded = [[False for i in range(num_peers)] for i in range(num_peers)] #The forwarding table of the txn. forwarded[i][j] = True means the txn has been forwarded from peer i to j or vice versa

class block:
    def __init__(self,id,txnlist,time,creatorid,previd,dummy):
        self.id = id #Block id
        self.txnlist = txnlist #List of txns in the block
        self.time = time #Time of creation
        self.creatorid = creatorid # ID of creator of the block
        self.previd = previd #Parent block ID
        self.dummy = dummy #Is the block a dummy block
        self.forwarded = [[False for i in range(num_peers)] for i in range(num_peers)] #Forwarding table, similar to transaction

    def size(self): #Returns size of block(In KB)
        return 1 + len(self.txnlist) 

    def mod_txns(self): #To 
        for t in self.txnlist:
            t.included = True

class peer:
    def __init__(self,id,balances):
        self.id = id #Peer id (unique)
        self.balances = balances #List of bitcoins left of all peers in the network
        self.transactions = [] #Txn pool
        self.blocktree = GenralTree() #Blockchain tree and initialization
        self.blocktree.setRoot(block(0,[],0,self.id,0,False))
        self.root = self.blocktree.getRoot()
        self.pending = {} #Pending blocks (blocks whose parents haven't arrived stored as Parent id : List of children who've arrived before)
        self.arrived = [] #Blocks recieved by the peer

    def update_transactions(self):
        l = [i for i in self.transactions if i.included == False]
        self.transactions = l

class event:
    def __init__(self,type,time,txn,peerid):
        self.type = type #Event type
        self.time = time #Time of execution of event
        self.txnorblock = txn #Transaction or block involving the event
        self.peerid = peerid #Peer id of peer executiong the event

    def __gt__(self,other): #Overriding greater than operator to return true for the event with lower value of time
        if self.time < other.time:
            return True
        else:
            return False


def latency(i,j,ro_ij,size,c): #Function to return latency in ms 
    c_ij = c[i][j] #c_ij as per definition
    d_ij = generate_exponential(96/c_ij) #d_ij as per definition
    t = d_ij + ro_ij + (size / c_ij)
    return t

def add_time(t1,t2): #Adds delay(from simulation) to the global time at the start of simulation
    t2 = t2 / 1000
    t = t2 / 3600
    t2 = t2 % 3600
    a = int(t1.hour + t)
    t = t2 / 60
    t2 = t2 % 60
    b = int(t1.minute + t)
    c = int(t1.second + t2)
    if c >= 60:
        b += int(c / 60)
        c = c % 60
    if b >= 60:
        a += int(b / 60)
        b = b % 60
    return time(a,b,c)





class p2p(object):
    def __init__(self,env,tx,tk,txn_id,blockid,peers,connected,ro_ij,c):
        self.env = env #Environment variable
        self.time_tx = tx #time T_tx 
        self.time_tk = tk #time T_tk
        self.txn_id = txn_id #Transaction id of the latest txn
        self.blockid = blockid #Transaction id of the latest block
        self.event_queue = PriorityQueue() #The priority queue of the peer2peer network
        self.peers = peers #List of peers
        self.connected = connected #A dictionary mapping a peer id to the ids of the peers connected to it
        self.ro_ij = ro_ij #Minimum latency
        self.c = c #A 2d vector with c_ij values for latency computation

    def generate_transaction(self,env,peer,dummy):
                
        timeout = generate_exponential(self.time_tx) #Time after which we'll execute next generate transaction event
        t = env.now
        y = select_random(self.peers)
        while y == peer:
            y = select_random(self.peers)
        
        high = peer.balances[y.id - 1]
        amt = random.uniform(0,high) #We select amount of txn from a unifrom distribution with ranges 0 and balance of sender 
        txn = transaction(peer,y,amt,self.txn_id) 
        if dummy==False: #Dummy = true is just for initialization
            with open(file_txn,"a") as ff:
                ff.write("Generating transaction " + str(self.txn_id) + " at peer " + str(peer.id) + " at t= " + str(env.now) + "\n")
            self.txn_id += 1
            peer.transactions.append(txn) #Adding to txn pool
            e = event("forward transaction",t,txn,peer.id) #Generating forward txn event at the same time
            self.event_queue.insert(e)
        e = event("generate transaction",t+timeout,txn,peer.id) #Next generate txn event
        self.event_queue.insert(e)

        yield self.env.timeout(0)


    def forward_transaction(self,peer,env,txn): 
        for p in connected[peer.id]: #Forward based on the transaction's forwarding table
            if txn.forwarded[peer.id-1][p-1] == False:
                txn.forwarded[peer.id-1][p-1] = True
                txn.forwarded[p-1][peer.id-1] = True
                timeout = latency(peer.id-1,p-1,self.ro_ij,1,self.c) #Calculate latency between two peers
                with open(file_txn,"a") as ff:
                    ff.write("Forwarding transaction " + str(txn.id) + " from peer " + str(peer.id) + " to peer " + str(p) + " at t= " + str(env.now) + " latency = " + str(timeout) + "\n")
                e = event("recieve transaction",env.now + timeout,txn,p) #Generating recieve txn event at the reciever after time latency
                self.event_queue.insert(e)
        
        yield self.env.timeout(0)

    def recieve_transaction(self,env,peer,txn):
        with open(file_txn,"a") as ff:
            ff.write("Recieved transaction " + str(txn.id) + " at peer " + str(peer.id) + " at t= " + str(env.now) + "\n")
        if txn not in peer.transactions: #Updating transaction pool
            peer.transactions.append(txn)
        for p in connected[peer.id]: 
            if txn.forwarded[peer.id-1][p-1] == False: #Forwarding as per the txn forwarding table, similar to forward_transaction function
                txn.forwarded[peer.id-1][p-1] = True
                txn.forwarded[p-1][peer.id-1] = True
                timeout = latency(peer.id-1,p-1,self.ro_ij,1,self.c)
                with open(file_txn,"a") as ff:
                    ff.write("Forwarding transaction " + str(txn.id) + " from peer " + str(peer.id) + " to peer " + str(p) + " at t= " + str(env.now) + " latency = " + str(timeout) + "\n")
                e = event("recieve transaction",env.now + timeout,txn,p)
                self.event_queue.insert(e)  

        yield self.env.timeout(0)

    def generate_block(self,env,peer):

        timeout = generate_exponential(self.time_tk[peer.id-1]) #Timeout after which we'll verify and broadcast the block
        t = env.now
        #In the following lines we're just taking a subset of transactions from the pool such that the block size doesn't exceed 1MB
        n = len(peer.transactions)
        lim  = 999
        l = [i for i in range(n)]
        if n == 0:
            num = 0
        else:
            num = random.sample(l,1)[0]
        while num > lim:
            num = random.sample(l,1)[0]
        txns = random.sample(peer.transactions,num) 
        longest_chain_id = peer.blocktree.lastElem().id   #Finding parent ID by finding last block id in longest chain     
        b = block(self.blockid*1000 + peer.id,txns,t,peer.id,longest_chain_id,False) #Our generated block
    
        with open(file_block,"a") as ff:
            ff.write("Generating block " + str(self.blockid) + " at peer " + str(peer.id) + " at t= " + str(env.now) + "\n")
        e = event("forward block", t + timeout,b,peer.id) #Generating forward block event after the computed timeout
        self.event_queue.insert(e)
        
        yield self.env.timeout(0)

    
    def forward_block(self,env,peer,block):

        l = peer.blocktree.lastElem().id
        if l == block.previd: #Checking if the longest chain hasn't changed
            valid = True
            for txn in block.txnlist: #Checking block validity
                s = txn.src
                r = txn.dest
                amt = txn.amt
                if amt > peer.balances[s.id-1]:
                    valid = False
                    break 
            if valid: #If block is valid
                with open(file_block,"a") as ff:
                    ff.write("Generated block " + str(block.id) + " at peer " + str(peer.id) + " time = " + str(env.now) + " with txns " + str([x.id for x in block.txnlist]) + "\n")
                self.blockid += 1
                blocknumbers[peer.id - 1] += 1
                block.mod_txns() #Setting included field in the txns used as true
                peer.update_transactions() #Removing used txns from the txn pool
                for txn in block.txnlist: #Updating balance
                    s = txn.src
                    r = txn.dest
                    amt = txn.amt
                    peer.balances[s.id-1] -= amt
                    peer.balances[r.id-1] += amt
                peer.balances[peer.id-1] += 50 #Adding mining fee
                b,b1 = peer.blocktree.DFS(block.previd)
                peer.blocktree.addChildTree(b,block)   #Adding block to the peer's blockchain tree

                #Update longest_chain
                trees[peer.id] = peer.blocktree #Updating the value of blocktree. We'll use this in part 8
                #We maintain a the longest chain of a peer with a dictionary longest_chain for part 8. Here we are updating it
                root = peer.blocktree.getRoot()
                lpath = peer.blocktree.longestPath(root)
                n = len(lpath) - 1
                final = [lpath[n-i] for i in range(len(lpath))]
                longest_chain[peer.id] = final

                e = event("generate block",env.now,block,peer.id) #We continue to mine on this generated valid block
                self.event_queue.insert(e)                


                #Now we write about this block in the peer file containing info about all blocks in the tree
                filename = "Peer " + str(peer.id) + " blocks.txt" 
                current = add_time(start_time , int(env.now))
                depth = peer.blocktree.get_height(block.id)
                if block.previd == 0:
                    content = str(block.id) + ", " + str(depth) + ", " + str(start_time.day) + "-" + str(start_time.month) + "-" + str(start_time.year) + " " + str(current) + ", Genesis block\n"
                else:
                    content = str(block.id) + ", " + str(depth) + ", " + str(start_time.day) + "-" + str(start_time.month) + "-" + str(start_time.year) + " " + str(current) + ", " + str(block.previd) + "\n"
                with open(filename, "a") as f:
                    f.write(content)

                



                size = block.size() #Getting block size
                for p in connected[peer.id]: #Forwarding the block, similar to txns
                    if block.forwarded[peer.id-1][p-1] == False:
                        block.forwarded[peer.id-1][p-1] = True
                        block.forwarded[p-1][peer.id-1] = True
                        timeout = latency(peer.id-1,p-1,self.ro_ij,size,self.c) #Calculating latency: Size will be what we computed above
                        with open(file_block,"a") as ff:
                            ff.write("Forwarding block " + str(block.id) + " from peer " + str(peer.id) + " to peer " + str(p) + " at t= " + str(env.now) + " latency = " + str(timeout) + "\n")
                        e = event("recieve block",env.now + timeout,block,p) #Generating a recieve block event at the reciever after time latency
                        self.event_queue.insert(e)
            
            else:
                with open(file_block,"a") as ff:
                    ff.write("Block " + str(block.id) + " is invalid at peer " + str(peer.id) + "\n")

        else:
            with open(file_block,"a") as ff:
                ff.write("Mining for block " + str(block.id) + " invalid due to change in longest chain at peer " + str(peer.id) + " last block " + str(l) + " but parent is " + str(block.previd) + "\n")
        
        yield self.env.timeout(0)      


    def recieve_block(self,env,peer,block):
        if block not in peer.arrived: #If a block has already arrived, no need to process the same block again
            if(block.dummy == True): #Checking if block is a dummy, which is just a trigger to start block generation
                e = event("generate block",env.now,block,peer.id)
                self.event_queue.insert(e)

            else:
                with open(file_block,"a") as ff:
                    ff.write("Recieved block " + str(block.id) + " at peer " + str(peer.id) + " at t= " + str(env.now)  + "\n")
                block1,boolean = peer.blocktree.DFS(block.previd) #Checking if the parent block exists in the blockchain tree
                if boolean != False:
                    size = block.size()
                    valid = True
                    for txn in block.txnlist: #Checking validity of the recieved block
                        if txn in peer.transactions:
                            s = txn.src
                            r = txn.dest
                            amt = txn.amt
                            if amt > peer.balances[s.id-1]:
                                valid = False
                                break
                    if valid:
                        peer.update_transactions() 
                        for txn in block.txnlist: #Update balance of peers
                            s = txn.src
                            r = txn.dest
                            amt = txn.amt
                            peer.balances[s.id-1] -= amt
                            peer.balances[r.id-1] += amt
                        peer.balances[block.creatorid-1] += 50
                        peer.blocktree.addChildTree(block1,block)   #Add the block to the blockchain tree of the peer  
                        prev = block.previd
                        if prev in peer.pending: #If any children of the current block had arrived before then process them by creating a recieve event at the current time
                            for b in peer.pending[prev]:
                                e = event("recieve block",env.now,b,peer.id)
                                self.event_queue.insert(e)  

                        #Update longest_chain  

                        trees[peer.id] = peer.blocktree #Updating the value of blocktree. We'll use this in part 8
                        #We maintain a the longest chain of a peer with a dictionary longest_chain for part 8. Here we are updating it
                        root = peer.blocktree.getRoot()
                        lpath = peer.blocktree.longestPath(root)
                        n = len(lpath) - 1
                        final = [lpath[n-i] for i in range(len(lpath))]
                        longest_chain[peer.id] = final                        
                                  

                        #Now we write about this block in the peer file containing info about all blocks in the tree
                        filename = "Peer " + str(peer.id) + " blocks.txt" 
                        current = add_time(start_time , int(env.now))
                        depth = peer.blocktree.get_height(block.id)
                        if block.previd == 0:
                            content = str(block.id) + ", " + str(depth) + ", " + str(start_time.day) + "-" + str(start_time.month) + "-" + str(start_time.year) + " " + str(current) + ", Genesis block\n"
                        else:
                            content = str(block.id) + ", " + str(depth) + ", " + str(start_time.day) + "-" + str(start_time.month) + "-" + str(start_time.year) + " " + str(current) + ", " + str(block.previd) + "\n"
                        with open(filename, "a") as f:
                            f.write(content)

                                       
                        e = event("generate block",env.now,block,peer.id)
                        self.event_queue.insert(e)
                        for p in connected[peer.id]: #Forward the block to the remaining connections
                            if block.forwarded[peer.id-1][p-1] == False:
                                block.forwarded[peer.id-1][p-1] = True
                                block.forwarded[p-1][peer.id-1] = True
                                timeout = latency(peer.id-1,p-1,self.ro_ij,size,self.c)
                                with open(file_block,"a") as ff:
                                    ff.write("Forwarding block " + str(block.id) + " from peer " + str(peer.id) + " to peer " + str(p) + " at t= " + str(env.now) + " latency = " + str(timeout) + "\n")
                                e = event("recieve block",env.now + timeout,block,p)
                                self.event_queue.insert(e)

                    else: #In case block was invalid
                        with open(file_block,"a") as ff:
                            ff.write("Block " + str(block.id) + " is invalid at peer " + str(peer.id) + "\n")
                
                else: #In case block's parent hasn't arrived, we keep this block in the pending dictionary and process this block after the parent block arrives if its valid
                    prev = block.previd
                    if prev in peer.pending:
                        peer.pending.append(block)
                    else:
                        peer.pending[prev] = [block]  
            peer.arrived.append(block)              
            
            
                                            
        yield self.env.timeout(0)




    def simulate(self,env): #This function keeps on executing all the events in the queue in order of time of arrival of the events. It looks at the event type and then calls the corresponding function
        while True:
            e = self.event_queue.delete()
            yield env.timeout(e.time - env.now) #Incrementing simulation time to the time of the event to be processed
            if e.type == "generate transaction":
                env.process(self.generate_transaction(env,self.peers[e.peerid-1],False))

            elif e.type == "forward transaction":
                env.process(self.forward_transaction(self.peers[e.peerid-1],env,e.txnorblock))

            elif e.type == "recieve transaction":
                env.process(self.recieve_transaction(env,self.peers[e.peerid-1],e.txnorblock))

            elif e.type == "generate block":
                env.process(self.generate_block(env,self.peers[e.peerid-1]))
            
            elif e.type == "forward block":
                env.process(self.forward_block(env,self.peers[e.peerid-1],e.txnorblock))
            
            elif e.type == "recieve block":
                env.process(self.recieve_block(env,self.peers[e.peerid-1],e.txnorblock))


            yield env.timeout(0)



def peer_function(env): #Main function that will run in the simulation
    tk = [10000 for i in range(num_peers)]
    peer2peer = p2p(env,10,tk,0,1,peers,connected,ro_ij,c) #Creating peer 2 peer network object
    for peer in peer2peer.peers: #Generating dummy transactions that will start transaction generation in all the peers
        yield env.process(peer2peer.generate_transaction(env,peer,True))

    for peer in peer2peer.peers: #Generating dummy blocks that will start block generation in all the peers
        b = block(-1,[],0,0,0,True)
        yield env.process(peer2peer.recieve_block(env,peer,b))
    
    yield env.process(peer2peer.simulate(env)) #Calling simulate function that will run subsequent events
    
    

    

if __name__ == '__main__':
    z = 0.3 #Fraction of slow peers
    txn_id = 0 
    ro_ij = generate_uniform(10,500)
    b = [500 for i in range(num_peers)] #Balances of the peers
    peers = [peer(i+1,b) for i in range(num_peers)]  #Generating the peer list
    slow = random.sample(peers,int(num_peers*z)) #List with slow peers
    fast = [i for i in peers if i not in slow] #List with fast peers
    trees = {}
    c = [] #Matrix that will determine c_ij as per the latency formula
    for i in peers:
        temp = []
        for j in peers:
            if i==j:
                temp.append(0)
            else:
                if i in slow or j in slow:
                    temp.append(5)
                else:
                    temp.append(100)
        c.append(temp)
    
    s = [x.id for x in slow] #Slow peer ids
    f = [x.id for x in fast] #Fast peer ids
    connected = MakeConnections([i+1 for i in range(num_peers)],s,f,int(num_peers / 2)) #Connections matrix (Refer to connections.py for the logic)

    start_time = datetime.now() #Start time of the simulation

    blocknumbers = [0 for i in range(num_peers)] #Denotes number of blocks generated by each peer
    longest_chain = {}  #This will store longest chain for every block


    env = simpy.Environment()  #Creating the environment of the simulation
    env.process(peer_function(env)) #Running peer function in the environment
    env.run(until=9000)  #Run untill timeout

    for i in range(num_peers):
        longest_ids = [x.id for x in longest_chain[i+1]][1:] #List of longest ids in the longest chain
        length = len(longest_ids)
        with open("Peer" + str(i+1) + "_Analysis.txt", "a") as f1:
            f1.write("The longest chain is of length " + str(length) + " consists of blocks with id(s) " + str(longest_ids) + "\n")
        contri = [0 for j in range(num_peers)]
        for item in longest_chain[i+1][1:]:
            contri[item.creatorid-1] += 1
        # fraction = []
        # for j in range(num_peers):
        #     fraction.append(float(contri[j] / blocknumbers[j]))
        with open("Peer" + str(i+1) + "_Analysis.txt", "a") as f1: #Updating analysis doc
            for j in range(num_peers):
                f1.write("Peer " + str(j+1) + " contributed " + str(contri[j]) + " out of total " + str(blocknumbers[j]) + "\n")
            f1.write("Slow nodes: " + str(s) + "\n")
            f1.write("Fast nodes: " + str(f) + "\n")

        

    for i in range(num_peers):
        trees[i+1].visualize()
    



