import os
import json
# from apps.util import json_merge
from flatten_json import flatten
from jsonmerge import Merger
from jsondiff import diff


def json_merge(base, new, merge_strategy):
    schema = {'mergeStrategy': merge_strategy}
    merger = Merger(schema)
    base = merger.merge(base, new)
    return base


def main():
    merge_strategy = os.environ["INPUT_MERGE_STRATEGY"]
    
    with open('json1.json') as f:
        json1 = json.load(f)
    with open('json2.json') as f:
        json2 = json.load(f)
      
    base = None
    json1 = flatten(json1)
    json2 = flatten(json2)
    base = json_merge(base, json1, merge_strategy)
    base = json_merge(base, json2, merge_strategy)
    
    # Output to workflow variable (TODO remove when able to use github commit)
    print(f"::set-output name=merge_strategy::{merge_strategy}")
    print(f"::set-output name=merged_json::{base}")

    # Difference_history & Number of changes per key
    # difference_history = generate_difference_history(json_history_1, json_history_2)
    # num_changes = generate_number_changes(difference_history)
    
    # Write File
    with open('merged_json.json', 'w', encoding='utf-8') as f:
        json.dump(base, f, ensure_ascii=False, indent=4)
                  
    # TODO Github Commit File
    

if __name__ == "__main__":
    main()
