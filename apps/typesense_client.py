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
    out = {
        "name": name,
        "fields": [ {"name": ".*", "type": "string*" } ]
    }
    if name == 'dataset':
        out['fields'].append({"name": "type", "type": "string", "facet": True })
    return out


def initialize_typesense():
    # Initialize Typesense
    print('Initializing Typesense. Host: ' + socket.gethostname())
    if socket.gethostname() == 'DESKTOP-9IOI6RV':
        client = typesense_client('127.0.0.1', '8108', 'http', 'Hu52dwsas2AdxdE') 
    else:
        client = typesense_client('39pfe1mawh8i0lx7p-1.a1.typesense.net', '443', 'https', os.environ['TYPESENSE_API_KEY']) # Typesense Cloud
        # client = typesense_client('typesense', '8108', 'http', 'Hu52dwsas2AdxdE')

    collection_list = ['project', 'node', 'session1'] # TODO Currently all users will use same session. Replace when generate user/session ID
    for name in collection_list:
        try:
            client.collections.create(generate_schema_auto(name))
            print('Create Typesense Collection: ', name)
        except typesense.exceptions.ObjectAlreadyExists:
            pass
        except Exception as e:
            print(e)
    
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

def search_documents(collection_id, per_page, search_parameters=None):
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
    data = search_documents(dataset_id, '250')
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
def Project(id, type, dataset=[], edge=[], experiment=[]):
    return {
        'id': id, 
        'type': type,
        'node_list': dataset,
        'edge_list': edge,
        'experiment': experiment
    }
def Node(id, name, description, documentation, type, details={}, features={}, expectation={}, index=[], target=[], graphs=[]):
    return {
        'id': id,
        'name': name,
        'description': description,
        'documentation': documentation,
        'type': type,
        'details': details, 
        'features': features,
        'expectation': expectation,
        'index': index, 
        'target': target,
        'graphs': graphs
    }


# Cytoscape Object 
def cNode(id, name, type, className, action_label, position={'x': 0, 'y': 0}):
    return {
        'data': {'id': id, 'name': name, 'type': type, 'action_label':action_label},
        'position': position,
        'classes': className,
    }
def cEdge(dataset_id_source, destination_id, position=None):
    return {
        'data': {
                'id': dataset_id_source + '_' + destination_id,
                'source': dataset_id_source,
                'target': destination_id,
            },
        'selectable': False,
        'position': position,
        'classes': '',
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
            name='New Data Source',
            description='',
            documentation='',
            type='raw',
    )
    upsert('node', dataset)
    return dataset_id

# Retrieve all Collections
def get_all_collections():
    return [c['name'] for c in client.collections.retrieve()]




def save_dataset_config(dataset_id, df, name, description, documentation, type, details):
    # Dataset
    if df is None:
        dataset = get_document('node', dataset_id)
        dataset['name'] = name
        dataset['description'] = description
        dataset['documentation'] = documentation
    else:
        dataset = Node(
                id=dataset_id,
                name=name,
                description=description, 
                documentation=documentation,
                type=type,
                details=details, 
                features={str(col):str(datatype) for col, datatype in zip(df.columns, df.convert_dtypes().dtypes)},
                expectation = {col:None for col in df.columns}, 
        )
    
    # Upload to Typesense
    upsert('node', dataset)
    if df is not None:
        try:
            client.collections.create(generate_schema_auto(dataset_id))
        except:
            client.collections[dataset_id].delete()
            client.collections.create(generate_schema_auto(dataset_id))
        jsonl = df.to_json(orient='records', lines=True) # Convert to jsonl
        r = client.collections[dataset_id].documents.import_(jsonl, {'action': 'create'})
    



def add_dataset(project_id, dataset_id):
    project = get_document('project', project_id)
    if dataset_id not in [d['id'] for d in project['node_list']]:
        project['node_list'].append({'id': dataset_id, 'position': {'x':0, 'y':0}})
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

        # Remove Action or Error (for debugging)
        if node['type'].startswith('action') or node['type'] == '':
            destination_node_id_list = [edge.split('_')[1] for edge in edge_list if edge.startswith(node_id)]

            project['node_list'] = [node for node in project['node_list'] if node['id'] != node_id]
            for edge in edge_list:
                if node_id in edge:
                    project['edge_list'].remove(edge)
                if node_id == edge.split('_')[0]:
                    project['node_list'] = [d for d in project['node_list'] if d['id'] != edge.split('_')[1]]
                if any(edge.startswith(destination_node_id) for destination_node_id in destination_node_id_list):
                    return
   
        # Remove Raw Dataset
        elif node['type'].startswith('raw'):
            dataset = get_document('node', node_id)
            if dataset['type'].startswith('raw'):
                if any(edge.startswith(node_id) for edge in edge_list):
                    pass
                else:
                    project['node_list'] = [d for d in project['node_list'] if d['id'] != node_id]
                    for edge in [edge for edge in edge_list if edge.startswith(node_id)]:
                        project['edge_list'].remove(edge)
        else:
            print('[Error] Unable to delete Node: ', node_id)
    
    upsert('project', project)
    


def action(project_id, dataset_id_source, action, dataset_metadata, df_new_dataset):
    # New id
    action_id = str(uuid.uuid1())
    dataset_id = str(uuid.uuid1())
    edge1 = dataset_id_source + '_' + action_id
    edge2 = action_id + '_' + dataset_id

    # Project Document
    project = get_document('project', project_id)
    project['node_list'].append({'id': action_id, 'position': {'x':0, 'y':0}})
    project['node_list'].append({'id': dataset_id, 'position': {'x':0, 'y':0}})
    project['edge_list'].append(edge1)
    project['edge_list'].append(edge2)

    # Action Document
    details = diff(get_document('node', dataset_id_source), dataset_metadata, syntax='symmetric', marshal=True)
    action_metadata = Node(id=action_id, name='', description='', documentation='', type=action, details=details)

    # Dataset Document
    dataset_metadata['id'] =  dataset_id # Overwrite previous dataset ID
    dataset_metadata['type'] = 'processed'
    dataset_metadata['details'] = None
    dataset_metadata['name'] = 'New Dataset'

    # Dataset Data Collection
    jsonl = df_new_dataset.to_json(orient='records', lines=True) # Convert to jsonl

    
    # Upload
    upsert('project', project)
    upsert('node', action_metadata)
    upsert('node', dataset_metadata)
    client.collections.create(generate_schema_auto(dataset_id))
    client.collections[dataset_id].documents.import_(jsonl, {'action': 'create'})


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
    dataset['name'] = 'New Dataset'
    
    # Upload
    upsert('project', project)
    upsert('node', action)
    upsert('node', dataset)
    client.collections.create(generate_schema_auto(dataset_id))
    client.collections[dataset_id].documents.import_(jsonl, {'action': 'create'})




def generate_cytoscape_elements(project_id):
    project = get_document('project', project_id)
    
    cNode_list = []
    for d in project['node_list']:
        position = {'x': d['position']['x'], 'y': d['position']['y']}
        node = get_document('node', d['id'])
    
        if node['type'].startswith('raw'): className = 'raw'
        elif node['type'].startswith('processed'): className = 'processed'
        else: className = 'action'

        action_label = get_action_label(node['type'])

        cNode_list.append(cNode(node['id'], name=node['name'], type=node['type'], className=className, action_label=action_label, position=position))

    cEdge_list = [cEdge(id.split('_')[0], id.split('_')[1]) for id in project['edge_list']]
    return cNode_list + cEdge_list


def get_action_label(node_type):
    if node_type == 'action_1': action_label = 'Clone Metadata'
    elif node_type == 'action_2': action_label = 'Truncate Dataset'
    elif node_type == 'action_3': action_label = 'Merge'
    elif node_type == 'action_4': action_label = 'action_4'
    elif node_type == 'action_5': action_label = 'action_5'
    elif node_type == 'action_6': action_label = 'action_6'
    elif node_type == 'action_7': action_label = 'action_7'
    else: action_label = 'Error'
    return action_label