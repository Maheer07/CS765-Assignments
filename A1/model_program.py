from utils import *
import threading
import random
import simpy
import time


connected = {}
txn_id = None
transactions = []
c = []
num_peers = 10
changed = False
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

class peer:
    def __init__(self,id):
        self.id = id
        self.balance = 50
        self.transactions = []

    def update_transactions(self):
        l = [i for i in self.transactions if i.included == False]
        self.transactions = l

class event:
    def __init__(self,type,time,txn,peerid):
        self.type = type
        self.time = time
        self.txn = txn
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
    def __init__(self,env,tx,txn_id,peers,connected,ro_ij,c):
        self.env = env
        self.tx = tx
        self.txn_id = txn_id
        self.event_queue = PriorityQueue()
        self.peers = peers
        self.connected = connected
        self.ro_ij = ro_ij
        self.c = c
        #self.peers = simpy.Resource(env,num_peers)

    def generate_transaction(self,env,peer,p2p,dummy):
        
        #print("Hi")
        timeout = generate_exponential(self.tx)
        t = env.now
        #print("time " + str(t) + "  " + str(timeout))
        y = select_random(self.peers)
        while y == peer:
            y = select_random(self.peers)
        txn = transaction(env,y,5,self.txn_id)
        
        if dummy==False:
            self.txn_id += 1
            peer.transactions.append(txn)
            self.tx.append(txn)
            e = event("forward",t,txn,peer.id)
            self.event_queue.insert(e)
        e = event("generate",t+timeout,txn,peer.id)
        self.event_queue.insert(e)
        
        #print(self.event_queue.__str__())
        yield self.env.timeout(0)
        #yield peer.id

    def forward_transaction(self,peer,env,txn):
        for p in connected[peer]:
            if txn.forwarded[peer-1][p-1] == False:
                txn.forwarded[peer-1][p-1] = True
                txn.forwarded[p-1][peer-1] = True
                timeout = latency(peer-1,p-1,self.ro_ij,1,self.c)
                e = event("recieve",env.now + timeout,txn,p.id)
                self.event_queue.insert(e)

    def recieve_transaction(self,env,peer,txn):
        peer.transactions.append(txn)
        for p in connected[peer]:
            if txn.forwarded[peer-1][p-1] == False:
                txn.forwarded[peer-1][p-1] = True
                txn.forwarded[p-1][peer-1] = True
                timeout = latency(peer-1,p-1,self.ro_ij,1,self.c)
                e = event("recieve",env.now + timeout,txn,p.id)
                self.event_queue.insert(e)  


    def simulate(self,env):
        while True:
            e = self.event_queue.delete()
            print(e.type + " " + str(e.time) + " " + str(e.peerid) + " " + str(e.txn.dest.id))




def peer_function(env):
    peer2peer = p2p(env,0.01,0,peers,connected,ro_ij,c)
    for peer in peer2peer.peers:
        yield env.process(peer2peer.generate_transaction(env,peer,peer2peer,True))
    changed = True
    #env.timeout(50)
    #time.sleep(10)
    env.process(peer2peer.simulate(env))
    yield env.timeout(0)

    

if __name__ == '__main__':
    z = 0.3
    txn_id = 0
    ro_ij = generate_uniform(10,500)
    peers = [peer(i+1) for i in range(num_peers)]
    slow = random.sample(peers,int(num_peers*z))
    #print(slow)
    fast = [i for i in peers if i not in slow]
    #print(fast)
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
        l = [(i+k) % num_peers for k in [2,3]]
        connected[i+1] = l
    env = simpy.Environment()
    #print(env.now)
    env.process(peer_function(env))
    #print(env.now)
    env.run(until=900000000)
    




    # for i in range(n):
    #     t = threading.Thread(target=start_transactions, args = (i,tx,peers,))
    #     t.start()
    #     threads.append(t)

