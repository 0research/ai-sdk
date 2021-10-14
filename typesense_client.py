import typesense
import json
import os
import pprint

client = typesense.Client({
  'nodes': [{
    'host': 'localhost', # For Typesense Cloud use xxx.a1.typesense.net
    'port': '8108',      # For Typesense Cloud use 443
    'protocol': 'http'   # For Typesense Cloud use https
  }],
  'api_key': 'Hu52dwsas2AdxdE',
  'connection_timeout_seconds': 2
})


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