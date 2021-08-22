from utils import *
import threading
import random
import simpy

peer1_timestamp = {}
peer2_timestamp = {}
amt_timestamp = {}
connected = {}
threads = []
txn_id = 0
transactions = []
num_peers = 10

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
  
    def delete(self):
        try:
            min = 0
            for i in range(len(self.queue)):
                if self.queue[i] > self.queue[min]:
                    min = i
            item = self.queue[min]
            del self.queue[min]
            del peer1_timestamp[item]
            del peer2_timestamp[item]
            del amt_timestamp[item]
            return item
        except IndexError:
            print()
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
        self.txn = []

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
    def __init__(self,env,tx,peers,connected,ro_ij,c):
        self.env = env
        self.event_queue = PriorityQueue()
        self.tx = tx
        self.peers = peers
        self.connected = connected
        self.ro_ij = ro_ij
        self.c = c
        #self.peers = simpy.Resource(env,num_peers)

        def generate_transaction(env,peer,p2p):
            timeout = generate_exponential(self.tx)
            y = select_random(self.peers)
            while y != peer:
                y = select_random(self.peers)
            txn = transaction(env,y,5,txn_id)
            txn_id += 1
            e = event("forward",env.now + timeout,txn,peer.id)
            event_queue.insert(e)
            #yield self.env.timeout(timeout)

        def forward_transaction(peer,env,txn):
            for p in connected[peer]:
                if txn.forwarded[peer-1][p-1] == False:
                    txn.forwarded[peer-1][p-1] = True
                    txn.forwarded[p-1][peer-1] = True
                    timeout = latency(peer-1,p-1,self.ro_ij,1,self.c)
                    e = event("recieve",env.now + time,p)
                    

        def recieve_transaction(env,peer,txn):
            for p in connected[peer]:
                if txn.forwarded[peer-1][p-1] == False:
                    txn.forwarded[peer-1][p-1] = True
                    txn.forwarded[p-1][peer-1] = True
                    timeout = latency(peer-1,p-1,self.ro_ij,1,self.c)
                    e = event("recieve",env.now + time,p)            



def peer_function(env,peer,p2p):
    while true:
        yield env.process(p2p.generate_transaction(env.peer,p2p))


        



def initialize_peers(n,b):
    balance = []
    id = []
    for i in range(n):
        balance.append(b)
        id.append(i+1)
    return (balance,id)

# def generate_transaction(x,y,tx):
#     t = generate_exponential(tx)
#     peer1_timestamp[t] = x
#     peer2_timestamp[t] = y
#     amt_timestamp[t] = 5
#     event_queue.insert(t)
#     transactions.append(transaction(x,y,5))
#     print(str(x) + " pays " + str(i) + ' 5' + " coins at t: " + str(t))



# def init_forwarding(n):
#     for i in range(n):
#         for j in range(n):
#             forwarded[i][j] = False    

# def forward(id,f,connected):
#     for i in connected[id]:
#         if forwarded[id-1][i-1] == False:
#             print(str(id) + "   " + str(i))
#             forwarded[id-1][i-1] = True
#             forwarded[i-1][id-1] = True
#     for i in peers:
#         for j in connected[i]:
#             if forwarded[i-1][j-1] == False:
#                 print(str(i) + "   " + str(j))
#                 forwarded[i-1][j-1] = True
#                 forwarded[j-1][i-1] = True





if __name__ == '__main__':
    n = 5
    z = 0.3
    ro_ij = generate_uniform(10,500)
    peers = [(i+1) for i in range(n)]
    slow = random.sample(peers,int(n*z))
    print(slow)
    fast = [i for i in peers if i not in slow]
    print(fast)
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
    
    
    for i in range(n):
        temp = [False for i in range(n)]
        forwarded.append(temp)    
    
    for i in range(n):
        l = [(i+k) % n for k in [2,3]]
        connected[i+1] = l
    print(connected[1])


    # for i in range(n):
    #     t = threading.Thread(target=start_transactions, args = (i,tx,peers,))
    #     t.start()
    #     threads.append(t)

