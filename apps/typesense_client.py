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

    collection_list = ['project', 'dataset', 'action', 'session1'] # TODO Currently all users will use same session. Replace when generate user/session ID
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
    dataset = get_document('dataset', dataset_id)
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
def Project(id, type, dataset, action, edge, experiment):
    return {
        'id': id, 
        'type': type, 
        'dataset_list': dataset,
        'action_list': action,
        'edge_list': edge,
        'experiment': experiment
    }
def Dataset(id, name, description, type, documentation, details, features, expectation, index, target, graphs):
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
def Action(id, action, description, changes):
    return {
        'id': id,
        'action': action,
        'description': description,
        'changes': changes
    }


# Cytoscape Object 
def cNode(id, name, type, action=None):
    return {
        'data': {'id': id, 'name': name, 'type': type, 'action': action},
        'classes': type,
    }
def cEdge(dataset_id_source, destination_id):
    return {
        'data': {
                'id': dataset_id_source + '_' + destination_id,
                'source': dataset_id_source,
                'target': destination_id,
            },
        'selectable': False,
        'classes': '',
    }


def new_project(project_id, project_type):
    document = Project(id=project_id, type=project_type, dataset=[], action=[], edge=[], experiment=[])
    create('project', document)

# def upload_dataset(project_id, dataset_id, dataset_data_store, description, documentation, 
#                     delimiter, remove_space, remove_header):
#     # Project
#     project_id = get_session('project_id')
#     project = get_document('project', project_id)
#     project['dataset_list'].append(dataset_id)

#     # Dataset
#     df = json_normalize(dataset_data_store)
#     jsonl = df.to_json(orient='records', lines=True) # Convert to jsonl

#     # Node
#     api_data = {
#         'delimiter': delimiter,
#         'remove_space': remove_space,
#         'remove_header': remove_header,
#     }

#     dataset = Dataset(
#             id=dataset_id,
#             description=description, 
#             api_data=api_data, 
#             features={col:str(datatype) for col, datatype in zip(df.columns, df.convert_dtypes().dtypes)},
#             expectation = {col:None for col in df.columns}, 
#             index = [], 
#             target = []
#     )

#     # Upload to Typesense
#     upsert('project', project)
#     upsert('dataset', dataset)
#     client.collections.create(generate_schema_auto(dataset_id))
#     client.collections[dataset_id].documents.import_(jsonl, {'action': 'create'})

def new_data_source():
    dataset_id = str(uuid.uuid1())
    dataset = Dataset(
            id=dataset_id,
            name='New Data Source',
            description='', 
            documentation='',
            type='raw',
            details='', 
            features={},
            expectation = {}, 
            index = [], 
            target = [],
            graphs = [],
    )
    upsert('dataset', dataset)
    return dataset_id

def save_dataset_config(dataset_id, df, name, description, documentation, type, details):
    # Dataset
    dataset = Dataset(
            id=dataset_id,
            name=name,
            description=description, 
            documentation=documentation,
            type=type,
            details=details, 
            features={str(col):str(datatype) for col, datatype in zip(df.columns, df.convert_dtypes().dtypes)},
            expectation = {col:None for col in df.columns}, 
            index = [], 
            target = [],
            graphs = [],
    )
    
    # Upload to Typesense
    upsert('dataset', dataset)
    try:
        client.collections.create(generate_schema_auto(dataset_id))
    except:
        client.collections[dataset_id].delete()
        client.collections.create(generate_schema_auto(dataset_id))
    jsonl = df.to_json(orient='records', lines=True) # Convert to jsonl
    r = client.collections[dataset_id].documents.import_(jsonl, {'action': 'create'})
    pprint(r)
    pprint(dataset)
    



def add_dataset(project_id, dataset_id):
    project = get_document('project', project_id)
    # project['dataset_list'].append(dataset_id)
    # upsert('project', project)
    if dataset_id not in project['dataset_list']:
        project['dataset_list'].append(dataset_id)
        # Upload to Typesense
        upsert('project', project)
        return True
    else:
        return False


def remove(project_id, node_id_list):
    project = get_document('project', project_id)
    edge_list = project['edge_list'].copy()

    for node_id in node_id_list:
        # Remove Action
        if node_id in project['action_list']:
            destination_node_id_list = [edge.split('_')[1] for edge in edge_list if edge.startswith(node_id)]
            project['action_list'].remove(node_id)
            for edge in edge_list:
                if node_id in edge:
                    project['edge_list'].remove(edge)
                if node_id == edge.split('_')[0]:
                    project['dataset_list'].remove(edge.split('_')[1])
                if any(edge.startswith(destination_node_id) for destination_node_id in destination_node_id_list):
                    return

            
        # Remove Raw Dataset
        elif node_id in project['dataset_list']:
            dataset = get_document('dataset', node_id)
            if dataset['type'].startswith('raw'):
                if any(edge.startswith(node_id) for edge in edge_list):
                    pass
                else:
                    project['dataset_list'].remove(node_id)
                    for edge in [edge for edge in edge_list if edge.startswith(node_id)]:
                        project['edge_list'].remove(edge)
                    
        
        else:
            print('[Error] Unable to delete Node: ', node_id)
    
    upsert('project', project)
    


def action(project_id, dataset_id_source, action, description, new_dataset, changed_feature_dict):
    # New id
    action_id = str(uuid.uuid1())
    dataset_id = str(uuid.uuid1())
    edge1 = dataset_id_source + '_' + action_id
    edge2 = action_id + '_' + dataset_id

    # Project Document
    project = get_document('project', project_id)
    project['action_list'].append(action_id)
    project['dataset_list'].append(dataset_id)
    project['edge_list'].append(edge1)
    project['edge_list'].append(edge2)

    # Action Document
    changes = diff(get_document('dataset', dataset_id_source), new_dataset, syntax='symmetric', marshal=True)
    action = Action(id=action_id, action=action, description=description, changes=changes)

    # Dataset Document
    new_dataset['id'] =  dataset_id # Overwrite previous dataset ID
    new_dataset['type'] = 'processed'
    new_dataset['details'] = None
    new_dataset['name'] = 'New Dataset'

    # Dataset Data Collection
    dataset_data_store = search_documents(dataset_id_source, 250)
    df = json_normalize(dataset_data_store)
    df = df.rename(columns=changed_feature_dict)
    jsonl = df.to_json(orient='records', lines=True) # Convert to jsonl

    
    # Upload
    upsert('project', project)
    upsert('action', action)
    upsert('dataset', new_dataset)
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


def merge(project_id, dataset_id_source_list, description, dataset_data_store, dataset, changes):
    # New id
    action_id = str(uuid.uuid1())
    dataset_id = str(uuid.uuid1())

    # Project Document
    project = get_document('project', project_id)
    project['action_list'].append(action_id)
    project['dataset_list'].append(dataset_id)
    for dataset_id_source in dataset_id_source_list:
        edge_id = dataset_id_source + '_' + action_id
        project['edge_list'].append(edge_id)
    project['edge_list'].append(action_id + '_' + dataset_id)

    # Dataset Data Collection
    df = json_normalize(dataset_data_store)
    jsonl = df.to_json(orient='records', lines=True) # Convert to jsonl

    # Action Document
    action = Action(action_id, 'merge', description, changes)

    # Dataset Document
    dataset['id'] =  dataset_id # Overwrite previous dataset ID
    dataset['type'] = 'processed'
    dataset['details'] = None
    dataset['name'] = 'New Dataset'
    
    # Upload
    upsert('project', project)
    upsert('action', action)
    upsert('dataset', dataset)
    client.collections.create(generate_schema_auto(dataset_id))
    client.collections[dataset_id].documents.import_(jsonl, {'action': 'create'})




def generate_cytoscape_elements(project_id):
    project = get_document('project', project_id)

    action_list = [get_document('action', id) for id in project['action_list']]
    dataset_list = [get_document('dataset', id) for id in project['dataset_list']]

    cAction_list = [cNode(action['id'], name='', type='action', action=action['action']) for action in action_list]
    cDataset_list = ([cNode(dataset['id'], name=dataset['name'], type=dataset['type']) for dataset in dataset_list])
    cEdge_list = [cEdge(id.split('_')[0], id.split('_')[1]) for id in project['edge_list']]

    return cAction_list + cDataset_list + cEdge_list