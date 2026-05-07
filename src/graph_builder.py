import networkx as nx

HORMUZ = "HORMUZ"
WORLD_SUPPLY = "WORLD_SUPPLY"


def build_graph(flows, shares):
    merged = flows.merge(shares, on=["exporter_iso3", "importer_iso3"], how="left")
    merged["hormuz_share"] = merged["hormuz_share"].fillna(0.0)
    merged["qty_kt"] = merged["quantity_tons"] / 1000.0

    G = nx.DiGraph()

    # Accumulate capacities separately before adding edges
    hormuz_in  = {}  # exporter -> HORMUZ capacity
    hormuz_out = {}  # HORMUZ -> importer capacity
    direct     = {}  # exporter -> importer direct capacity (pipeline bypass)

    for _, r in merged.iterrows():
        exp, imp = r["exporter_iso3"], r["importer_iso3"]
        qty, hs = r["qty_kt"], r["hormuz_share"]
        if qty <= 0:
            continue
        through_hormuz = hs * qty
        bypass = (1 - hs) * qty
        if through_hormuz > 0:
            hormuz_in[exp]  = hormuz_in.get(exp, 0) + through_hormuz
            hormuz_out[imp] = hormuz_out.get(imp, 0) + through_hormuz
        if bypass > 0:
            direct[(exp, imp)] = direct.get((exp, imp), 0) + bypass

    for exp, cap in hormuz_in.items():
        G.add_edge(exp, HORMUZ, capacity=cap, cost=1/(cap+1))
    for imp, cap in hormuz_out.items():
        G.add_edge(HORMUZ, imp, capacity=cap, cost=1/(cap+1))
    for (exp, imp), cap in direct.items():
        if G.has_edge(exp, imp):
            G[exp][imp]["capacity"] += cap
            G[exp][imp]["cost"] = 1 / (G[exp][imp]["capacity"] + 1)
        else:
            G.add_edge(exp, imp, capacity=cap, cost=1/(cap+1))

    # Add a dummy world supply node connected to every exporter
    for exp, total in merged.groupby("exporter_iso3")["qty_kt"].sum().items():
        if total > 0 and exp in G:
            G.add_edge(WORLD_SUPPLY, exp, capacity=float(total), cost=0)

    hormuz_throughput_mbd = sum(d["capacity"] for _, _, d in G.in_edges(HORMUZ, data=True)) * (1000/0.136) / 365 / 1e6
    print(f"Graph built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    print(f"Hormuz throughput: {hormuz_throughput_mbd:.1f} mb/d (EIA estimate ~21 mb/d)")
    return G


def close_hormuz(G):
    G_closed = G.copy()
    G_closed.remove_node(HORMUZ)
    return G_closed
