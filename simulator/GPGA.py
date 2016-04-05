
from collections import namedtuple
from operator import itemgetter
from mininet.net import Mininet
from mininet.node import UserSwitch, OVSKernelSwitch
from mininet.topo import Topo
from mininet.log import lg
from mininet.util import irange
import random
import math
import sys
import subprocess, os, logging
import time


#Defining sample graph

#containers = [1000, 1000, 1000, 2000]
#containers = [300, 400, 400, 500]
#containers = [240, 400, 380, 450]
#containers = [200, 360, 320, 400]
#containers = [300, 400, 400, 650]

logging.basicConfig(level=logging.INFO)
class myTopo(Topo):
	def __init__(self, **opts):
		Topo.__init__(self, **opts)


class Clustering:
	def __init__(self,topologies, tunnels):
		self.topos = topologies
		self.tunnels = tunnels
    
	def getTunnels(self):
		return self.tunnels

	def getTopos(self):
		return self.topos



class Partitioner():

###########################################################
# 				INITIALAZE THE CLASS	
###########################################################	

	def __init__(self,):
		self.logger = logging.getLogger(__name__)
		
		self.cuts = 0			#number of available containers
		self.containers = []	#capacity of containers

		self.childCounter = 0
		self.firstGenGrace = 1.3 # this is how much we can go over the original capacities for the first generation
		self.underflow = False  # indicates if we have more capacity than the weight of the topology
		self.percentOfOldGen = 0.2 #how much of the prev generation is picked in the new generation
		self.crossoverPoints = 60
		self.randomPoints = 0	#number of random points in crossover
		self.mutationRate = 0.7
		self.numMutations = 10
		self.stopCount = 20	#when to stop
		self.generationStep = 120
		self.populationNum = 20   #each generation population
		self.start = None		#start point of bfs

		self.containerWeights = {}
		self.tempContainerWeights={}
		self.graph = {}			#adj matrix
		self.weights = {}		#weights of vertecies 
		self.link_weights = {}	#weight of each link
		self.hostMap = {}		#hosts that connect to each switch
		self.originalTopo = None


###########################################################
# 			CONVERT THE MININET TOPO TO OUR TOPO	
###########################################################		

	def loadtopo(self,topo):
		self.originalTopo = topo
		switches = topo.switches()
		links = topo.links()
		hosts = topo.hosts()
		
		for s in switches:
			self.graph[s] = set()
			self.weights[s] = 0 
			self.hostMap[s] = []

		for l in links:
			info  = topo.linkInfo(l[0],l[1])
			self.logger.debug(l[0], " ",l[1])
			if( topo.isSwitch(l[0]) and topo.isSwitch(l[1]) ):
				self.graph[l[0]].add(l[1])
				self.graph[l[1]].add(l[0])
				self.weights[l[0]] += info['bw']
				self.weights[l[1]] += info['bw']
				self.link_weights[l[0]+l[1]] = info['bw']
			else:
				if(topo.isSwitch(l[0])):
					self.weights[l[0]] += info['bw']
					self.hostMap[l[0]].append(l[1])
				if(topo.isSwitch(l[1])):
					self.weights[l[1]] += info['bw']
					self.hostMap[l[1]].append(l[0])
					
		self.start = switches[0]
		self.logger.debug(switches[0])

###########################################################
# 		THIS FUNCTION WILL BE CALLED AFTER THE LOADTOP	
###########################################################	
	
	def partition(self,n,shares):
		self.cuts = n 

		self.logger.debug(self.containers)
		self.logger.debug(shares)
		
		self.containers = shares[:]
			
#		print self.containers
		self.logger.debug(self.containers)
		
		# return Clustering(self.myMain(self.originalTopo), None)
		return self.myMain(self.originalTopo)

###########################################################
# 		THIS FUNCTION IS FOR DYNAMIC POPULATION SIZE
###########################################################	

	def calcTopoWeight(self,topo):
		links = topo.links(sort = True)
		switches = topo.switches()
		weights = {x:0.0 for x in switches}

		for l in links:
			if topo.isSwitch(l[0]):
				weights[l[0]] = weights[l[0]] + float(topo.linkInfo(l[0], l[1])["bw"])
			if topo.isSwitch(l[1]):
				weights[l[1]] = weights[l[1]] + float(topo.linkInfo(l[0], l[1])["bw"])

		#print weights
		return sum(weights.values())


###########################################################
# 					MAIN
###########################################################
	def myMain(self,topo):
		

		#print self.calcTopoWeight(topo)
		self.logger.debug( "graph: ",  (self.graph))
		
		self.newContainers = []
		self.oldContainers = []

		self.randomPoints = self.crossoverPoints*len(self.graph)/100 			# set the number of random points for crossover
		self.populationNum = min(self.populationNum, math.ceil((pow(2,len(self.graph))*0.6)))  # set the population size
		#self.populationNum = 20
		topoWeight = self.calcTopoWeight(topo)
		i = 0
		if sum(self.containers) > topoWeight :
			if sum(self.containers) / topoWeight < 1.02 :
				self.populationNum = self.populationNum
			else:
				while (sum(self.newContainers) < topoWeight):
					self.newContainers.append(self.containers[i])
					i += 1
				while (sum(self.newContainers) / topoWeight > 1.1) :
					self.newContainers[i-1] = self.newContainers[i-1] - 10 
				self.cuts = i
				self.oldContainers = self.containers
				self.containers = self.newContainers
				#self.populationNum = int((sum(self.containers)/self.calcTopoWeight(topo))) * self.populationNum * 18
				self.underflow = True
		else:
			self.populationNum = 20
		
		if len(self.containers) < 2 and (sum(self.containers) > topoWeight):
			self.populationNum = 1
		print "NEW CONTAINERS: ", self.containers
		print "POPULATION SIZE: ", self.populationNum
	
		mybfs = self.bfs(self.graph,self.start) 
		start = time.time()
		mypopulation = self.createPopulation(mybfs, self.populationNum)
		stop = time.time()
		print "FIRST population TIME: ", stop - start 
		
		stopArray =  list()
		currentCost = list()
		
		generation_counter = 0
		while (len(stopArray) < self.stopCount ):

			if generation_counter > self.generationStep:
				break
			generation_counter += 1	
			start = time.time()
			weight_Fitness = self.costFunction(mypopulation)
			stop = time.time()
			#print "WEIGHT FITNESS TIME: ", stop - start 
			start = time.time()
			newgen = self.crossOver(weight_Fitness, mypopulation)
			[mypopulation,self.containerWeights] = self.replacementScheme(mypopulation, newgen, weight_Fitness)
			stop = time.time()
			#print "CREATE NEW GEN TIME: ", stop - start 
			currentCost = self.costFunction( mypopulation )
			if not stopArray or stopArray[0] == currentCost[0][1] :
				stopArray.append(currentCost[0][1])
			else:
				del stopArray[:]
				stopArray.append(currentCost[0][1])
			self.logger.debug( stopArray )

		initialBestChrome = self.bestSolution(currentCost, stopArray[0])[0]
		bestChrome = initialBestChrome
		for i in range(len(stopArray)):
			bestChrome = self.bestSolution(currentCost, stopArray[i])[0] 
			#print bestChrome, "\n\n\n"
			#print bestChrome[0][2], "\n\n\n"
			#temp = self.check_Validity(bestChrome[0][2])
			#print self.check_Validity(bestChrome[0][2])
			if ( self.check_Validity(bestChrome[0][2])[0] == 0):
				break
			else:
				bestChrom = initialBestChrome
		print "Generation Steps: ", generation_counter
		print "childs: ", self.childCounter
		print "Average Child per generation: ", int(self.childCounter/generation_counter)
		subTopos = self.rebuildTopos(bestChrome, topo)
		return subTopos
	
###########################################################
# 		THIS FUNCTION WILL BE CALLED AT THE END AND 
#		WILL BUILD THE SUBTOPOS FROM THE BEST SOLUTION	
###########################################################	

	def rebuildTopos(self, bestSolutions, topo):
		bs = bestSolutions[0][2]
		subTopos = {}
		subToposSwitch={}
	   
		for index in range (self.cuts):
			subTopos[index]  = myTopo()
			#subToposSwitch[index] = []
	   
		for i in range (len(bs)):
			
			subTopos[bs[i].gen].addSwitch(bs[i].label)
			
			hosts = self.hostMap[bs[i].label]

			for x in range(len(hosts)):
				subTopos[bs[i].gen].addHost(hosts[x])
				linkInfo_temp = topo.linkInfo(hosts[x], bs[i].label)
				subTopos[bs[i].gen].addLink(hosts[x], bs[i].label, **linkInfo_temp)
			x = 0
			self.logger.debug( "link weights: ", self.link_weights)
			for j in range(i+1, len(bs)):
				self.logger.debug( bs[i].gen, "," , bs[j].gen)
				self.logger.debug( bs[i].label, "," , bs[j].label )
				if (bs[i].gen == bs[j].gen) and ( (bs[i].label + bs[j].label in self.link_weights) or (bs[j].label + bs[i].label in self.link_weights) ):
					subTopos[bs[j].gen].addSwitch(bs[j].label)
					linkInfo_temp = topo.linkInfo(bs[j].label, bs[i].label)
					subTopos[bs[i].gen].addLink(bs[j].label, bs[i].label, **linkInfo_temp)

		return subTopos
		



###########################################################
# 				BFS FUNCTION		
###########################################################

	def bfs(self,graph, start):

		Gene = namedtuple("Gene", "label weight gen")
		visited, queue = set(), [start]
		mybfs = list()
		
		while queue:
			vertex = queue.pop(0)
			if vertex not in visited:
				visited.add(vertex)
				obj = Gene(vertex, self.weights[vertex], 0)
				mybfs.append(obj)
				queue.extend(self.graph[vertex] - visited)
		return mybfs



###########################################################
# 		THIS FUNCTION CREATES THE FIRST GENERATION 
#					BASED ON THE BFS	
###########################################################

	def createPopulation(self,firstChrom, population):

		firstGeneration = list();
		index = 0
		self.logger.info("Creating the first generation!")
		while(population > index):
			partitions = [0]*self.cuts
			container_overflow_flag = 0
			binaryString=[random.randint(0,self.cuts-1) for i in range(len(firstChrom))]
			
			newMember=list()


			for i in range(len(firstChrom)):
				for j in range(len (partitions)):
					if(binaryString[i] == j):
						partitions[j] += firstChrom[i].weight
			
			for i in range(len (partitions)):
				if (self.underflow):
					self.firstGenGrace = 1.0
					
				if( partitions[i] > self.firstGenGrace * self.containers[i]):
					container_overflow_flag = 1
					break
			if container_overflow_flag == 1:
				self.logger.debug("failed to generate a valid chromosome")
				continue
			

			for i in range(len(firstChrom)):
				obj = firstChrom[i]
				obj = obj._replace(gen = binaryString[i]) 
				newMember.append( obj )

			if( newMember in firstGeneration):
				continue
			
			self.containerWeights[index] = partitions
			
			firstGeneration.append(newMember)
			index += 1
		self.logger.info("First generation Created!")
		return firstGeneration

###########################################################
# 		THIS FUNCTION CHECKS THE VALIDITY OF A CHILD	
###########################################################

	def check_Validity(self,Chrom):
		newMember=list()

		partitions = [0]*self.cuts
		container_overflow_flag = 0

		for i in range(len(Chrom)):
			for j in range(len (partitions)):
				if(Chrom[i].gen == j):
					partitions[j] += Chrom[i].weight
		
		for i in range(len (partitions)):
				if( partitions[i] > self.containers[i]):		
					return [1]
		'''
		#print partitions[0] , self.containers[0], "----" , partitions[1] , self.containers[1], "----" , partitions[2] , self.containers[2]
		if( partitions[0] > 1.0 * self.containers[0] or partitions[1] > 1.038 * self.containers[1] or partitions[2] > 1.01 * self.containers[2]):		
			return [1]
		'''

		return [0,partitions]
		# 0 means that is valid, along with 0 we also send back amount of containers used.

###########################################################
# 		THIS FUNCTION GETS A WHOLE GENERATION AND 
#		CALCULATES THE COST OF EACH AND RETURNS THE SORTED
#		VERSION OF THE COST.
###########################################################

	def costFunction(self,population):

		weight_Fitness =  list()

		for i in range( len(population)):
			tempFitness = 0
			tempChromo = population[i]

			for j in range( len(tempChromo)):
				for k in range(j , len (tempChromo)):
					#print tempChromo
					if ( tempChromo[j].gen != tempChromo[k].gen ):
						templabel1 = tempChromo[j].label + tempChromo[k].label
						templabel2 = tempChromo[k].label + tempChromo[j].label
						if( (templabel1 in self.link_weights) or (templabel2 in self.link_weights) ):
							#print templabel1
							if( templabel1 in self.link_weights):
								tempFitness += self.link_weights[templabel1]
							else:
								tempFitness += self.link_weights[templabel2] 
						else:
							continue
			tup = list()
			tup.append(i)
			tup.append(tempFitness)
			tup.append(tempChromo)
			weight_Fitness.append(tup)
		weight_Fitness = sorted(weight_Fitness,key=itemgetter(1))
		#print weight_Fitness
		return weight_Fitness	


###########################################################
# 		THIS FUNCTION GETS A WHOLE GENERATION AND CHOOSES
#		TWO PARENTS AND CREATES TWO CHILDEREN AND THEN 
#		SENDS THEM TO CHECK VALIDITY BEFORE RETURNING
###########################################################
	def createChild(self,weight_Fitness, population):

		tempWeights = list()
		used = list()
		indexes = list()
		flag = 0

		#choose two parent randomly favoring better cuts
		sum_weights = sum(j for i,j,k in weight_Fitness)

		# this is inverting the weights so we can figure out which one has the least cost.
		for i in range ( len(weight_Fitness)):
			tempWeights.append(sum_weights - list(weight_Fitness[i])[1])

		totals = list()  # this is creating an accumulative on the tempWeights
		running_total = 0

		for i in range ( len(weight_Fitness)):
			running_total += tempWeights[i]
			totals.append(running_total)
		
		while (len(used) < 2):
			
			rnd = random.randint(0,self.populationNum-1)
			#print rnd
			if(rnd not in used):
				used.append(list(weight_Fitness[rnd])[0])
				#print used
				#break
			'''
			rnd = random.randint(0,running_total)
			for i, total in enumerate(totals):
				if rnd < total:
					if(i not in used):
						used.append(list(weight_Fitness[i])[0])
						#print used
						break
				'''
		# have to check the above routine for choosing the two fittest parents

		parent1 = population[used[0]]
		parent2 = population[used[1]]

		
		#print "here ", parent1
		indexes = random.sample(range(0, len(parent1)-1), self.randomPoints-1)
		indexes.append(len(parent1))
		indexes  = sorted(indexes, key=int)  
		#print "\n\n\n\n"
		#print "INDEXES: ", indexes
		child1 = list()
		child2 = list()
		tempPrev = 0
		

		for i in range(0,len(indexes)):
			if (i % 2 ) == 0:
				child1[tempPrev:indexes[i]] = parent1[tempPrev:indexes[i]]
				child2[tempPrev:indexes[i]] = parent2[tempPrev:indexes[i]]
			else:
				child2[tempPrev:indexes[i]] = parent1[tempPrev:indexes[i]]
				child1[tempPrev:indexes[i]] = parent2[tempPrev:indexes[i]]

			tempPrev = indexes[i]
		#print len(child1)

		#print len(child2)


		for i in range(1,self.numMutations):
			rnd_ = random.random()
			if(rnd_ <= self.mutationRate):
				child1 = self.mutationScheme (child1)

		for i in range(1,self.numMutations):
			rnd_ = random.random()
			if(rnd_ <= self.mutationRate):
				child2 = self.mutationScheme (child2)


	#	print rnd
	#	print child1
	#	print check_Validity(child1)
		return [child1, self.check_Validity(child1), child2, self.check_Validity(child2)]


###########################################################
# 		
###########################################################
	def crossOver(self,weight_Fitness, population):
		
		children_count = 0 	#len(population);
		children = list();

		while (children_count < len(population)):
			self.childCounter += 2
			[newChild1, val1, newChild2, val2] = self.createChild(weight_Fitness, population)

			if(val1[0] == 0 and newChild1 not in children):
				self.tempContainerWeights[children_count] = val1[1]
				children.append(newChild1)
				children_count += 1
			if(val2[0] == 0 and newChild2 not in children):
				self.tempContainerWeights[children_count] = val2[1]
				children.append(newChild2)
				children_count += 1

		
		return children
		#print children

###########################################################
# 		
###########################################################
	def replacementScheme(self,population, newgen, weight_Fitness):

		tempWeights = {}
		updated_generation = list();
		new_fitness = self.costFunction(newgen)

		n = math.ceil(len(population) * self.percentOfOldGen)
		j = 0

		while (j < n):
			old_index = list(weight_Fitness.pop(0))[0]
			updated_generation.append(population[old_index])
			tempWeights[j] = self.containerWeights[old_index]
			j += 1

		while (j < len(population)):
			index = list(new_fitness.pop(0))[0]
			updated_generation.append(newgen[index])
			#print index
			tempWeights[j] = self.tempContainerWeights[index]

			j += 1
		#containerWeights = tempWeights.copy()
		return [updated_generation, tempWeights]

###########################################################
# 		
###########################################################
	def mutationScheme(self, chromosome ):
		rnd = random.randint(0,len(chromosome)-1)
		numbers = range(0,chromosome[rnd].gen) + range(chromosome[rnd].gen+1,self.cuts-1)
		if not numbers:
			return chromosome
		r = random.choice(numbers)
		chromosome[rnd]._replace(gen = r)

		return chromosome


###########################################################
# 		
###########################################################
	def bestSolution(self,costArray, bestCost):

		bestSolutions =  list()
		tempSolutions =  list()
		minCountainers = self.cuts+10


		for i in range (len(costArray)):
			if costArray[i][1] == bestCost :
				count = self.cuts - self.containerWeights[i].count(0)
			
				if(count <= minCountainers):
					minCountainers = count
					tempSolutions.append([costArray[i], count])

		for i in range (len(tempSolutions)):
			if(tempSolutions[i][1] == minCountainers):
				bestSolutions.append(tempSolutions[i])

		#print bestSolutions[0][1]
		#print costArray[bestSolutions[0][0][0]]

		for i in range (len(self.containerWeights)):
			self.containerWeights[i] = sorted(self.containerWeights[i], key=int) 
		
		

		i = self.cuts - 1

		self.logger.debug("number of best solutions after filtering based on empty containers", len(bestSolutions))
		self.logger.debug("minimum number of containers used: " , minCountainers)

		
		while(i >= 0):
			#print "while"
			del tempSolutions[:]
			curMax = -1
			#print "bestSolutions length: ", len(bestSolutions)
			j = 0
			for j in range (len(bestSolutions)):
				#print containerWeights[bestSolutions[j][0][0]][i]
				if curMax < self.containerWeights[bestSolutions[j][0][0]][i]:
					curMax = self.containerWeights[bestSolutions[j][0][0]][i]
					#print "max: ", curMax

			j = 0
			for j in range( len(bestSolutions)):

				if self.containerWeights[bestSolutions[j][0][0]][i] == curMax:
					tempSolutions.append(bestSolutions[j])
					#print "top" 

			del bestSolutions[:]
			#print "temp length: ", len(tempSolutions)
			bestSolutions = tempSolutions[:]

			if len(bestSolutions) == 1:
				break

			i -= 1

		
		#self.logger.info("number of best solutions: ", len(bestSolutions))
		#self.logger.info("containers that the best solutions filled up: " , self.containerWeights[bestSolutions[0][0][0]])
#		print "\n\nnumber of best solutions: ", len(bestSolutions)
		#for x in range(len(self.containerWeights)):
			#print self.containerWeights[x]
#		print "containers that the best solutions filled up: " , self.containerWeights[bestSolutions[0][0][0]] , "\n\n"
		return bestSolutions

		


	   
if __name__ == '__main__':
	logger2 = logging.getLogger(__name__)
	for x in xrange(1,2):
		topo  = myTopo()
		client0 = topo.addHost('h0')
		client1 = topo.addHost('h1')
		client2 = topo.addHost('h2')
		client3 = topo.addHost('h3')
		switch0 = topo.addSwitch('s0')
		switch1 = topo.addSwitch('s1')
		switch2 = topo.addSwitch('s2')
		switch3 = topo.addSwitch('s3')
		switch4 = topo.addSwitch('s4')
		switch5 = topo.addSwitch('s5')
		switch6 = topo.addSwitch('s6')
		switch7 = topo.addSwitch('s7')
		switch8 = topo.addSwitch('s8')
		switch9 = topo.addSwitch('s9')
		switch10 = topo.addSwitch('s10')
		switch11 = topo.addSwitch('s11')
		switch12 = topo.addSwitch('s12')
		switch13 = topo.addSwitch('s13')
		switch14 = topo.addSwitch('s14')



		topo.addLink(client0, switch0, bw=100)
		topo.addLink(client1, switch1, bw=100)
		topo.addLink(client2, switch2, bw=100)
		topo.addLink(client3, switch3, bw=100)
		topo.addLink(switch0, switch4, bw=100)
		topo.addLink(switch1, switch4, bw=100)
		topo.addLink(switch2, switch5, bw=100)
		topo.addLink(switch3, switch5, bw=100)
		topo.addLink(switch4, switch6, bw=200)
		topo.addLink(switch5, switch6, bw=200)

		topo.addLink(switch7, switch14, bw=100)
		topo.addLink(switch9, switch14, bw=100)
		topo.addLink(switch9, switch10, bw=100)
		topo.addLink(switch10, switch11, bw=100)
		topo.addLink(switch10, switch13, bw=200)
		topo.addLink(switch14, switch13, bw=200)
		topo.addLink(switch8, switch10, bw=100)
		topo.addLink(switch9, switch12, bw=100)
		topo.addLink(switch8, switch6, bw=100)
		topo.addLink(switch10, switch6, bw=100)
		topo.addLink(switch5, switch11, bw=200)
		topo.addLink(switch4, switch13, bw=200)
		topo.addLink(switch6, switch14, bw=200)
		topo.addLink(switch12, switch6, bw=200)

		logger2.debug("sw: " + str(topo.switches()))
		logger2.debug("hosts:", topo.hosts())
		logger2.debug("links:", topo.links())

		p = Partitioner()

		p.loadtopo(topo)
		subTopos = p.partition(4,[1000,1000,4000,2000])

		for i in range(len(subTopos)) : 
			logger2.debug( i, ": ")
			logger2.debug( "sw:", subTopos[i].switches())
			logger2.debug( "hosts:", subTopos[i].hosts())
			logger2.debug( "links:", subTopos[i].links() )
			for l in subTopos[i].links():
				logger2.debug( topo.linkInfo(l[0], l[1]))
			logger2.debug( "\n\n")
#print costFunction(mypopulation)
#print containerWeights


# while (stop > 0):
# 	weight_Fitness = costFunction(mypopulation)
# 	newgen = crossOver(weight_Fitness, mypopulation)
# 	#print costFunction(mypopulation)
# 	#print "\n"
# 	#print newgen
# 	newgen = replacementScheme(mypopulation , newgen)
# 	#print costFunction(newgen)
# 	mypopulation = newgen
# 	stop -= 1






# to see just the chromosomes

# for val in mypopulation:
#     for y in list(val):
#     	sys.stdout.write(str(y.gen))
#     print "\n"
# print "\n\n"
# print weight_Fitness
#createChild(weight_Fitness, mypopulation)



