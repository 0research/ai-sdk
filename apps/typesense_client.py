import typesense
import os
import socket
import ast

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
    client = typesense_client('localhost', '8108', 'http', 'Hu52dwsas2AdxdE') 
  else:
    client = typesense_client('oswmql6f04pndbi1p-1.a1.typesense.net', '443', 'https', os.environ['TYPESENSE_API_KEY']) # Typesense Cloud

  try:
    client.collections.create(generate_schema_auto('dataset'))
    client.collections.create(generate_schema_auto('node'))
    print('Created Dataset and Node Collections')
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


def upsert(collection_id, document):
  document = {k:str(v) for k, v in document.items()}
  client.collections[collection_id].documents.upsert(document)

