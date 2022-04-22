import typesense
import os
import socket
import ast
import uuid
import pandas as pd
from pandas import json_normalize
from pprint import pprint
from jsondiff import diff, symbols
import json
from apps.util import *
from datetime import datetime

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
    if name == 'node':
        out = {
            "name": name,
            "fields": [
                {"name": ".*", "type": "string*"},
                {"name": "type", "type": "string*", "facet": True},
            ]
        }
    else:
        out = {
            "name": name,
            "fields": [ {"name": ".*", "type": "string*" } ]
        }
        print(name, out)
    return out


def initialize_typesense():
    print('Initializing Typesense')
    
    if socket.gethostname() == 'DESKTOP-9IOI6RV':
        client = typesense_client('127.0.0.1', '8108', 'http', 'Hu52dwsas2AdxdE')
    else:
        # client = typesense_client('39pfe1mawh8i0lx7p-1.a1.typesense.net', '443', 'https', 'ON8Qi0o4Fh8oDWQHVVPeRQx9Unh6VoR3') # Typesense Cloud
        client = typesense_client('39pfe1mawh8i0lx7p-1.a1.typesense.net', '443', 'https', os.environ['TYPESENSE_API_KEY']) # Typesense Cloud

    collection_list = ['project', 'node', 'graph', 'node_log', 'session1'] # TODO Currently all users will use same session. Replace when generate user/session ID
    for name in collection_list:
        try:
            client.collections.create(generate_schema_auto(name))
            print('Create Typesense Collection: ', name)
        except typesense.exceptions.ObjectAlreadyExists:
            pass
            # print('Typesense Object Already Exist')
        except Exception as e:
            print('Initialize Typesense Failed: ', e)
    
    return client

client = initialize_typesense()



 # Basic Typesense Functions
def get_document(collection_id, document_id):
    doc = client.collections[collection_id].documents[document_id].retrieve()
    for k, v in doc.items():
        if len(v)>0:
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

def search_documents(collection_id, per_page=250, search_parameters=None):
    if search_parameters is None:
        search_parameters = {
            'q': '*',
            'per_page': per_page,
        }
    if collection_id in [c['name'] for c in client.collections.retrieve()]:
        result = client.collections[collection_id].documents.search(search_parameters)
        result = [d['document'] for d in result['hits']]
    else:
        result = None
    return result

def get_dataset_data(dataset_id):
    dataset = get_document('node', dataset_id)
    features = list(dataset['features'].keys())
    data = search_documents(dataset_id)
    if data != None:
        return json_normalize(data)[features]
    else:
        return json_normalize([])


# Store & Retrieve Session
def store_session(key, value):
    session_id = 'session1' # TODO Currently all users will use same session. Replace when generate user/session ID
    client.collections[session_id].documents.upsert({'id': key, 'value': str(value)})
def get_session(key):
    try:
        session_id = 'session1' # TODO Currently all users will use same session. Replace when generate user/session ID
        session_value = client.collections[session_id].documents[key].retrieve()['value']
        session_value = session_value
    except Exception as e:
        # print(e)
        return None
    return session_value

# Typesense Object
def Project(id, type, dataset=[], edge=[], graph_dict={}, experiment=[], node_log={}):
    return {
        'id': id, 
        'type': type,
        'node_list': dataset,
        'edge_list': edge,
        'graph_dict': graph_dict,
        'experiment': experiment,
        'node_log': node_log,
    }
def Node(id, name, description, type, inputs=[], outputs=[], state='', action='',
            documentation='', details={}, features={}, expectation={}, index=[], graphs=[]):
    return {
        'id': id,
        'name': name,
        'description': description,
        'type': type,
        'inputs': inputs,
        'outputs': outputs,
        'state': state,
        'action': action,
        'documentation': documentation,
        'details': details, 
        'features': features,
        'expectation': expectation,
        'index': index,
        'graphs': graphs,
    }


# Cytoscape Object 
def cNode(id, name, type, state='', action='', position={'x': 0, 'y': 0}, classes=''):
    return {
        'data': {'id': id, 'name': name, 'type': type, 'state': state, 'action': action},
        'position': position,
        'classes': classes,
    }
def cEdge(dataset_id_source, destination_id, position=None, classes=''):
    return {
        'data': {
                'id': dataset_id_source + '_' + destination_id,
                'source': dataset_id_source,
                'target': destination_id,
            },
        'selectable': False,
        'position': position,
        'classes': classes,
    }


# Create New Project
def new_project(project_id, project_type):
    project = Project(id=project_id, type=project_type)
    create('project', project)

# Create Raw Data Source
def new_data_source():
    dataset_id = str(uuid.uuid1())
    dataset = Node(
            id=dataset_id,
            name='New',
            description='',
            documentation='',
            type='raw',
    )
    upsert('node', dataset)
    return dataset_id

# Retrieve all Collections
def get_all_collections():
    return [c['name'] for c in client.collections.retrieve()]




def update_node_log(project_id, node_id, description, timestamp=None):
    project = get_document('project', project_id)
    log_id = str(uuid.uuid1())
    timestamp = str(datetime.now()) if timestamp is None else timestamp
    log = {
        'id': log_id,
        'timestamp': timestamp,
        'description': description,
    }
    if node_id in project['node_log']: project['node_log'][node_id].append(log_id)
    else: project['node_log'][node_id] = [log_id]

    upsert('project', project)
    upsert('node_log', log)


def save_data_source(df, node_id, type, details):
    node = get_document('node', node_id)
    node['type'] = type
    node['details'] = details
    features = {str(col):str(datatype) for col, datatype in zip(df.columns, df.convert_dtypes().dtypes)}
    if type == 'raw_restapi':
        features['timestamp'] = 'datetime64'
    node['features'] = features
    node['expectation'] = {col:None for col in df.columns}

    # Upload to Typesense
    upsert('node', node)
    update_node_log(get_session('project_id'), node_id, 'Uploaded Data Source {}'.format(details))
    
    collection_name_list = [row['name'] for row in client.collections.retrieve()]
    if node_id in collection_name_list:
        client.collections[node_id].delete()
        # print("Dropped Collection: ", node_id)
    client.collections.create(generate_schema_auto(node_id))
    jsonl = df.to_json(orient='records', lines=True) # Convert to jsonl
    r = client.collections[node_id].documents.import_(jsonl, {'action': 'create'})
    # print("Created Collection: ", node_id)



def add_dataset(project_id, dataset_id):
    project = get_document('project', project_id)
    if dataset_id not in [d['id'] for d in project['node_list']]:
        # If node position is taken, move default initial position
        x, y = 0 ,0
        while True:
            for node in project['node_list']:
                pos_diff_x = abs(node['position']['x'] - x)
                pos_diff_y = abs(node['position']['y'] - y)
                if pos_diff_x < 5 and pos_diff_y < 5:
                    x += 20
                    y += 20
            break
        project['node_list'].append({'id': dataset_id, 'position': {'x': x, 'y': y}})
        
        # Upload to Typesense
        upsert('project', project)
        return True
    else:
        return False


def remove(project_id, selectedNodeData):
    project = get_document('project', project_id)
    edge_list = project['edge_list'].copy()

    for node in selectedNodeData:
        node_id = node['id']

        # Debugging
        if node['type'] == 'processed':
            for edge in edge_list:
                if node_id in edge:
                    return
            project['node_list'] = [node for node in project['node_list'] if node['id'] != node_id]

        # Remove Action or '' (for debugging)
        elif node['type'] == 'action' or node['type'] == '':
            destination_node_id_list = [edge.split('_')[1] for edge in edge_list if edge.startswith(node_id)]

            project['node_list'] = [node for node in project['node_list'] if node['id'] != node_id]
            for edge in edge_list:
                if node_id in edge:
                    project['edge_list'].remove(edge)
                if node_id == edge.split('_')[0]:
                    project['node_list'] = [node for node in project['node_list'] if node['id'] != edge.split('_')[1]]
                if any(edge.startswith(destination_node_id) for destination_node_id in destination_node_id_list):
                    return
   
        # Remove Raw Dataset
        elif node['type'] == 'raw':
            dataset = get_document('node', node_id)
            if dataset['type'] == 'raw':
                if any(edge.startswith(node_id) for edge in edge_list):
                    pass
                else:
                    project['node_list'] = [d for d in project['node_list'] if d['id'] != node_id]
                    for edge in [edge for edge in edge_list if edge.startswith(node_id)]:
                        project['edge_list'].remove(edge)
        else:
            print('[Error] Unable to delete Node: ', node_id)
    
    upsert('project', project)
    
def cytoscape_action(source_id_list):
    # Get Node Position
    project = get_document('project', get_session('project_id'))
    dataset_position_list = [d for d in project['node_list'] if d['id'] in source_id_list]
    x, y, num_sources = 0, [], len(source_id_list)
    for d in dataset_position_list:
        x += d['position']['x']
        y.append(d['position']['y'])
    x = x/num_sources
    y = max(y) + 100

    # Generate New Node
    action_id = str(uuid.uuid1())
    new_node_id = str(uuid.uuid1())
    project['node_list'].append({'id': action_id, 'position': {'x': x, 'y': y}})
    project['node_list'].append({'id': new_node_id, 'position': {'x': x, 'y': y+100}})

    action = Node(id=action_id, name='', description='', type='action', inputs=source_id_list, outputs=[new_node_id], state='yellow')
    new_node = Node(id=new_node_id, name='New', description='', type='processed')
    
    # Upload Changes
    upsert('project', project)
    upsert('node', action)
    upsert('node', new_node)


def action(project_id, dataset_id_source, action, dataset_metadata, df_dataset_data=None, details=None):
    # New id
    action_id = str(uuid.uuid1())
    dataset_id = str(uuid.uuid1())
    edge1 = dataset_id_source + '_' + action_id
    edge2 = action_id + '_' + dataset_id

    # Project Document
    project = get_document('project', project_id)

    node = next(node for node in project['node_list'] if node["id"] == dataset_id_source)
    x = node['position']['x']
    y = node['position']['y'] + 100
    
    project['node_list'].append({'id': action_id, 'position': {'x': x, 'y': y} })
    project['node_list'].append({'id': dataset_id, 'position': {'x': x, 'y': y + 100}})
    project['edge_list'].append(edge1)
    project['edge_list'].append(edge2)

    # # Action Document
    # if details is None:
    #     details = diff(get_document('node', dataset_id_source), dataset_metadata, syntax='symmetric', marshal=True)
    #     action_metadata = Node(id=action_id, name='', description='', documentation='', type=action, details=details)

    # # Dataset Document
    # dataset_metadata['id'] =  dataset_id # Overwrite previous dataset ID
    # dataset_metadata['type'] = 'processed'
    # dataset_metadata['details'] = None
    # dataset_metadata['name'] = ''

    # # Dataset Data Collection
    # if df_dataset_data is None:
    #     dataset_data = search_documents(dataset_id)
    #     df_dataset_data = json_normalize(dataset_data)
    # jsonl = df_dataset_data.to_json(orient='records', lines=True) # Convert to jsonl
    
    # Upload
    upsert('project', project)
    # upsert('node', action_metadata)
    # upsert('node', dataset_metadata)
    # client.collections.create(generate_schema_auto(dataset_id))
    # client.collections[dataset_id].documents.import_(jsonl, {'action': 'create'})


def add_edge(project_id, source_id, destination_id):
    project = get_document('project', project_id)
    edge = source_id + '_' + destination_id
    if edge in project['edge_list']:
        return
    else:
        project['edge_list'].append(edge)
        upsert('project', project)


def merge(project_id, source_id_list, dataset_data_store, dataset, details):
    # New id
    action_id = str(uuid.uuid1())
    dataset_id = str(uuid.uuid1())

    # Project Document
    project = get_document('project', project_id)
    dataset_position_list = [d for d in project['node_list'] if d['id'] in source_id_list]
    x, y, num_sources = 0, [], len(source_id_list)
    for d in dataset_position_list:
        x += d['position']['x']
        y.append(d['position']['y'])
    x = x/num_sources
    y = max(y) + 100

    project['node_list'].append({'id': action_id, 'position': {'x': x, 'y': y}})
    project['node_list'].append({'id': dataset_id, 'position': {'x': x, 'y': y+100}})
    for dataset_id_source in source_id_list:
        edge_id = dataset_id_source + '_' + action_id
        project['edge_list'].append(edge_id)
    project['edge_list'].append(action_id + '_' + dataset_id)

    # Dataset Data Collection
    df = json_normalize(dataset_data_store)
    jsonl = df.to_json(orient='records', lines=True) # Convert to jsonl

    # Action Document
    action = Node(id=action_id, name='', description='', documentation='', type='action_3', details=details)

    # Dataset Document
    dataset['id'] =  dataset_id # Overwrite previous dataset ID
    dataset['type'] = 'processed'
    dataset['details'] = None
    dataset['name'] = ''
    
    # Upload
    upsert('project', project)
    upsert('node', action)
    upsert('node', dataset)
    client.collections.create(generate_schema_auto(dataset_id))
    client.collections[dataset_id].documents.import_(jsonl, {'action': 'create'})



def upsert_graph(project_id, node_id, graph_id, log_description, graph):
    project = get_document('project', project_id)
    if 'graph_dict' not in project:
        project['graph_dict'] = {}

    if node_id in project['graph_dict']:
        if graph_id not in project['graph_dict'][node_id]:
            project['graph_dict'][node_id].append(graph_id)
    else:
        project['graph_dict'][node_id] = [graph_id]

    upsert('project', project)
    update_node_log(project_id, node_id, log_description + graph_id)
    upsert('graph', graph)

    


    

def generate_cytoscape_elements(project_id):
    project = get_document('project', project_id)
    
    cNode_list, cEdge_list = [], []
    for d in project['node_list']:
        position = {'x': d['position']['x'], 'y': d['position']['y']}
        node = get_document('node', d['id'])

        cNode_list.append(
            cNode(
                node['id'], 
                name=node['name'], 
                type=node['type'],
                state=node['state'], 
                action=node['action'], 
                position=position
            )
        )

        if node['type'] == 'action':
            cEdge_list += [cEdge(inp, node['id']) for inp in node['inputs']]
            cEdge_list += [cEdge(node['id'], output) for output in node['outputs']]

    return cNode_list + cEdge_list
