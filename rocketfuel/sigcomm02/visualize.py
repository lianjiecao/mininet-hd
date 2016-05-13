import sys

fName = sys.argv[1]
f = open(sys.argv[1],'r')
cont = [x for x in f.read().split('\n') if x != '']
edgeSw = []
links = []
for line in cont:
    tokens = line.split()
    for i in range(2, len(tokens), 2):
        if sorted([tokens[0], tokens[i]]) not in links:
            links.append(sorted([tokens[0], tokens[i]]))
    if len(tokens) == 4:
        edgeSw.append(line)

print 'graph %s {' % (fName.split('.')[0])
for l in links:
    print '    %s -- %s' % (l[0], l[1])
print '}'
print len(edgeSw)

