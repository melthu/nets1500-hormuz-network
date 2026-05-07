Project: Can Oil Trade Networks Predict Energy Price Shocks? A Hormuz Closure Case Study


PROJECT DESCRIPTION

This project models global oil trade as a weighted directed graph and simulates
a closure of the Strait of Hormuz by removing a transit node from the network.
For each importing country, an exposure score is computed using two graph
algorithms: max flow (to measure supply loss) and shortest path (to measure
rerouting difficulty). These scores are validated against real OECD energy CPI
data from January to March 2026, following the closure of the Strait after
war broke out between Iran and the U.S./Israel on February 28, 2026.


CATEGORIES USED

- Graph and graph algorithms: The core of the project is a directed weighted
  graph of bilateral oil trade flows. Max flow is used to measure supply
  disruption and Dijkstra's shortest path is used to measure
  rerouting cost before and after the Hormuz closure.

- Physical Networks: The Strait of Hormuz is modeled as a physical chokepoint
  node in the network. Its removal simulates the real-world severing of a
  critical transit route, analogous to a link failure in a physical network.


WORK BREAKDOWN

This was a solo project. All data collection, graph construction, analysis,
and writing was completed by Melvin Thu.


AI USAGE

AI was used for debugging code and for assistance with plotting and data
visualization.
