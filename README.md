# ai-sdk
AI-SDK is a nocode tool used for defining and refining the data data strategy by using current and new datasets by doing discovery, exploratory analysis, schema decisions to come to a consesnus of what is the best way to build a data product. This is super useful for Data Scientists, Data Engineers, Data Analysts and Database Administrators to all come on the same page on an ongoing basis while addressing the evolving data needs.

**AI-SDK's Data Strategy tool entails the following features**
- [x] (Experiments: Live Data Flow Diagram )
- [x] (Data profiling)
- [x] (Live Data Merging)
- [x] (Searching Data and Schema Management)
- [x] (Data Catalog)
- [x] (Data Exploration)
- [x] (Data Cleaning)
- [x] (Data Limitations & Transformations)
- [x] (Data Governance)
- [x] (AI Feature store)
- [x] (Temporal/Streaming Data Evolutions)

**AI-SDK is a data strategy tool which can we used in 3 Form Factors**
1. Method1: [Github Action](https://github.com/marketplace/actions/ai-sdk-action) along with [Github Flat Data](https://github.com/githubocto/flat) - 10 minutes to setup and see the value
2. Method2: [Cloud WebApp](http://app.0research.com) - Nocode solution to 
3. Method3: [Docker Self Hosted ](https://hub.docker.com/repository/docker/0research/ai-sdk)

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


<!-- Features to be implemented / to be implemented
- [x] (for checked checkbox)
- [ ] (for unchecked checkbox)
- [ ] (for unchecked checkbox)
- [ ] (for unchecked checkbox)
- [ ] (for unchecked checkbox)
- [ ] (for unchecked checkbox) -->