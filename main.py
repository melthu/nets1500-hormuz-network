from src.data_loader import load_baci, filter_oil, make_hormuz_shares, load_price_data
from src.graph_builder import build_graph, close_hormuz
from src.exposure import compute_exposure
from src.validation import run_validation
from src.visualize import plot_regression

raw = load_baci(year=2024)
flows = filter_oil(raw)
hormuz_shares = make_hormuz_shares(flows)

G = build_graph(flows, hormuz_shares)
G_closed = close_hormuz(G)
scores = compute_exposure(G, G_closed, flows)

prices = load_price_data()
merged = run_validation(scores, prices)
plot_regression(merged)
