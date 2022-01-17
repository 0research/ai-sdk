
# Uploader
UPLOAD_FOLDER_ROOT = r"C:\tmp\Uploads"

# Navigation
SIDEBAR_2_LIST = [
    {'label': 'Modify Metadata',            'value': '#',                       'multiple':False,   'disabled': True,  'className': 'fas fa-search-plus'},
    {'label': 'Impute Data',                'value': '/apps/impute_data',       'multiple':False,   'disabled': False,   'className': 'fas fa-search-plus'},
    {'label': 'Extract & Transform',        'value': '/apps/extract_transform', 'multiple':False,   'disabled': False,   'className': 'fas fa-search-plus'},
    
    {'label': 'Merge Datasets',             'value': '#',                       'multiple':True,    'disabled': False,  'className': 'fas fa-search-plus'},

    # {'label': 'Join',               'value': '/apps/join',               'multiple':True,   'className': 'fas fa-search-plus'},
    # {'label': 'Modify Profile',             'value': '/apps/profile',           'multiple':False,   'disabled': False,  'className': 'fas fa-chess-knight'},
    
]
SIDEBAR_3_LIST = [
    {'label': 'Merge Strategy',     'value': '/apps/merge_strategy',     'multiple':True,  'className': 'fas fa-chess-knight'},
    {'label': 'Temporal Evolution', 'value': '/apps/temporal_evolution', 'multiple':False, 'className': 'fas fa-clock'},
]






# Datatypes
DATATYPE_LIST = ['object', 'Int64', 'float64', 'bool', 'datetime64', 'geopoint']




# Types of Merges
MERGE_TYPES = ['arrayMergeByIndex', 'arrayMergeById', 'objectMerge'] # 'overwrite', 'version', 'append'



# Datatable
style_data_conditional = [
    {
        "if": {"state": "active"},
        "backgroundColor": "rgba(150, 180, 225, 0.2)",
        "border": "1px solid blue",
    },
    {
        "if": {"state": "selected"},
        "backgroundColor": "rgba(0, 116, 217, .03)",
        "border": "1px solid blue",
    },
]



