import os
import networkx as nx
import numpy as np
import pandas as pd

from src.graph_builder import HORMUZ, WORLD_SUPPLY

MIN_IMPORT_KT = 100.0   # ignore countries below this import volume
MAX_REROUTE   = 5.0     # cap rerouting cost at 500%


def compute_exposure(G_full, G_closed, flows):
    top_exporters = get_top_exporters(flows)
    rows = []

    importers = [n for n in G_full.nodes()
                 if n not in (WORLD_SUPPLY, HORMUZ) and G_full.in_degree(n) > 0]

    for imp in importers:
        flow_before = max_flow(G_full, WORLD_SUPPLY, imp)
        if flow_before < MIN_IMPORT_KT:
            continue

        flow_after = max_flow(G_closed, WORLD_SUPPLY, imp) if imp in G_closed else 0.0
        volume_loss = max(0.0, (flow_before - flow_after) / flow_before)
        reroute_cost = rerouting_cost(G_full, G_closed, imp, top_exporters.get(imp, []))
        exposure = volume_loss * (1 + reroute_cost)

        rows.append({
            "country_iso3":       imp,
            "volume_loss_pct":    round(volume_loss, 4),
            "rerouting_cost_pct": round(reroute_cost, 4),
            "exposure_score":     round(exposure, 4),
            "import_volume_kt":   round(flow_before, 1),
        })

    df = pd.DataFrame(rows).sort_values("exposure_score", ascending=False).reset_index(drop=True)
    out = os.path.join(os.path.dirname(__file__), "..", "output", "exposure_scores.csv")
    df.to_csv(out, index=False)
    print(f"Exposure scores computed for {len(df)} countries")
    return df


def max_flow(G, source, sink):
    if source not in G or sink not in G:
        return 0.0
    if not nx.has_path(G, source, sink):
        return 0.0
    try:
        return float(nx.maximum_flow_value(G, source, sink, capacity="capacity",
                                           flow_func=nx.algorithms.flow.dinitz))
    except Exception:
        return 0.0


def rerouting_cost(G_full, G_closed, imp, exporters):
    before, after = [], []
    for exp in exporters:
        if exp == imp or exp not in G_full:
            continue
        d_before = path_cost(G_full, exp, imp)
        if d_before is None:
            continue
        before.append(d_before)
        d_after = path_cost(G_closed, exp, imp) if exp in G_closed and imp in G_closed else None
        after.append(d_after if d_after is not None else MAX_REROUTE)

    if not before:
        return 0.0
    avg_before = np.mean(before)
    avg_after  = np.mean(after)
    if avg_before < 1e-12:
        return 0.0
    return float(np.clip((avg_after - avg_before) / avg_before, 0, MAX_REROUTE))


def path_cost(G, source, target):
    try:
        return float(nx.shortest_path_length(G, source, target, weight="cost"))
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None


def get_top_exporters(flows, n=3):
    result = {}
    grouped = flows.groupby(["importer_iso3", "exporter_iso3"])["quantity_tons"].sum().reset_index()
    for imp, grp in grouped.groupby("importer_iso3"):
        result[imp] = grp.nlargest(n, "quantity_tons")["exporter_iso3"].tolist()
    return result
