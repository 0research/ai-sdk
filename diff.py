import os
import json
# from apps.util import json_merge
from flatten_json import flatten
from jsonmerge import Merger
from jsondiff import diff
from git import Repo

def json_merge(base, new, merge_strategy):
    schema = {'mergeStrategy': merge_strategy}
    merger = Merger(schema)
    base = merger.merge(base, new)
    return base


def main():
    # Read Inputs
    merge_strategy = str(os.environ["INPUT_MERGE_STRATEGY"])
    branch = str(os.environ["GITHUB_REF"])

    # Print
    print("Merge Strategy: ", merge_strategy)
    print("Branch: ", branch)
    
    # Read Files
    with open('json1.json') as f:
        json1 = json.load(f)
    with open('json2.json') as f:
        json2 = json.load(f)
    
    # Flatten, Merge, Difference & Number of changes per key
    base = None
    json1 = flatten(json1)
    json2 = flatten(json2)
    base = json_merge(base, json1, merge_strategy)
    base = json_merge(base, json2, merge_strategy)
    # difference_history = generate_difference_history(json_history_1, json_history_2)
    # num_changes = generate_number_changes(difference_history)
    
    # Write Files
    with open('merged_json.json', 'w', encoding='utf-8') as f:
        json.dump(base, f, ensure_ascii=False, indent=4)
    
    # Push to Git
    repo = Repo('.')
    repo.git.reset()
    repo.index.add(['merged_json.json'])
    repo.index.commit('Upload Merged Json')
    origin = repo.remote('origin')
    origin.push()
    repo.index.add(['json1.json', 'json2.json'])

if __name__ == "__main__":
    main()