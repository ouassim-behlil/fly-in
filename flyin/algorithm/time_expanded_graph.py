from __future__ import annotations
from typing import Dict, Set, List
from dataclasses import dataclass

from flyin.model import Graph, ZoneType

@dataclass
class TimeExpandedNode:
	""" A node in the time expanded graph """
	zone_name: str
	turn: int
	is_in: bool

	def __hash__(self) -> int:
		return hash((self.zone_name, self.turn, self.is_in))
	
	def __eq__(self, other: object) -> bool:

		if not isinstance(other, TimeExpandedNode):
			return False
		
		return (
			self.zone_name == other.zone_name
			and self.turn == other.turn
			and self.is_in == other.is_in
		)
	
	def __repr__(self) -> str:

		node_type = "IN" if self.is_in else "OUT"

		return f"{self.zone_name}_{node_type}[{self.turn}]"


@dataclass
class Edge:
	""" An edge with capacity """

	src: TimeExpandedNode
	dst: TimeExpandedNode
	capacity: int
	flow: int = 0

	def residual_capacity(self) -> int:
		""" remaining capacity for this edge """

		return self.capacity - self.flow
	
	def __repr__(self) -> str:

		return f"{self.src} ->({self.capacity}) {self.dst}"


class TimeExpandedGraph:
	""" Time-expanded graph for T turns """

	def __init__(self, original_graph: Graph, max_turns: int):
		self.original_graph = original_graph
		self.max_turns = max_turns

		self.edges_from: Dict[TimeExpandedNode, List[Edge]] = {}
		self.edges_to: Dict[TimeExpandedNode, List[Edge]] = {}

		self.source: TimeExpandedNode = TimeExpandedNode("__SOURCE__", -1, True)
		self.sink: TimeExpandedNode = TimeExpandedNode("__SINK__", max_turns, False)

		self.nodes: Set[TimeExpandedNode] = {self.source, self.sink}
	

	def add_edge(self, src: TimeExpandedNode, dst: TimeExpandedNode, capacity: int) -> None:
		""" Add a directed edge with capacity """

		if src not in self.edges_from:

			self.edges_from[src] = []
		
		if dst not in self.edges_to:

			self.edges_to[dst] = []
		
		edge = Edge(src, dst, capacity)
		self.edges_from[src].append(edge)
		self.edges_to[dst].append(edge)

		self.nodes.add(src)
		self.nodes.add(dst)

	
	def build(self, T: int) -> None:
		""" build time-expanded graph for T turns """

		# step 1: add zone split edges and temporal edges
		for t in range(T):

			for zone in self.original_graph.zones:

				in_node = TimeExpandedNode(zone.name, t, True)
				out_node = TimeExpandedNode(zone.name, t, False)

				self.add_edge(in_node, out_node, zone.metadata.max_drones)

				if t < T - 1:

					next_in_Node = TimeExpandedNode(zone.name, t + 1, True)

					# unlimited capacity for waiting
					self.add_edge(out_node, next_in_Node, float('inf'))
				
		# strp2: Add connection edges
		for conn in self.original_graph.connections:

			src, dst = conn.zone1, conn.zone2

			dst_zone = next(z for z in self.original_graph.zones if z.name == dst)
			move_cost = dst_zone.metadata.cost

			# add edges in both directions:
			for t in range(T - move_cost):

				# forward edge
				src_out = TimeExpandedNode(src, t, False)
				dst_in = TimeExpandedNode(dst, t + move_cost, True)
				self.add_edge(src_out, dst_in, conn.max_link_capacity)
			
				# backward edge:
				dst_out = TimeExpandedNode(dst, t, False)
				src_in = TimeExpandedNode(src, t + move_cost, True)
				self.add_edge(dst_out, src_in, conn.max_link_capacity)
		
		# step 3: Add source -> start_zone and  end_zone -> sink
		for t in range(T):
			start_in = TimeExpandedNode(self.original_graph.start_zone.name, t, True)
			self.add_edge(self.source, start_in, self.original_graph.nb_drones)

			goal_out = TimeExpandedNode(self.original_graph.end_zone.name, t, False)
			self.add_edge(goal_out, self.sink, float('inf'))
		
	
	def get_edges(self, src: TimeExpandedNode) -> List[Edge]:
		""" Get all outgoing edges from a node """

		return self.edges_from.get(src, [])
	

	def reset_flow(self) -> None:
		""" Reset all edge flows to zero """

		for edges in self.edges_from.values():
			
			for edge in edges:

				edge.flow = 0
