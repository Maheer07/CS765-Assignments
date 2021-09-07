import networkx as nx
import matplotlib.pyplot as plt

# Ref:
# https://gist.github.com/goldsamantha/36767f42c25ae6b97fbc
class Node: #Component of a tree. This will be a block in our implementation
    def __init__(self,val,parent=None,children=None):
        self.val=val    #Value (block for us)
        self.parent=parent  #Parent node
        if children is None:    #Node children
            self.children = []
        else:
            self.children = children

    #Setting and getting data
    def getData(self):  
        return self.val

    def setData(self,val):
        self.val=val
        return
    #Setting and getting node children
    def getChildren(self):
        return self.children

    def addChild(self,node):
        self.children.append(node)
        return
    #Setting and getting node parents
    def getParent(self):
        return self.parent

    def setParent(self,val):
        self.parent=val
        return

class GenralTree:   #Basic tree

    def __init__(self):
        self.root = None    #Root node
        self.longest=0      #Length of longest path
        self.visual = []    #Used for visualization using networkx

    def getLongest(self):
        return self.longest

    def getRoot(self):
        return self.root

    def setRoot(self,root):
        nd=Node(root)
        self.root=nd


    def addChildTree(self,parent,val):  #Add child node with value val to the parent 
        nd = Node(val, parent)
        parent.addChild(nd)
        p = parent.getData().id
        c = nd.getData().id
        self.visual.append([p, c])
        return nd

    def DFS(self,val):  #Checks if a node exists in the tree and if yes, returns it
        stack=[]
        curr=self.root
        stack.append(curr)

        while len(stack)>0:
            curr = stack.pop()
            if curr.getData().id == val:
                return (curr,True)
            else:
                [stack.append(elem) for elem in curr.getChildren()]
        return (Node(0),False)

    def get_height(self,val):   #Height of a node with value val
        stack=[]
        h = 0
        curr=self.root
        stack.append(curr)

        while len(stack)>0:
            curr = stack.pop()
            if curr.getData().id == val:
                return h
            else:
                [stack.append(elem) for elem in curr.getChildren()]
                h += 1
        return -1       

    def findLongest(self, Node,height): #Updates longest path length in the tree
        #print(len(Node.getChildren()))
        if len(Node.getChildren())==0:
            self.longest=max(height,self.longest)
            return 
        else:
            [self.findLongest(elem,height+1) for elem in Node.getChildren()]

    def longestPath(self, node):    #Returns longest path in the tree (used in longest chain)
        if (len(node.getChildren()) == 0):
            return [node.getData()]
        max_len = -1
        ind = -1
        i = 0
        temp = [self.longestPath(elem) for elem in node.getChildren()]
        for x in temp:
            if len(x) > max_len:
                max_len = len(x)
                x.append(node.getData())
                ind = i
            i += 1
        return temp[ind]

    def lastElem(self): #Last node in the longest path
        return self.longestPath(self.root)[0]  

    def visualize(self):    #Displaying the tree(used at the end)
        G = nx.Graph()
        G.add_edges_from(self.visual)
        nx.draw_networkx(G)
        plt.show()         




# def main():
#     # tree = GenralTree()
#     # tree.SetRoot(2)
#     # curr=tree.getRoot()
#     # child1=tree.addChildTree(curr,3)
#     # child2=tree.addChildTree(curr,4)
#     # child3=tree.addChildTree(curr,5)
#     # child11=tree.addChildTree(child1,6)
#     # child12=tree.addChildTree(child1,7)
#     # child21=tree.addChildTree(child2,8)
#     # child211=tree.addChildTree(child21,9)
#     # children1=child1.getChildren()
#     #for i in children1:
#     #    print(i.getData())
#     #tree.printTree()
#     #search = int(input())
#     #mynode=tree.DFS(search)
#     #tree.addChildTree(mynode,10)

#     #tree.DFS(6)
#     #ans=-1
#     # tree.findLongest(curr,0)
#     # print(tree.getLongest())

#     tree = GenralTree()
#     tree.setRoot(0)
#     curr=tree.getRoot()
#     child1=tree.addChildTree(curr,1)
#     child2=tree.addChildTree(curr,2)
#     child3=tree.addChildTree(curr,3)
#     child31=tree.addChildTree(child3,4)
#     child311=tree.addChildTree(child31,5)
#     tree.findLongest(curr,0)
#     l = tree.longestPath(curr)
#     print(type(l))
#     print(l)
#     n = len(l) - 1
#     l1 = [l[n - i] for i in range(len(l))]
#     print(l1)
#     print(tree.getLongest())
#     child312=tree.addChildTree(child31,6)
#     child3121=tree.addChildTree(child312,7)
#     tree.findLongest(curr,0)
#     print(tree.getLongest())
#     child11=tree.addChildTree(child1,8)
#     child111=tree.addChildTree(child11,9)
#     child1111=tree.addChildTree(child111,10)
#     child11111=tree.addChildTree(child1111,11)
#     tree.findLongest(curr,0)
#     print(tree.getLongest())
#     print(tree.lastElem())
#     tree.visualize()

# if __name__ == '__main__':
#     main()