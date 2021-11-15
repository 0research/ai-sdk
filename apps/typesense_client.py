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
        # client = typesense_client('oswmql6f04pndbi1p-1.a1.typesense.net', '443', 'https', os.environ['TYPESENSE_API_KEY']) # Typesense Cloud
        client = typesense_client('localhost', '8108', 'http', 'Hu52dwsas2AdxdE') 
    else:
        client = typesense_client('oswmql6f04pndbi1p-1.a1.typesense.net', '443', 'https', os.environ['TYPESENSE_API_KEY']) # Typesense Cloud

    collection_list = ['project', 'dataset', 'action', 'session1'] # TODO Currently all users will use same session. Replace when generate user/session ID
    for name in collection_list:
        try:
            client.collections.create(generate_schema_auto(name))
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

def search_documents(collection_id, per_page):
    search_parameters = {
        'q': '*',
        'per_page': per_page,
    }
    result = client.collections[collection_id].documents.search(search_parameters)
    return [d['document'] for d in result['hits']]
def get_dataset_data(dataset_id):
    dataset = get_document('dataset', dataset_id)
    column = dataset['column']
    data = search_documents(dataset_id, '250')
    df = json_normalize(data)

    return df[column]


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
def Dataset(id, description, api_data, column, datatype, expectation, index, target):
    return {
        'id': id,
        'description': description,
        'api_data': api_data, # None or {source, delimiter, remove_space, remove_header}
        'column': column,
        'datatype': datatype,
        'expectation': expectation,
        'index': index, 
        'target': target,
    }
def Action(id, action, description, action_details):
    return {
        'id': id,
        'action': action,
        'description': description,
        'action_details': action_details
    }


# Cytoscape Object 
def cNode(id, node_type, action=None):
    return {
        'data': {'id': id, 'type': node_type, 'action': action},
        'classes': node_type,
    }
def cEdge(source_id, destination_id):
    return {
        'data': {
                'id': source_id + '_' + destination_id,
                'source': source_id,
                'target': destination_id,
            },
            'selectable': False
    }


def new_project(project_id, project_type):
    document = Project(id=project_id, type=project_type, dataset=[], action=[], edge=[], experiment=[])
    create('project', document)

def upload_dataset(project_id, dataset_id, dataset_data, description, source, 
                    delimiter, remove_space, remove_header):
    # Project
    project_id = get_session('project_id')
    project = get_document('project', project_id)
    project['dataset_list'].append(dataset_id)

    # Dataset
    df = json_normalize(dataset_data)
    jsonl = df.to_json(orient='records', lines=True) # Convert to jsonl

    # Node
    api_data = {
        'source': source, 
        'delimiter': delimiter,
        'remove_space': remove_space,
        'remove_header': remove_header,
    }

    dataset = Dataset(
            id=dataset_id,
            description=description, 
            api_data=api_data, 
            column={col:True for col in df.columns}, 
            datatype={col:str(datatype) for col, datatype in zip(df.columns, df.convert_dtypes().dtypes)},
            expectation = {col:None for col in df.columns}, 
            index = [], 
            target = []
    )

    # Upload to Typesense
    upsert('project', project)
    upsert('dataset', dataset)
    client.collections.create(generate_schema_auto(dataset_id))
    client.collections[dataset_id].documents.import_(jsonl, {'action': 'create'})
    

def delete(project_id, node_id):
    project = get_document('project', project_id)
    edge_source_list = [edge.split('_')[0] for edge in project['edge_list']]

    # TODO delete action = deletes multiple nodes
    if node_id in project['action_list']:
        print('TODO delete action')
    elif node_id in project['dataset_list']:
        if node_id in edge_source_list:
            print('[Error] Node selected is not a leaf node.')
        else:
            print('TODO delete')
            # project['dataset_list'].remove(node_id)
            # for edge in project['edge_list']:
            #     if edge.split('_')[1] == node_id:
            #         project['edge_list'].remove(node_id)
            upsert('project', project)

def action(project_id, source_id, action, description, action_details, changed_dataset, dataset_data):
    # New id
    action_id = str(uuid.uuid1())
    dataset_id = str(uuid.uuid1())
    edge1 = source_id + '_' + action_id
    edge2 = action_id + '_' + dataset_id

    # Project Document
    project = get_document('project', project_id)
    project['action_list'].append(action_id)
    project['dataset_list'].append(dataset_id)
    project['edge_list'].append(edge1)
    project['edge_list'].append(edge2)

    # Action Document
    action = Action(id=action_id, action=action, description=description, action_details=action_details)
    changed_dataset['id'] =  dataset_id # Overwrite previous dataset ID

    # Dataset Data Collection
    df = json_normalize(dataset_data)
    jsonl = df.to_json(orient='records', lines=True) # Convert to jsonl
    
    # Upload
    upsert('project', project)
    upsert('action', action)
    upsert('dataset', changed_dataset)
    client.collections.create(generate_schema_auto(dataset_id))
    client.collections[dataset_id].documents.import_(jsonl, {'action': 'create'})



def join(project_id, source_id_list, description, dataset_data, action_details):
    # New id
    action_id = str(uuid.uuid1())
    dataset_id = str(uuid.uuid1())

    # Project Document
    project = get_document('project', project_id)
    project['action_list'].append(action_id)
    project['dataset_list'].append(dataset_id)
    for source_id in source_id_list:
        edge_id = source_id + '_' + action_id
        project['edge_list'].append(edge_id)
    project['edge_list'].append(action_id + '_' + dataset_id)

    for source_id in source_id_list:
        source_data = get_dataset_data(source_id)

        # Dataset Data Collection
        df = json_normalize(dataset_data)
        jsonl = df.to_json(orient='records', lines=True) # Convert to jsonl

        # Action Document
        action = Action(action_id, 'join', description, action_details)
        dataset = Dataset(
                id=dataset_id,
                description=description, 
                api_data=None, 
                column=list(df.columns), 
                datatype = [],
                expectation = [],
                index = [], 
                target = []
        )
    
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

    cAction_list = [cNode(action['id'], node_type='action', action=action['action']) for action in action_list]
    cDataset_list = [cNode(dataset['id'], node_type='dataset') for dataset in dataset_list]
    cEdge_list = [cEdge(id.split('_')[0], id.split('_')[1]) for id in project['edge_list']]


    return cAction_list + cDataset_list + cEdge_list