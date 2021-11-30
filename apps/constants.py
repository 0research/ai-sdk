


# Navigation
SIDEBAR_2_LIST = [
    {'label': 'Upload Dataset',     'value': '/apps/upload_dataset',     'multiple':None,  'className': 'fas fa-upload'},
    {'label': 'Profile',            'value': '/apps/profile',            'multiple':False, 'className': 'fas fa-chess-knight'},
    {'label': 'Impute Data',        'value': '/apps/impute_data',        'multiple':False, 'className': 'fas fa-search-plus'},
    {'label': 'Extract & Transform','value': '/apps/extract_transform',                'multiple':False,   'className': 'fas fa-search-plus'},
    {'label': 'Join',               'value': '/apps/join',               'multiple':True,   'className': 'fas fa-search-plus'},
]
SIDEBAR_3_LIST = [
    {'label': 'Merge Strategy',     'value': '/apps/merge_strategy',     'multiple':True,  'className': 'fas fa-chess-knight'},
    {'label': 'Temporal Evolution', 'value': '/apps/temporal_evolution', 'multiple':False, 'className': 'fas fa-clock'},
]






# Datatypes
DATATYPE_LIST = ['object', 'Int64', 'float64', 'bool', 'datetime64', 'category']







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