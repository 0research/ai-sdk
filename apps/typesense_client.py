import typesense
import os
import socket
import ast
import uuid
import pandas as pd
from pandas import json_normalize
from pprint import pprint

def typesense_client(host, port, protocol, api_key, timeout=2):
    return typesense.Client({
        'nodes': [{
        'host': host, # For Typesense Cloud use xxx.a1.typesense.net
        'port': port,      # For Typesense Cloud use 443
        'protocol': protocol   # For Typesense Cloud use https
        }],
        'api_key': api_key,
        'connection_timeout_seconds': 2
    })

def generate_schema_auto(name):
    return {
        "name": name,  
        "fields": [{"name": ".*", "type": "auto" }]
    }


def initialize_typesense():
    # Initialize Typesense
    if socket.gethostname() == 'DESKTOP-9IOI6RV':
        client = typesense_client('oswmql6f04pndbi1p-1.a1.typesense.net', '443', 'https', os.environ['TYPESENSE_API_KEY']) # Typesense Cloud
        # client = typesense_client('localhost', '8108', 'http', 'Hu52dwsas2AdxdE') 
    else:
        client = typesense_client('oswmql6f04pndbi1p-1.a1.typesense.net', '443', 'https', os.environ['TYPESENSE_API_KEY']) # Typesense Cloud

    collection_list = ['dataset', 'node', 'session1'] # TODO Currently all users will use same session. Replace when generate user/session ID
    for name in collection_list:
        try:
            client.collections.create(generate_schema_auto(name))
        except typesense.exceptions.ObjectAlreadyExists:
            pass
        except Exception as e:
            print(e)

    return client

client = initialize_typesense()




def search_documents(collection_id, per_page):
    search_parameters = {
        'q': '*',
        'per_page': per_page,
    }
    result = client.collections[collection_id].documents.search(search_parameters)
    return [d['document'] for d in result['hits']]

def get_document(collection_id, document_id):
    doc = client.collections[collection_id].documents[document_id].retrieve()
    for k, v in doc.items():
        if (v[0] == '[' and v[-1] == ']') or (v[0] == '{' and v[-1] == '}'):
            try: 
                doc[k] = ast.literal_eval(v)
            except Exception as e: 
                print(e)
    return doc
def create(collection_id, document):
    document = {k:str(v) for k, v in document.items()}
    client.collections[collection_id].documents.create(document)

def upsert(collection_id, document):
    document = {k:str(v) for k, v in document.items()}
    client.collections[collection_id].documents.upsert(document)



# Store & Retrieve Session
def store_session(key, value):
    session_id = 'session1' # TODO Currently all users will use same session. Replace when generate user/session ID
    client.collections[session_id].documents.upsert({'id': key, 'value': str(value)})
def get_session(key):
    session_id = 'session1' # TODO Currently all users will use same session. Replace when generate user/session ID
    return client.collections[session_id].documents[key].retrieve()['value']



# Typesense Object
def Project(id, type, cDataset, cAction, cEdge):
    return {
        'id': id, 
        'type': type, 
        'cytoscape_dataset': cDataset,
        'cytoscape_action': cAction,
        'cytoscape_edge': cEdge
    }
def Dataset(id, description, type, api_data, column, datatype, expectation, index, target):
    return {
        'id': id,
        'description': description,
        'type': type,
        'api_data': api_data, # Source, Delimiter, remove_space, remove_header
        'column': list(column),
        'datatype': datatype,
        'expectation': expectation,
        'index': index, 
        'target': target,
    }

# Cytoscape Object 
def cNode(node_id, node_type, label=''):
    return {
        'data': {'id': node_id, 'label': label},
        # 'position': {'x': 50, 'y': 50},
        'classes': node_type,
    }
def cEdge(source_node_id, destination_node_id, label='', extra_data=''):
    return {
        'data': {
                'id': source_node_id + '-' + destination_node_id,
                'source': source_node_id,
                'target': destination_node_id,
                'label': '',
                'extra_data': extra_data,
            },
            'selectable': False
    }

def action(dataset_id, source_node_id, data, label=''):
    # Dataset Document
    dataset = get_document('dataset', dataset_id)
    node_id = str(uuid.uuid1())
    dataset['node'].append(node_id)
    node = cNode(node_id, node_type='dataset', label=label)
    edge = cEdge(source_node_id, node_id, label=label)
    
    dataset['cytoscape_node'].append(node)
    dataset['cytoscape_edge'].append(edge)

    node2 = cNode(node_id, node_type='action', label=label)
    edge2 = cEdge(source_node_id, node_id, label=label)

    # Node Document
    source_node = get_document('node', source_node_id)
    df = get_node_data(source_node_id)
    node = {
        'id': node_id,
        'description': None, 
        'source': None,
        'delimiter': None, 
        'remove_space': None,
        'remove_header': None,
        'type': 'dataset', 
        'datatype': {col:str(datatype) for col, datatype in zip(df.columns, df.convert_dtypes().dtypes)}, 
        'columns': source_node['columns'],
        'columns_deleted': source_node['columns_deleted'],
        'expectation': {col:None for col in df.columns}, 
        'index': [],
        'target': [], 
    }

    # Node Data Collection
    df = json_normalize(data)
    jsonl = df.to_json(orient='records', lines=True) # Convert to jsonl
    
    # Upload
    upsert('dataset', dataset)
    upsert('node', node)
    client.collections.create(generate_schema_auto(node_id))
    client.collections[node_id].documents.import_(jsonl, {'action': 'create'})



def merge_nodes(dataset_id, source_node_id_list, label='', node_type='blob'):
    # Dataset Document
    dataset = get_document('dataset', dataset_id)
    node_id = str(uuid.uuid1())
    node = cNode(node_id, node_type, label=label)
    dataset['node'].append(node_id)
    dataset['cytoscape_node'].append(node)
    for source_node_id in source_node_id_list:
        edge = cEdge(source_node_id, node_id, label=label)
        dataset['cytoscape_edge'].append(edge)

    # Node Document
    source_node = get_document('node', source_node_id)
    df = get_node_data(source_node_id)
    node = {
        'id': node_id,
        'description': None, 
        'source': None,
        'delimiter': None, 
        'remove_space': None,
        'remove_header': None,
        'type': node_type, 
        'datatype': {col:str(datatype) for col, datatype in zip(df.columns, df.convert_dtypes().dtypes)}, 
        'columns': source_node['columns'],
        'columns_deleted': source_node['columns_deleted'],
        'expectation': {col:None for col in df.columns}, 
        'index': [],
        'target': [], 
    }

    # Node Data Collection
    df_list = [get_node_data(source_node_id) for source_node_id in source_node_id_list]
    df = pd.concat(df_list)
    jsonl = df.to_json(orient='records', lines=True) # Convert to jsonl
    
    # Upload
    upsert('dataset', dataset)
    upsert('node', node)
    client.collections.create(generate_schema_auto(node_id))
    client.collections[node_id].documents.import_(jsonl, {'action': 'create'})



def get_node_data(node_id):
    node = get_document('node', node_id)
    data = search_documents(node_id, '250')
    df = json_normalize(data)
    df = df[node['columns']]

    return df