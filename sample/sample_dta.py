from sample.sample_contract_abandon import project as project_abandon
from sample.sample_contract_small_dev import project as project_small_dev
from sample.sample_contract_large_dev import project as project_large_dev
from sample.sample_contract_dry import project as project_dry

from sample.sample_contract_abandon import fiscal as fiscal_abandon
from sample.sample_contract_small_dev import fiscal as fiscal_small_dev
from sample.sample_contract_large_dev import fiscal as fiscal_large_dev
from sample.sample_contract_dry import fiscal as fiscal_dry

from sample.sample_contract_abandon import summary_parameter as summary_abandon
from sample.sample_contract_small_dev import summary_parameter as summary_small_dev
from sample.sample_contract_large_dev import summary_parameter as summary_large_dev
from sample.sample_contract_dry import summary_parameter as summary_dry

from pyscnomics.extension.decision_tree import NodeType, Branch, Node, DecisionTree

# --- Success branch: choose Large vs Small development ---
dev_large_success = Node(
    name="NPV: Large Dev | Success",
    node_type=NodeType.TERMINAL,
    contract=project_large_dev,
    contract_args=fiscal_large_dev,
    summary_args=summary_large_dev
)

dev_small_success = Node(
    name="NPV: Small Dev | Success",
    node_type=NodeType.TERMINAL,
    contract=project_small_dev,
    contract_args=fiscal_small_dev,
    summary_args=summary_small_dev
)

develop_decision = Node("Develop?", NodeType.DECISION, maximize=True)
develop_decision.add_branch(Branch("Large development", dev_large_success))
develop_decision.add_branch(Branch("Small development", dev_small_success))

# --- Dry branch: abandon ---
abandon = Node(
    name="NPV: Abandon | Dry",
    node_type=NodeType.TERMINAL,
    contract=project_dry,
    contract_args=fiscal_dry,
    summary_args=summary_dry
)

# --- Chance node: drilling outcome ---
drill_outcome = Node("Drilling Outcome", NodeType.CHANCE)
drill_outcome.add_branch(Branch("Success", develop_decision, probability=0.67))
drill_outcome.add_branch(Branch("Dry", abandon, probability=0.33))

# --- Alternative top-level choice: farm-out instead of drilling ---
farm_out = Node(
    name="NPV: Farm-out",
    node_type=NodeType.TERMINAL,
    contract=project_abandon,
    contract_args=fiscal_abandon,
    summary_args=summary_abandon
)

# --- Root decision: Drill vs Farm-out ---
root = Node("Drill or Farm-out?", NodeType.DECISION, maximize=True)
root.add_branch(Branch("Drill exploration well", drill_outcome))
root.add_branch(Branch("Farm-out", farm_out))

tree = DecisionTree(root, title="E&P Appraisal Decision Tree (EMV NPVs, $MM)")
ev = tree.evaluate()
print(f"Root expected value: ${ev:,.2f} MM")
print(f"Optimal top-level choice: {root.optimal_branch}")
print(f"Optimal development choice (if success): {develop_decision.optimal_branch}")

fig = tree.plot()
fig.write_html("decision_tree.html")
fig.show()
print("Saved interactive plot to decision_tree_demo.html")
