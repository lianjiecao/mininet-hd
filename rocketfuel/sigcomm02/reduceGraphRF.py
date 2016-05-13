import sys

def retEdgeNodes(cont):
    eList = []
    for line in cont:
        tokens = line.split()
        if len(tokens) == 4:
            eList.append(tokens[0])

    return eList

def selectNext(cont):
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
    # print 'Number of nodes:', len(cont), len(set(nodes)), len(set(neighbors))
    # print 'Number of edges:', nEdge
    # print 'Total weight:   ', w


if __name__ == '__main__':
    fName = sys.argv[1]
    targetSize = int(sys.argv[2])
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
    # print retEdgeNodes(cont)
