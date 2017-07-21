import sys, random

def graphToAdjlist(fName):
    f = open(fName, 'r')
    cont = [x for x in f.read().split('\n') if x is not '']
    adjList = {}
    remainNodes = []
    for line in cont:
        tokens = line.split()
        adjList[tokens[0]] = [x for x in tokens[1:] if x != tokens[0]]
    f.close()
    return adjList

def retEdgeNodes(cont):
    eList = []
    for line in cont:
        tokens = line.split()
        if len(tokens) == 4:
            eList.append(tokens[0])

    return eList

def selectNext(cont):
    ''' 
    Select next node with least degree.
    '''
    n = ['', 0]
    for line in cont:
        tokens = line.split()
        if n[0] is '' or len(tokens) < n[1]:
            n = [tokens[0], len(tokens)]
            # print n
    return n[0]

def removeNode(cont, n):
    # print 'Removing node:', n
    newCont = []
    for line in cont:
        tokens = line.split()
        # nodeList = [tokens[i] for i in range(0,len(tokens),2)] # Nodes with out edge weights
        # print 'Full list:', tokens
        # print 'Node list:', nodeList
        if n in tokens and n != tokens[0]:
            # print 'Found', n
            # Node can only appear once in a line
            idx = tokens.index(n)
            tokens.pop(idx) # Remove the node
            # tokens.pop(idx) # Remove the edge weight
            newCont.append(' '.join(tokens))
            # print 'Removed:', ' '.join(tokens)
        elif n not in tokens:
            newCont.append(line)

    return newCont

def updateWeights(cont):
    newCont = []
    for line in cont:
        tokens = line.split()
        tokens[1] = str(sum([int(tokens[i]) for i in range(3,len(tokens),2)]))
        newCont.append(' '.join(tokens))

    return newCont


def printGraph(cont):
    nEdge = 0
    # w = 0
    nodes = []
    neighbors = []
    for l in cont:
        tokens = l.split()
        nEdge += (len(tokens)-2)
        nodes.append(tokens[0])
        neighbors.extend(tokens[2:])
        # w += int(tokens[1])
        print l
    print 'Number of nodes:', len(cont), len(set(nodes)), len(set(neighbors))
    print 'Number of edges:', nEdge
    # print 'Total weight:   ', w


def reduceGraph(fName, targetSize):

    f = open(fName, 'r')
    cont = f.read().split('\n')
    cont = [x for x in cont if x is not '']

    currSize = len(cont)
    deleted = []
    # printGraph(cont)
    while currSize > targetSize:
        # eList = retEdgeNodes(cont)
        n = selectNext(cont)
        # print 'Current Size: %d, target size: %d' % (currSize, targetSize)
        # print 'Edge nodes: %s', (' '.join(eList))
        # print 'Next to remove:', n
        cont = removeNode(cont, n)
        deleted.append(n)
        currSize = len(cont)

    printGraph(cont)
    f.close()
    # print retEdgeNodes(cont)

def convertToDOT(adjList):
    links = []
    for key in adjList:
        for nb in adjList[key][1:]:
            l = sorted([key, nb])
            if l not in links:
                links.append(l)
                print '    %s -- %s;' % (l[0], l[1])

def printAdjList(adjList):
    for key in sorted(adjList.keys()):
        print key, ' '.join(adjList[key])

def graphStat(adjList):
    nodeNum, edgNum = len(adjList), sum([len(x)-1 for x in adjList.values()])/2
    print 'Node: %d, edge: %d' % (nodeNum, edgNum)
    return [nodeNum, edgNum]

def nodeDegrees(adjList):
    degreeList = {}
    for key in adjList:
        print '%s: %d' % (key, len(adjList[key])-1)
        degreeList.setdefault(len(adjList[key])-1, []).append(key)

    for i in degreeList:
        print '%d edges: %d => %s' % (i, len(degreeList[i]), degreeList[i])
    graphStat(adjList)

def collapseNodes(adjList, node, remainNodes):
    avaNbs = [x for x in adjList[node][1:] if x in remainNodes]
    if avaNbs == []:
        return None
    nb = random.choice(avaNbs)
    # print '*** Collapse', node, nb, '***'
    # print node, adjList[node]
    # print nb, adjList[nb]
    adjList[node].remove(nb) # remove the target nb from target node's neighbor list
    adjList[nb].remove(node) # remove the target node from target nb's neighbor list
    if adjList[node][0] != adjList[nb][0]:
        adjList[node][0] = 'bb'
    if len(adjList[nb]) > 1: # if the target nb has other neighbors
        for n in [x for x in adjList[nb][1:] if x not in adjList[node]]: 
            adjList[node].append(n) # add them to target node's neighbor list
    del adjList[nb] # remove the selected nb from graph

    for key in adjList: # update related connectivities
        if nb in adjList[key] and node in adjList[key]: # a node connects to both
            adjList[key].remove(nb)
        elif nb in adjList[key]:
            adjList[key].remove(nb)
            adjList[key].append(node)
    
    return nb


def collapseGraph(fName, n=1):
    '''
    Use random matching to collapse a graph
    '''

    adjList = graphToAdjlist(sys.argv[1])
    graphStat(adjList)
    
    print 'Coarsened graphs:'
    for i in range(n):
        remainNodes = adjList.keys()
        while remainNodes:
            next = random.choice(remainNodes)
            nb = collapseNodes(adjList, next, remainNodes)
            remainNodes.remove(next)
            if nb:
                remainNodes.remove(nb)
            # print 'Remain list:', remainNodes

        newCont = ''
        for key in sorted(adjList.keys()):
            newCont = newCont + key + ' ' + ' '.join(adjList[key]) + '\n'  #'%s %s\n' % (key, ' '.join(adjList[key])
        printAdjList(adjList)
        graphStat(adjList)
        # fNew = open('%d-%s' % (len(adjList), fName),'w')
        # fNew.write(newCont)
        # fNew.close()


if __name__ == '__main__':

    adjList = graphToAdjlist(sys.argv[1])
    # reduceGraph(sys.argv[1], int(sys.argv[2]))
    # graphStat(sys.argv[1])
    collapseGraph(sys.argv[1], int(sys.argv[2]))
    # nodeDegrees(adjList)
    # convertToDOT(adjList)
