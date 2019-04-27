import random
import networkx as nx 
import numpy as np
from scipy.integrate import quad

class Node:
	""" 
	A Node represents a person in a graph, should have the following:
	-a randomized lambda value for each person for which we plug into the pdf of an exponential function (between 0.0666, 0.5)
	-a level of wealth (0 to 1)
	-an int value in (0, 1, 2) representing status for whether someone is uninvolved, involved, or out
	"""

	def __init__(self):

		# randomize the lambda, wealth, and closeness

		self.goat = random.uniform(0.0666, 0.5)
		self.wealth = random.uniform(0.1, 0.4)
		self.status = 0 # uninvolved
		self.patience = self.wealth * 1/(random.uniform(0.015, 0.02)) # min patience is 5, max patience is 26 days
		self.time_since_invite = 0
		# wealth * some scalar = patience, how many time steps they wait iuntil sending another invite
		self.sent_invites = 0  # how many people theyve sent invites to
		self.accepted = 0 # 
		self.start_time = -1
		# 0 = cashed out/got money, 1 = lost money/failed, 2 = declined
		self.gained_money = -1

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
	def __init__(self, threshold, num_recruits):
		self.threshold = threshold
		self.num_recruits = num_recruits

# OUTPUT: (graph, fat_map): fat_map maps nodes to created nodes cuz can't generate graph with custom nodes
# can also generate based on probability?
# total number of people, edges

	def generate_graph(self, num_people, num_edges):
		graph = nx.gnm_random_graph(num_people, num_edges)
		for (u, v, w) in graph.edges(data = True):
			w["weight"] = random.uniform(0.4, 1)

		fat_map = {}
		for i in graph.nodes():
			fat_map[i] = Node()


		self.graph = graph
		self.fat_map = fat_map
		self.time = 0
		self.curr_involved = []
		self.curr_invited = {}
		self.uninvolved = graph.nodes()

	# graph, fat_map, curr time step, people in the scheme rn, people who haven't been involved yet
	def increment_time(self):
		if not len(self.uninvolved) and not self.curr_invited:
			print("but we done boi")
			return True
		#find a person to start (no one currently involved)
		while not self.curr_involved:
			rando = random.randint(0, len(self.uninvolved) - 1)
			start = self.uninvolved.pop(rando)
			if not self.graph.degree()[start]: # if the guy we chose has no friends
				self.fat_map[start].status = 2
				self.fat_map[start].gained_money = 3
			else:
				#JK just don't include them
				if len(self.graph.adj[start]) < self.num_recruits:
					self.uninvolved.append(start)
				else:
					#yes
					self.add_involved(start)


		# when someone is done/cashed out, i remove the node in inviter
		for inviter in list(self.curr_invited.keys()):
			inviter_node = self.fat_map[inviter]
			# if they sent invites to all friends but everyone has already responded
			if inviter_node.sent_invites == len(self.graph[inviter]) and not self.curr_invited[inviter]:
				inviter_node.status = 2
				inviter_node.gained_money = 1
				self.remove_involved(inviter)
				continue

			for invited in self.curr_invited[inviter][:]:
				invited_node = self.fat_map[invited]
				offset = self.time - invited_node.start_time
				response = invited_node.get_probability(0, offset)
				# print("probability of " + str(invited) + " responding: " + str(response) + ", offset: " + str(offset))
				#random threshold for responding
				if response > 0.5:
					answer = (1/self.graph[inviter][invited]["weight"]) * invited_node.wealth # max answer = 1, min answer = 0.1
					self.curr_invited[inviter].remove(invited)
					print(str(answer) + " is the calculated prob of yes, vs. " + str(self.threshold))
					#accept
					if answer >= self.threshold and not invited_node.status:
						self.add_involved(invited)
						inviter_node.accepted += 1
						if inviter_node.accepted == self.num_recruits:
							inviter_node.status = 2
							inviter_node.gained_money = 0
							self.remove_involved(inviter)
							break
					#decline
					else:
						print(str(invited) + " says no! They are currently in gained_money state " 
							+ str(invited_node.gained_money) + ", and their status is " + str(invited_node.status))
						if not invited_node.status:
							print("We yeeting out of here!")
							invited_node.status = 2
							invited_node.gained_money = 2
							if invited not in self.curr_involved:
								self.uninvolved.remove(invited)

			# print("Patience: " + str(inviter_node.patience) + " vs. Time Since Invite: " + str(inviter_node.time_since_invite))
			inviter_node.time_since_invite += 1
			if inviter_node.time_since_invite > inviter_node.patience or inviter in list(self.curr_invited.keys()) and not self.curr_invited[inviter]: # to make sure they are not waiting on an empty list of people.
				self.send_invite(inviter)

		self.time += 1
		return False

	def add_involved(self, person):
		node = self.fat_map[person]
		self.curr_involved.append(person)
		self.curr_invited[person] = []

		if person in self.uninvolved:
			self.uninvolved.remove(person)

		if len(self.graph[person]) < self.num_recruits: # not enough friends
			node.status = 2
			node.gained_money = 1
			self.remove_involved(person)
			return

		self.send_invite(person)
		node.status = 1
		node.start_time = self.time

	#modify status and gained_money outside of function
	def remove_involved(self, person):
		self.curr_involved.remove(person)
		del self.curr_invited[person]

	def send_invite(self, person):
		node = self.fat_map[person]
		#no more ppl to invite
		if node.sent_invites == len(self.graph[person]):
			return
		else:
			#sort neighbors by edge weight largest to smallest
			neighbors = sorted(self.graph.adj[person], key = lambda x: self.graph[person][x]["weight"])

			#first invite
			if not node.sent_invites:
				node.sent_invites = self.num_recruits
				node.time_since_invite = 0
				for new_invite in neighbors[:node.sent_invites]:
					self.curr_invited[person].append(new_invite)
					# self.fat_map[new_invite].start_time = self.time # set the start time to be the current time, so offset is correct

			else: # did we check if we have enough friends??
				self.curr_invited[person].append(neighbors[node.sent_invites])
				node.sent_invites += 1
				node.time_since_invite = 0


scheme = Scheme(0.3, 2)
scheme.generate_graph(10, 45)
print(scheme.graph)
# print("Time: " + str(scheme.time) + ", Involved: " + str(scheme.curr_involved) + ", Invited: " + str(scheme.curr_invited) + ", Uninvolved: " + str(scheme.uninvolved) + ", Threshold: " + str(scheme.threshold) + ", Number of recruits: " + str(scheme.num_recruits))
while not scheme.increment_time():
	print("Time: " + str(scheme.time) + ", Involved: " + str(scheme.curr_involved) 
		+ ", Invited: " + str(scheme.curr_invited) + ", Uninvolved: " + str(scheme.uninvolved) + 
		", Threshold: " + str(scheme.threshold) + ", Number of recruits: " + str(scheme.num_recruits) + "\n")
for node in scheme.fat_map:
	print(scheme.fat_map[node].gained_money)
