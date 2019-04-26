import random
import networkx as nx 
import numpy as np
from scipy.integrate import quad

class Node:
	""" 
	A Node represents a person in a graph, should have the following:
	-a randomized lambda value for each person for which we plug into the pdf of an exponential function (between 1/15 to 1)
	-a level of wealth (0 to 1)
	-threshold (from wealth and closeness) = 1/(closeness) * wealth, between 0 and 1, 
	compared to the calculated integral of exponential function
	-an int value in (0, 1, 2) for whether someone is uninvolved, involved, or out
	"""

	def __init__(self):

		# randomize the lambda, wealth, and closeness

		self.goat = random.uniform(0.0666, 0.5)
		self.wealth = random.uniform(0.001, 1)
		self.status = 0 # uninvolved
		self.patience = self.wealth * 1/(random.uniform(0.00001, 0.001))
		# wealth * some scalar = patience, how many time steps they wait iuntil sending another invite
		self.sent_invites = []

	#lower bounded by 0
	def get_probability(self, lower, upper):
		return quad(self.exp_pdf, lower, upper)[0]

	def exp_pdf(self, x):
		return self.goat * np.exp(-1 * self.goat * x)

# node = Node()
# i = 0
# while node.get_probability(0, i) < 0.93:
# 	i += 1

# print(i)

class Scheme:
	def __init__(self, threshold, money_to_join, num_recruits):
		self.threshold = threshold
		self.money_to_join = money_to_join
		self.num_recruits = num_recruits

# OUTPUT: (graph, fat_map): fat_map maps nodes to created nodes cuz can't generate graph with custom nodes
# can also generate based on probability?
# total number of people, edges

	def generate_graph(num_people, num_edges):
		graph = nx.gnm_random_graph(num_people, num_edges)
		for (u, v, w) in graph.edges(data = True):
	    	w['weight'] = random.uniform(0.001, 1)

	    fat_map = {}
	    for i in graph.nodes:
	    	fat_map[i] = Node()

	    self.graph = graph
	    self.fat_map = fat_map
	    self.time = 0
	    self.curr_involved = []
	    self.uninvolved = graph.nodes
	    self.no_friends = nx.isolates(graph)

	# graph, fat_map, curr time step, people in the scheme rn, people who haven't been involved yet
	def increment_time():
		if not len(self.uninvolved):
			print("but we done boi")
			return
		while not self.curr_involved:
			rando = random.randint(0, len(self.uninvolved))
			start = self.uninvolved.pop(rando)
			if start in self.no_friends:
				self.fat_map[start].status = 2
			else:
				if len(self.graph[start]) < self.num_recruits:
					self.fat_map[start].status = 2
				else:
					self.curr_involved.append(start)
					self.fat_map[start].status = 1

		for person in self.curr_involved:


