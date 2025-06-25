# src/client.py
import requests
import time

NODES = {
    "node1": "http://localhost:5001",
    "node2": "http://localhost:5002",
    "node3": "http://localhost:5003"
}

def log_header(title):
    print("\n" + "="*10 + f" {title} " + "="*10)

def local_put(node, key, value):
    # log_header(f"Local PUT {key}={value} @ {node}")
    url = f"{NODES[node]}/local_put"
    resp = requests.post(url, json={"key": key, "value": value})
    print(resp.json())
    time.sleep(1)

def scenario_1_independent_writes():
    log_header("SCENARIO 1: Independent Writes to Different Keys")
    local_put("node1", "a", "A1")
    local_put("node2", "b", "B1")
    local_put("node3", "c", "C1")

def scenario_2_causal_chain():
    log_header("SCENARIO 2: Causal Chain Across Nodes")
    local_put("node1", "x", "X1")
    local_put("node2", "x", "X2")  # should wait for X1
    local_put("node3", "x", "X3")  # should wait for X2

def scenario_3_parallel_causal_writes():
    log_header("SCENARIO 3: Concurrent Writes to Same Key")
    # Fire two writes to the same key from different nodes without dependency
    local_put("node1", "y", "Y1")
    local_put("node2", "y", "Y2")

def scenario_4_out_of_order():
    log_header("SCENARIO 4: Out-of-Order Arrival Simulation")
    local_put("node2", "z", "Z2")
    time.sleep(0.5)
    local_put("node1", "z", "Z1")

def get_status(node):
    print(f"\n--- Status of {node} ---")
    resp = requests.get(f"{NODES[node]}/status")
    print(resp.json())

def show_all_statuses():
    log_header("Final Node States")
    for node in NODES:
        get_status(node)

if __name__ == "__main__":
    scenario_1_independent_writes()
    scenario_2_causal_chain()
    scenario_3_parallel_causal_writes()
    scenario_4_out_of_order()
    time.sleep(2)
    show_all_statuses()
