# ai-sdk
AI-SDK is a nocode tool used for doing datasets discovery, exploratory, schema decisions and preparing a data strategy ready for Data Scientists.


# ai-sdk Action
AI-SDK Action allows users to 
* Periodically Fetch JSON data from two sources through [Flat Data](https://github.com/githubocto/flat)
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

# MIT License
At [0Research](https://0research.com), we offer our flagship open-source software through the MIT license. Why? It’s simple: we want to provide developers with the intellectual freedom to share their contributions in whatever manner they see fit. If they work hard on a AI-SDK project, they should be able to freely share their insight without any worry of legal repercussions.

MIT (Massachusetts Institute of Technology) License is a “permissive” license like BSD (Berkeley Software Distribution) and Apache licenses. These licenses are less restrictive when it comes to the release of source code. 

If a developer writes a million lines of code for a project and then incorporates even a few lines of GPL-licensed code, then all the code must be revealed under the GPL. The developer can’t mix their own proprietary software and GPL software together. This is precisely why the GPL has drawn the ire of many professional developers. **(This does not hold true for MIT License)**

Needless to say, we don’t think there’s anything scary about AI-SDK. When developer’s use AI-SDK and its permissive MIT license, they can put it on the internet without sharing app source code with anyone and not worry about a thing. 