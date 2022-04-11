
# Uploader
UPLOAD_FOLDER_ROOT = r"C:\tmp\Uploads"

# Navigation
SIDEBAR_2_LIST = [
    {'label': 'Modify Metadata',            'value': '#',                       'multiple':False,   'disabled': True,  'className': 'fas fa-search-plus'},
    {'label': 'Impute Data',                'value': '/apps/impute_data',       'multiple':False,   'disabled': False,   'className': 'fas fa-search-plus'},
    {'label': 'Extract & Transform',        'value': '/apps/transform_node', 'multiple':False,   'disabled': False,   'className': 'fas fa-search-plus'},
    
    {'label': 'Merge Datasets',             'value': '#',                       'multiple':True,    'disabled': False,  'className': 'fas fa-search-plus'},

    # {'label': 'Join',               'value': '/apps/join',               'multiple':True,   'className': 'fas fa-search-plus'},
    # {'label': 'Modify Profile',             'value': '/apps/profile',           'multiple':False,   'disabled': False,  'className': 'fas fa-chess-knight'},
    
]
SIDEBAR_3_LIST = [
    {'label': 'Merge Strategy',     'value': '/apps/merge_strategy',     'multiple':True,  'className': 'fas fa-chess-knight'},
    {'label': 'Temporal Evolution', 'value': '/apps/temporal_evolution', 'multiple':False, 'className': 'fas fa-clock'},
]






# Datatypes
DATATYPE_LIST = ['string', 'numerical', 'bool', 'datetime', 'geopoint', 'Float64']
DATATYPE_NUMERICAL = ['Int64', 'Float64']
DATATYPE_NONNUMERICAL = ['string', 'bool', 'datetime64', 'geopoint']


# Types of Merges
MERGE_TYPES = ['arrayMergeByIndex', 'arrayMergeById', 'objectMerge'] # 'overwrite', 'version', 'append'







# Graph Options
options_graph = [
    {'label':'Line Graph', 'value':'line'},
    {'label':'Bar Plot', 'value':'bar'},
    {'label':'Pie Plot', 'value':'pie'},
    {'label':'Scatter Plot', 'value':'scatter'},
    # {'label':'Box Plot', 'value':'box'},
]


# Names of all Groupby Aggregate functions
aggregate_button_name_list = ['Distinct', 'Min', 'Max', 'Avg', 'Median', 'Sum', 'Concat', 'Std Dev']



# Datatable Default Name of Index Column
index_col_name = 'no.'