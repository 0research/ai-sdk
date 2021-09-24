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
    difference = diff(json1, json2, syntax='symmetric', marshal=True)
    
    # Write Files
    with open('merged_json.json', 'w', encoding='utf-8') as f:
        json.dump(base, f, ensure_ascii=False, indent=4)
    with open('difference.json', 'w', encoding='utf-8') as f:
        json.dump(difference, f, ensure_ascii=False, indent=4)
    
    # Push to Git (Set Config, Reset staged files from flat-data, commit, push, add previously staged files)
    repo = Repo('.')
    username = "ai-sdk"
    repo.config_writer().set_value("user", "name", username).release()
    repo.config_writer().set_value("user", "email", username+"@users.noreply.github.com").release()
    repo.git.reset()
    repo.index.add(['merged_json.json', 'difference.json'])
    repo.index.commit('ai-sdk: Upload & Process data')
    origin = repo.remote('origin')
    origin.push()
    repo.index.add(['json1.json', 'json2.json'])

if __name__ == "__main__":
    main()