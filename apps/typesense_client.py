import typesense
import json
import os
import pprint


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

# Initialize Typesense
# client = typesense_client('localhost', '8108', 'http', 'Hu52dwsas2AdxdE') # Local
client = typesense_client('oswmql6f04pndbi1p-1.a1.typesense.net', '443', 'https', os.environ['TYPESENSE_API_KEY']) # Typesense Cloud


def generate_schema_auto(name):
    return {
        "name": name,  
        "fields": [{"name": ".*", "type": "auto" }]
    }

def get_documents(dataset_name, per_page):
    search_parameters = {
        'q': '*',
        'per_page': per_page,
    }
    result = client.collections[dataset_name].documents.search(search_parameters)
    return [d['document'] for d in result['hits']]


# collection_name = 'dataset'
# schema = {
#     "name": collection_name,  
#     "fields": [{"name": ".*", "type": "auto" }]
# }

# for collection in client.collections.retrieve():
#     if collection['name'] == collection_name:
#         client.collections[collection_name].delete()
# client.collections.create(schema)

# # Insert Data to Collection
# books_dir = "C:/0research/Project/ai-sdk/datasets/books.jsonl"
# size = os.path.getsize(books_dir)
# if size < 1000000:
#     print(size)
# else:
#     print('large')
# with open(books_dir) as infile:
#     for i, json_line in enumerate(infile):
#         book_document = json.loads(json_line)
#         client.collections[collection_name].documents.create(book_document)

#         if i > 100:
#             break