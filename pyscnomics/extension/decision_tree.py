"""
Decision Tree Analysis for Production Sharing Contracts (PSC) and other E&P investment decisions
==============================================
Custom object-oriented implementation using dataclasses, with backward
induction (rollback) for expected-value computation and Plotly for
interactive visualization.

Design
------
- NodeType: DECISION | CHANCE | TERMINAL
- Branch: an edge out of a node. Carries an optional probability
  (required for CHANCE nodes), an optional cash flow / cost incurred by
  taking that branch (e.g. drilling cost, appraisal cost), and a
  reference to the child Node.
- Node: recursive structure. `.evaluate()` performs backward induction:
    * TERMINAL  -> returns its stored value (e.g. NPV from pyscnomics)
    * CHANCE    -> returns probability-weighted expected value of children
    * DECISION  -> returns the max (or min) over children, and records
                   which branch was optimal
- DecisionTree: thin wrapper holding the root node + plotting logic.

Terminal values are meant to be NPVs (e.g. output of a pyscnomics
CostRecovery.run() -> get_summary() call for a given scenario), so this
tree is designed to sit *above* your fiscal engine, not duplicate it.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Tuple
import math

import plotly.graph_objects as go

from pyscnomics.contracts.costrecovery import CostRecovery
from pyscnomics.contracts.gross_split import GrossSplit

# ---------------------------------------------------------------------------
# Core data model
# ---------------------------------------------------------------------------

class NodeType(Enum):
    DECISION = "decision"   # square: choose the branch that optimizes the objective
    CHANCE = "chance"       # circle: probability-weighted branches
    TERMINAL = "terminal"   # triangle: leaf, holds a final value (e.g. NPV)


@dataclass
class Branch:
    """An edge leaving a node."""
    label: str
    child: "Node"
    probability: Optional[float] = None   # required if parent is CHANCE

    def __post_init__(self):
        if self.probability is not None and not (0.0 <= self.probability <= 1.0):
            raise ValueError(f"Branch '{self.label}': probability must be in [0,1]")


@dataclass
class Node:
    """A node in the decision tree."""
    name: str
    node_type: NodeType
    branches: List[Branch] = field(default_factory=list)
    contract: CostRecovery | GrossSplit | None = None  # optional: contract object for this node
    contract_args: dict = field(default_factory=dict)  # optional: args to pass to contract for this node
    summary_args: dict = field(default_factory=dict)    # optional: args to pass to contract.get_summary() for this node
    value: Optional[float] = None          # TERMINAL: input value. Others: computed EV after evaluate()
    optimal_branch: Optional[str] = None   # filled in for DECISION nodes after evaluate()
    maximize: bool = True                  # DECISION nodes: True -> pick max EV, False -> pick min (e.g. min cost/risk)

    # -- construction helpers -------------------------------------------------
    def add_branch(self, branch: Branch) -> "Node":
        self.branches.append(branch)
        return self  # chainable

    # -- core algorithm: backward induction / rollback -----------------------
    def evaluate(self) -> float:
        """Recursively compute the expected value of this node (rollback)."""
        if self.node_type == NodeType.TERMINAL:
            if self.contract is not None:
                if self.contract_args:
                    self.contract.run(**self.contract_args)
                else:
                    self.contract.run()
                summary = self.contract.get_summary(**self.summary_args)
                if "ctr_npv" not in summary:
                    raise KeyError(f"Contract summary for node '{self.name}' does not contain 'ctr_npv'")
                self.value = summary["ctr_npv"]
            elif self.value is None:
                raise ValueError(f"Terminal node '{self.name}' has neither a contract nor a value set")
            return self.value

        if not self.branches:
            raise ValueError(f"Non-terminal node '{self.name}' has no branches")

        branch_totals: Dict[str, float] = {}
        for b in self.branches:
            branch_totals[b.label] = b.child.evaluate()

        if self.node_type == NodeType.CHANCE:
            probs = [b.probability for b in self.branches]
            if any(p is None for p in probs):
                raise ValueError(f"Chance node '{self.name}': every branch needs a probability")
            if not math.isclose(sum(probs), 1.0, abs_tol=1e-6):
                raise ValueError(f"Chance node '{self.name}': probabilities sum to {sum(probs)}, not 1.0")
            ev = sum(branch_totals[b.label] * b.probability for b in self.branches)
            self.value = ev
            return ev

        # DECISION node
        pick = max if self.maximize else min
        best_label = pick(branch_totals, key=branch_totals.get)
        self.value = branch_totals[best_label]
        self.optimal_branch = best_label
        return self.value


@dataclass
class DecisionTree:
    """Wraps a root Node; adds evaluation entry point + Plotly rendering."""
    root: Node
    title: str = "Decision Tree Analysis"

    def evaluate(self) -> float:
        return self.root.evaluate()

    # -- layout: assign (x, y) to every node via simple recursive spacing ----
    def _layout(self) -> Tuple[Dict[str, dict], List[dict]]:
        """
        Returns (node_positions, edges) where:
          node_positions[node.name] = {"x","y","node": Node}
          edges = list of dicts with x0,y0,x1,y1,label,is_optimal,branch
        """
        positions: Dict[str, dict] = {}
        edges: List[dict] = []
        leaf_counter = {"i": 0}

        def depth_of(node: Node) -> int:
            if not node.branches:
                return 0
            return 1 + max(depth_of(b.child) for b in node.branches)

        def place(node: Node, depth: int) -> float:
            """Post-order placement; returns the y-coordinate assigned to `node`."""
            if not node.branches:
                y = leaf_counter["i"]
                leaf_counter["i"] += 1
            else:
                child_ys = []
                for b in node.branches:
                    cy = place(b.child, depth + 1)
                    child_ys.append(cy)
                    is_opt = (node.node_type == NodeType.DECISION and node.optimal_branch == b.label)
                    cx = positions[b.child.name]["x"]
                    edges.append(dict(
                        x0=depth, y0=None,  # y0 filled after we know this node's y
                        x1=cx, y1=cy,
                        label=b.label, probability=b.probability,
                        is_optimal=is_opt,
                        parent=node.name, child=b.child.name,
                    ))
                y = sum(child_ys) / len(child_ys)

            positions[node.name] = {"x": depth, "y": y, "node": node}
            return y

        place(self.root, 0)
        for e in edges:
            e["y0"] = positions[e["parent"]]["y"]
        return positions, edges

    # -- rendering -------------------------------------------------------------
    def plot(self, currency: str = "$", value_fmt: str = ",.1f") -> go.Figure:
        positions, edges = self._layout()
        max_depth = max(p["x"] for p in positions.values()) or 1

        fig = go.Figure()

        # edges (draw first so nodes sit on top)
        for e in edges:
            color = "#2E86AB" if e["is_optimal"] else "#B0B0B0"
            width = 4 if e["is_optimal"] else 1.5
            fig.add_trace(go.Scatter(
                x=[e["x0"], e["x1"]], y=[e["y0"], e["y1"]],
                mode="lines", line=dict(color=color, width=width),
                hoverinfo="skip", showlegend=False,
            ))
            mid_x, mid_y = (e["x0"] + e["x1"]) / 2, (e["y0"] + e["y1"]) / 2
            label = e["label"]
            if e["probability"] is not None:
                label += f"  p={e['probability']:.2f}"
            fig.add_annotation(
                x=mid_x, y=mid_y, text=label, showarrow=False,
                font=dict(size=11, color=color), bgcolor="rgba(255,255,255,0.85)",
                yshift=10,
            )

        # nodes
        shape_map = {NodeType.DECISION: "square", NodeType.CHANCE: "circle", NodeType.TERMINAL: "triangle-right"}
        color_map = {NodeType.DECISION: "#F26419", NodeType.CHANCE: "#2E86AB", NodeType.TERMINAL: "#4C9A2A"}

        for name, p in positions.items():
            node: Node = p["node"]
            hover = f"{node.name}<br>EV: {currency}{node.value:,.2f}" if node.value is not None else node.name
            if node.node_type == NodeType.DECISION and node.optimal_branch:
                hover += f"<br>Optimal: {node.optimal_branch}"
            fig.add_trace(go.Scatter(
                x=[p["x"]], y=[p["y"]], mode="markers+text",
                marker=dict(symbol=shape_map[node.node_type], size=28,
                            color=color_map[node.node_type], line=dict(width=1, color="white")),
                text=[f"{node.name}<br>{currency}{node.value:,.1f}" if node.value is not None else node.name],
                textposition="bottom center", textfont=dict(size=11),
                hovertext=hover, hoverinfo="text", showlegend=False,
            ))

        # legend (dummy traces)
        for nt, label in [(NodeType.DECISION, "Decision node"), (NodeType.CHANCE, "Chance node"),
                           (NodeType.TERMINAL, "Terminal (NPV)")]:
            fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers",
                                      marker=dict(symbol=shape_map[nt], size=14, color=color_map[nt]),
                                      name=label))

        fig.update_layout(
            title=self.title,
            xaxis=dict(visible=False, range=[-0.5, max_depth + 1.5]),
            yaxis=dict(visible=False),
            plot_bgcolor="white", height=520 + 40 * len(positions) // max(1, max_depth + 1),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            margin=dict(l=40, r=120, t=80, b=40),
        )
        return fig


# ---------------------------------------------------------------------------
# Example: E&P appraisal/development decision under uncertainty
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Terminal NPVs here are placeholders — in practice, each would come from
    # a pyscnomics CostRecovery.run() -> get_summary() call for that scenario's
    # production profile, cost structure, and fiscal terms.

    # Terminal values are net NPVs (any capex/drilling cost is already
    # netted in — e.g. by pyscnomics.CostRecovery.run() -> get_summary()
    # for that scenario's production profile, cost structure, and fiscal terms).

    # --- Success branch: choose Large vs Small development ---
    dev_large_success = Node("NPV: Large Dev | Success", NodeType.TERMINAL, value=550.0)
    dev_small_success = Node("NPV: Small Dev | Success", NodeType.TERMINAL, value=300.0)

    develop_decision = Node("Develop?", NodeType.DECISION, maximize=True)
    develop_decision.add_branch(Branch("Large development", dev_large_success))
    develop_decision.add_branch(Branch("Small development", dev_small_success))

    # --- Dry branch: abandon ---
    abandon = Node("NPV: Abandon | Dry", NodeType.TERMINAL, value=-80.0)

    # --- Chance node: drilling outcome ---
    drill_outcome = Node("Drilling Outcome", NodeType.CHANCE)
    drill_outcome.add_branch(Branch("Success (POS=35%)", develop_decision, probability=0.35))
    drill_outcome.add_branch(Branch("Dry (65%)", abandon, probability=0.65))

    # --- Alternative top-level choice: farm-out instead of drilling ---
    farm_out = Node("NPV: Farm-out", NodeType.TERMINAL, value=60.0)

    # --- Root decision: Drill vs Farm-out ---
    root = Node("Drill or Farm-out?", NodeType.DECISION, maximize=True)
    root.add_branch(Branch("Drill exploration well", drill_outcome))
    root.add_branch(Branch("Farm-out", farm_out))

    tree = DecisionTree(root, title="E&P Appraisal Decision Tree (illustrative NPVs, $MM)")
    ev = tree.evaluate()
    print(f"Root expected value: ${ev:,.2f} MM")
    print(f"Optimal top-level choice: {root.optimal_branch}")
    print(f"Optimal development choice (if success): {develop_decision.optimal_branch}")

    fig = tree.plot()
    fig.write_html("decision_tree_demo.html")
    print("Saved interactive plot to decision_tree_demo.html")
