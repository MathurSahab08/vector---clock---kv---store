from flask import Flask, request, jsonify
import requests
import sys

app = Flask(__name__)
store = {}
vector_clock = {}
buffer = []


NODE_ID = None
ALL_NODES = []
PORT = None

def init_vector_clock():

    # creating a dictionary vector_clock with initial values of all nodes as 0
    global vector_clock
    vector_clock = {node: 0 for node in ALL_NODES}
    print('initialising vector clock.. --> ', vector_clock)

def increment_clock():
    vector_clock[NODE_ID] += 1
    print('vector clock value after increment --> ', vector_clock)

# obtain max value for each node and update in current node's vector clock
def update_clock(received_vc):
    for node in received_vc:
        vector_clock[node] = max(vector_clock[node], received_vc[node])

def get_sender_from_vector(received_vc):
    for node in received_vc:
        if received_vc[node] > vector_clock.get(node, 0):
            return node
    return None

# checks current node's vector clock value for every node, return false if even a single value is greater than existing value
def can_deliver(received_vc):
    sender = get_sender_from_vector(received_vc)
    if sender is None:
        return False
    for node in received_vc:
        if node == sender:
            if received_vc[node] != vector_clock.get(node, 0) + 1:
                return False
        else:
            if received_vc[node] > vector_clock.get(node, 0):
                return False
    return True

def deliver_buffered_messages():
    global buffer
    delivered = True
    while delivered:
        delivered = False
        still_buffered = []
        for msg in buffer:
            if can_deliver(msg['vector_clock']):
                key, value = msg['key'], msg['value']
                store[key] = value
                update_clock(msg['vector_clock'])
                print(f"[{NODE_ID}] Delivered from buffer: {key}={value}")
                delivered = True
            else:
                still_buffered.append(msg)
        buffer = still_buffered

# this method recieves the sent node's key-value pair and vector clock and evaluates whether to buffer
@app.route('/put', methods=['POST'])
def put():
    data = request.json

    # vc = vector clock of the sent node
    key, value, vc = data['key'], data['value'], data['vector_clock']

    if not can_deliver(vc):
        buffer.append(data)
        return jsonify({"status": "buffered"})

    store[key] = value

    # if sent node's vector clock has lower node values then current nodes' vc values, get max values of each node from both vc's
    update_clock(vc)
    deliver_buffered_messages()
    return jsonify({"status": "stored", "store": store, "clock": vector_clock})

# method to process client request locally; adds +1 to the value of current node's vector clock; updates key-value store
@app.route('/local_put', methods=['POST'])
def local_put():
    data = request.json
    key, value = data['key'], data['value']
    increment_clock()
    store[key] = value
    print('store value --> ', store)
    replicate_write(key, value)
    return jsonify({"status": "local_stored", "clock": vector_clock})

# calls put method; provides current node's key-value pair and  vector clock to other nodes
def replicate_write(key, value):
    for node in ALL_NODES:
        if node == NODE_ID:
            continue
        try:
            requests.post(f'http://{node}:5000/put', json={'key': key, 'value': value, 'vector_clock': vector_clock})
        except:
            continue

@app.route('/status')
def status():
    print('Get current status...')
    return jsonify({"store": store, "clock": vector_clock, "buffer": buffer})

def start_server():
    app.run(host='0.0.0.0', port=5000)



if __name__ == '__main__':
    # obtaining NODE_ID and ALL_NODES from environment variables provided by the 'command'
    NODE_ID = sys.argv[1]
    ALL_NODES = sys.argv[2].split(',')
    init_vector_clock()
    start_server()
