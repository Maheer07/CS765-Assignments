# Ref:
# https://gist.github.com/goldsamantha/36767f42c25ae6b97fbc
class Node:
    def __init__(self,val,parent=None,children=None):
        self.val=val
        self.parent=parent
        if children is None:
            self.children = []
        else:
            self.children = children

    def getData(self):
        return self.val

    def setData(self,val):
        self.val=val
        return
    
    def getChildren(self):
        return self.children

    def addChild(self,node):
        self.children.append(node)
        return
    
    def getParent(self):
        return self.parent

    def setParent(self,val):
        self.parent=val
        return

class GenralTree:

    def __init__(self):
        self.root = None
        self.longest=0

    def getLongest(self):
        return self.longest

    def getRoot(self):
        return self.root

    def setRoot(self,root):
        nd=Node(root)
        self.root=nd

    #def isEmpty:

    def addChildTree(self,parent,val):
        nd = Node(val, parent)
        parent.addChild(nd)
        return nd

    def printTree(self):#has bugs
        stack=[]
        curr=self.root
        stack.append(curr)

        while len(stack)>0:
            print(curr.getData())
            curr = stack[-1]
            stack.pop()
            [stack.append(elem) for elem in curr.getChildren()]
        return

    def DFS(self,val):
        stack=[]
        curr=self.root
        stack.append(curr)

        while len(stack)>0:
            curr = stack.pop()
            print(curr.getData())
            if curr.getData() == val:
                print("Eureka! found it")
                return curr
            else:
                [stack.append(elem) for elem in curr.getChildren()]
        print("OOPS! not found")
        return -1

    def findLongest(self, Node,height):
        #print(len(Node.getChildren()))
        if len(Node.getChildren())==0:
            self.longest=max(height,self.longest)
            return 
        else:
            [self.findLongest(elem,height+1) for elem in Node.getChildren()]

    def longestPath(self, node):
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

    def lastElem(self):
        return self.longestPath(self.root)[0]            




def main():
    # tree = GenralTree()
    # tree.SetRoot(2)
    # curr=tree.getRoot()
    # child1=tree.addChildTree(curr,3)
    # child2=tree.addChildTree(curr,4)
    # child3=tree.addChildTree(curr,5)
    # child11=tree.addChildTree(child1,6)
    # child12=tree.addChildTree(child1,7)
    # child21=tree.addChildTree(child2,8)
    # child211=tree.addChildTree(child21,9)
    # children1=child1.getChildren()
    #for i in children1:
    #    print(i.getData())
    #tree.printTree()
    #search = int(input())
    #mynode=tree.DFS(search)
    #tree.addChildTree(mynode,10)

    #tree.DFS(6)
    #ans=-1
    # tree.findLongest(curr,0)
    # print(tree.getLongest())

    tree = GenralTree()
    tree.setRoot(0)
    curr=tree.getRoot()
    child1=tree.addChildTree(curr,1)
    child2=tree.addChildTree(curr,2)
    child3=tree.addChildTree(curr,3)
    child31=tree.addChildTree(child3,4)
    child311=tree.addChildTree(child31,5)
    tree.findLongest(curr,0)
    print(tree.getLongest())
    child312=tree.addChildTree(child31,6)
    child3121=tree.addChildTree(child312,7)
    tree.findLongest(curr,0)
    print(tree.getLongest())
    child11=tree.addChildTree(child1,8)
    child111=tree.addChildTree(child11,9)
    child1111=tree.addChildTree(child111,10)
    child11111=tree.addChildTree(child1111,11)
    tree.findLongest(curr,0)
    print(tree.getLongest())
    print(tree.lastElem())

if __name__ == '__main__':
    main()