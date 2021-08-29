from utils import *
from genral_tree import *
import threading
import random
import simpy
import os
import time


connected = {}
txn_id = None
transactions = []
c = []
num_peers = 5
peer2peer = None
env = None

#Took this class from https://www.geeksforgeeks.org/priority-queue-in-python/ with a change in delete function because of unfamiliarity with python data structures
class PriorityQueue(object):
    def __init__(self):
        self.queue = []
  
    def __str__(self):
        return ' '.join([str(i) for i in self.queue])
  
    def isEmpty(self):
        return len(self.queue) == 0
  
    def insert(self, data):
        self.queue.append(data)
        #print(len(self.queue))

  
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
            #print()
            exit()

class transaction:
    def __init__(self,src,dest,amt,id):
        self.src = src
        self.dest = dest
        self.amt = amt
        self.id = id
        self.included = False
        self.forwarded = [[False for i in range(num_peers)] for i in range(num_peers)]

class block:
    def __init__(self,id,txnlist,time,creatorid,previd,dummy):
        self.id = id
        self.txnlist = txnlist
        self.time = time
        self.creatorid = creatorid
        self.previd = previd
        self.dummy = dummy
        self.forwarded = [[False for i in range(num_peers)] for i in range(num_peers)]

    def size(self):
        return 1 + len(self.txnlist)

    def mod_txns(self):
        for t in self.txnlist:
            t.included = True

class peer:
    def __init__(self,id,balances):
        self.id = id
        self.balances = balances
        self.transactions = []
        self.blocktree = GenralTree()
        self.blocktree.setRoot(block(0,[],0,self.id,0,False))
        self.root = self.blocktree.getRoot()
        self.pending = {}

    def update_transactions(self):
        l = [i for i in self.transactions if i.included == False]
        self.transactions = l

class event:
    def __init__(self,type,time,txn,peerid):
        self.type = type
        self.time = time
        self.txnorblock = txn
        self.peerid = peerid

    def __gt__(self,other):
        if self.time < other.time:
            return True
        else:
            return False


def latency(i,j,ro_ij,size,c):
    #size is in kb
    c_ij = c[i][j]
    d_ij = generate_exponential(96/c_ij)
    t = d_ij + ro_ij + (size / c_ij) #t is in ms
    return t



class p2p(object):
    def __init__(self,env,tx,tk,txn_id,blockid,peers,connected,ro_ij,c):
        self.env = env
        self.time_tx = tx
        self.time_tk = tk
        self.txn_id = txn_id
        self.blockid = blockid
        self.event_queue = PriorityQueue()
        self.peers = peers
        self.connected = connected
        self.ro_ij = ro_ij
        self.c = c

    def generate_transaction(self,env,peer,dummy):
                
        timeout = generate_exponential(self.time_tx)
        t = env.now
        y = select_random(self.peers)
        while y == peer:
            y = select_random(self.peers)
        txn = transaction(peer,y,5,self.txn_id)
        if dummy==False:
            #print("Generating transaction " + str(self.txn_id) + " at peer " + str(peer.id) + " at t= " + str(env.now))
            self.txn_id += 1
            peer.transactions.append(txn)
            e = event("forward transaction",t,txn,peer.id)
            self.event_queue.insert(e)
        e = event("generate transaction",t+timeout,txn,peer.id)
        self.event_queue.insert(e)

        yield self.env.timeout(0)


    def forward_transaction(self,peer,env,txn):
        for p in connected[peer.id]:
            if txn.forwarded[peer.id-1][p-1] == False:
                txn.forwarded[peer.id-1][p-1] = True
                txn.forwarded[p-1][peer.id-1] = True
                timeout = latency(peer.id-1,p-1,self.ro_ij,1,self.c)
                #print("Forwarding transaction " + str(txn.id) + " from peer " + str(peer.id) + " to peer " + str(p) + " at t= " + str(env.now) + " latency = " + str(timeout))
                e = event("recieve transaction",env.now + timeout,txn,p)
                self.event_queue.insert(e)
        
        yield self.env.timeout(0)

    def recieve_transaction(self,env,peer,txn):
        #print("Recieved transaction " + str(txn.id) + " at peer " + str(peer.id) + " at t= " + str(env.now))
        peer.transactions.append(txn)
        for p in connected[peer.id]:
            if txn.forwarded[peer.id-1][p-1] == False:
                txn.forwarded[peer.id-1][p-1] = True
                txn.forwarded[p-1][peer.id-1] = True
                timeout = latency(peer.id-1,p-1,self.ro_ij,1,self.c)
                #print("Forwarding transaction " + str(txn.id) + " from peer " + str(peer.id) + " to peer " + str(p) + " at t= " + str(env.now) + " latency = " + str(timeout))
                e = event("recieve transaction",env.now + timeout,txn,p)
                self.event_queue.insert(e)  

        yield self.env.timeout(0)

    def generate_block(self,env,peer):

        timeout = generate_exponential(self.time_tk)
        t = env.now
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
        longest_chain_id = peer.blocktree.lastElem().id        
        b = block(self.blockid,txns,t,peer.id,longest_chain_id,False)
    
        print("Generating block " + str(self.blockid) + " at peer " + str(peer.id) + " at t= " + str(env.now))
        e = event("forward block", t + timeout,b,peer.id)
        self.event_queue.insert(e)
        
        yield self.env.timeout(0)

    
    def forward_block(self,env,peer,block):

        l = peer.blocktree.lastElem().id
        print("Longest chain last id = " + str(l))
        if l == block.previd:
            valid = True
            for txn in block.txnlist:
                s = txn.src
                r = txn.dest
                amt = txn.amt
                if amt > peer.balances[s.id-1]:
                    valid = False
                    break
            if valid:
                print("Generated block " + str(block.id) + " at peer " + str(peer.id) + " time = " + str(env.now))
                self.blockid += 1
                block.mod_txns()
                peer.update_transactions()
                for txn in block.txnlist:
                    s = txn.src
                    r = txn.dest
                    amt = txn.amt
                    peer.balances[s.id-1] -= amt
                    peer.balances[r.id-1] += amt
                peer.balances[peer.id-1] += 50
                b,b1 = peer.blocktree.DFS(block.previd)
                peer.blocktree.addChildTree(b,block)   
                size = block.size()
                for p in connected[peer.id]:
                    if block.forwarded[peer.id-1][p-1] == False:
                        block.forwarded[peer.id-1][p-1] = True
                        block.forwarded[p-1][peer.id-1] = True
                        timeout = latency(peer.id-1,p-1,self.ro_ij,size,self.c)
                        print("Forwarding block " + str(block.id) + " from peer " + str(peer.id) + " to peer " + str(p) + " at t= " + str(env.now) + " latency = " + str(timeout))
                        e = event("recieve block",env.now + timeout,block,p)
                        self.event_queue.insert(e)
            
            else:
                print("Block " + str(block.id) + " is invalid at peer " + str(peer.id))

        else:
            print("Mining for block " + str(block.id) + " invalid due to change in longest chain at peer " + str(peer.id))
        
        yield self.env.timeout(0)      


    def recieve_block(self,env,peer,block):
        print("Recieved block " + str(block.id) + " at peer " + str(peer.id) + " at t= " + str(env.now))
        if(block.dummy == True):
            e = event("generate block",env.now,block,peer.id)
            self.event_queue.insert(e)

        else:
            block1,boolean = peer.blocktree.DFS(block.previd)
            if boolean != False:
                size = block.size()
                valid = True
                for txn in block.txnlist:
                    s = txn.src
                    r = txn.dest
                    amt = txn.amt
                    if amt > peer.balances[s.id-1]:
                        valid = False
                        break
                if valid:
                    peer.update_transactions()
                    for txn in block.txnlist:
                        s = txn.src
                        r = txn.dest
                        amt = txn.amt
                        peer.balances[s.id-1] -= amt
                        peer.balances[r.id-1] += amt
                    peer.balances[block.creatorid-1] += 50
                    peer.blocktree.addChildTree(block1,block)    
                    prev = block.previd
                    if prev in peer.pending:
                        for b in peer.pending[prev]:
                            e = event("recieve block",env.now,b,peer.id)
                            self.event_queue.insert(e)              

                    #Recieve all the pending blocks of this node                    
                    e = event("generate block",env.now,block,peer.id)
                    self.event_queue.insert(e)
                    for p in connected[peer.id]:
                        if block.forwarded[peer.id-1][p-1] == False:
                            block.forwarded[peer.id-1][p-1] = True
                            block.forwarded[p-1][peer.id-1] = True
                            timeout = latency(peer.id-1,p-1,self.ro_ij,size,self.c)
                            print("Forwarding block " + str(block.id) + " from peer " + str(peer.id) + " to peer " + str(p) + " at t= " + str(env.now) + " latency = " + str(timeout))
                            e = event("recieve block",env.now + timeout,block,p)
                            self.event_queue.insert(e)

                else:
                    print("Block " + str(block.id) + " is invalid at peer " + str(peer.id))
            
            else:
                prev = block.previd
                if prev in peer.pending:
                    peer.pending.append(block)
                else:
                    peer.pending[prev] = [block]                
            
            
                                            
        yield self.env.timeout(0)




    def simulate(self,env):
        while True:
            e = self.event_queue.delete()
            yield env.timeout(e.time - env.now)
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



def peer_function(env):
    peer2peer = p2p(env,100,10000,0,1,peers,connected,ro_ij,c)
    for peer in peer2peer.peers:
        yield env.process(peer2peer.generate_transaction(env,peer,True))

    for peer in peer2peer.peers:
        b = block(1,[],0,0,0,True)
        yield env.process(peer2peer.recieve_block(env,peer,b))
        env.process(peer2peer.simulate(env))
    yield env.timeout(0)

def helper(i,num_peers):
    l = []
    for k in [2,3]:
        if (i+k) > num_peers:
            l.append(i+k - num_peers)
        else:
            l.append(i+k)
    return l


    

if __name__ == '__main__':
    z = 0.3
    txn_id = 0
    ro_ij = generate_uniform(10,500)
    b = [500 for i in range(num_peers)]
    peers = [peer(i+1,b) for i in range(num_peers)]
    slow = random.sample(peers,int(num_peers*z))
    fast = [i for i in peers if i not in slow]
    c = []
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
    
    
    for i in range(num_peers):
        connected[i+1] = helper(i,num_peers)

    env = simpy.Environment()
    env.process(peer_function(env))
    env.run(until=9000)
    



