import os
import json
# from apps.util import json_merge
from flatten_json import flatten
from jsonmerge import Merger
from jsondiff import diff

def read_json_folder(directory):
    json_list = []
    for name in os.listdir(directory):
        with open(directory+name) as f:
            data = json.load(f)
            json_list.append(data)
    return json_list

def json_merge(base, new, merge_strategy):
    schema = {'mergeStrategy': merge_strategy}
    merger = Merger(schema)
    base = merger.merge(base, new)
    return base

def merge(json1_list, merge_strategy):
    base, base_history = None, []
    for json in json1_list:
        new = flatten(json)
        base = json_merge(base, new, merge_strategy)
        base_history.append(base)
    return base_history

def main():
    merge_strategy = os.environ["INPUT_MERGE_STRATEGY"]
    directory_1 = os.environ["INPUT_JSON1"]
    directory_2 = os.environ["INPUT_JSON2"]
    
    print('start')
    print(merge_strategy)
    print(directory_1)
    print(directory_2)
    
    # Read json files & Merge
    json1_list = read_json_folder(directory_1)
    json2_list = read_json_folder(directory_2)
    merged_json_1 = merge(json1_list, merge_strategy)
    merged_json_2 = merge(json2_list, merge_strategy)
    
    # Output to workflow variable
    print(f"::set-output name=merge_strategy::{merge_strategy}")
    print(f"::set-output name=merged_json_1::{merged_json_1}")
    print(f"::set-output name=merged_json_2::{merged_json_2}")

    # Difference_history & Number of changes per key
    # difference_history = generate_difference_history(json_history_1, json_history_2)
    # num_changes = generate_number_changes(difference_history)
    

if __name__ == "__main__":
    main()
