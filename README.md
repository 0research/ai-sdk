# ai-sdk
AI-SDK is a nocode tool used for doing datasets discovery, exploratory, schema decisions and preparing a data strategy ready for Data Scientists.


# ai-sdk Action
AI-SDK Action allows users to 
* Periodically Fetch JSON data from two sources
* Merge both JSON data via Merging Strategies 


# Usage
* Under ```on```. Users are required to configure code to their specific needs.
* Under ```jobs```, the fields that can be modified are:
  * Both ```http_url``` to your desired HTTP GET API. These files will be pushed to your github repo.
  * ```merge_strategy``` with options (overwrite, objectMerge, version)

```python
on:
  workflow_dispatch: {}
  push:
    branches:
        - main
        - development
  schedule:
    - cron: "*/5 * * * *"
jobs:
  ai-sdk:
    runs-on: ubuntu-latest
    steps:
      - name: Setup deno
        uses: denoland/setup-deno@main
        with:
          deno-version: v1.x
      - name: Check out repo
        uses: actions/checkout@v2
      - name: Fetch data 1
        uses: githubocto/flat@v3
        with:
          http_url: https://api.coindesk.com/v2/bpi/currentprice.json
          downloaded_filename: json1.json
      - name: Fetch data 2
        uses: githubocto/flat@v3
        with:
          http_url: https://free.currconv.com/api/v7/convert?q=USD_PHP&compact=ultra&apiKey=4709550d97d6056b11e5
          downloaded_filename: json2.json
      - name: Merge Data
        id: mergeData
        uses: 0research/ai-sdk@main
        with:
          merge_strategy: objectMerge   
```


# Feedback
* We would love to receive feedback on the action from users to understand how we can improve.

