from dotenv import find_dotenv, load_dotenv
from os import environ as env
import os

# Session
session_id = 'session1'


# Auth0
ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)
    AUTH0_SECRET_KEY = env.get("APP_SECRET_KEY")
    AUTH0_CLIENT_ID = env.get("AUTH0_CLIENT_ID")
    AUTH0_CLIENT_SECRET = env.get("AUTH0_CLIENT_SECRET")
    AUTH0_DOMAIN = env.get("AUTH0_DOMAIN")
else:
    AUTH0_SECRET_KEY = os.environ['APP_SECRET_KEY']
    AUTH0_CLIENT_ID = os.environ['AUTH0_CLIENT_ID']
    AUTH0_CLIENT_SECRET = os.environ['AUTH0_CLIENT_SECRET']
    AUTH0_DOMAIN = os.environ['AUTH0_DOMAIN']


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
DATATYPE_LIST = ['string', 'int64', 'numerical', 'bool', 'datetime', 'geopoint', 'float64']
DATATYPE_NUMERICAL = ['int64', 'float64']
DATATYPE_NONNUMERICAL = ['string', 'bool', 'datetime', 'geopoint']


# Types of Merges
options_join = [
    {'label': 'Left Join', 'value': 'left'},
    {'label': 'Right Join', 'value': 'right'},
    {'label': 'Inner Join', 'value': 'inner'},
    {'label': 'Outer Join', 'value': 'outer'},
    # {'label': 'Cross Join', 'value': 'cross'},
]

# Types of Merges
options_merge = [
    {'label': 'Merge by Index', 'value': 'arrayMergeByIndex'},
    {'label': 'Object Merge', 'value': 'objectMerge'},
    {'label': 'Merge by Id', 'value': 'arrayMergeById'},
    # {'label': 'Overwrite', 'value': 'overwrite', 'disabled':True},
    # {'label': 'Version Merge', 'value': 'version', 'disabled':True},
    {'label': 'Append', 'value': 'append', 'disabled':True},
]


# List of Actions
option_actions = [
    {'label':'Join',        'value':'join'},
    # {'label':'Merge',       'value':'merge'},
    {'label':'Transform',   'value':'transform'},
    {'label':'Aggregate',   'value':'aggregate'},
    {'label':'Impute',      'value':'impute'},
]



# Graph Options
options_graph = [
    {'label':'Line Graph', 'value':'line'},
    {'label':'Bar Plot', 'value':'bar'},
    {'label':'Pie Plot', 'value':'pie'},
    {'label':'Scatter Plot', 'value':'scatter'},
    # {'label':'Box Plot', 'value':'box'},
]


# Names of all Groupby Aggregate functions
aggregate_button_name_list = [ 'min', 'max', 'sum', 'count']



# Datatable Default Name of Index Column
index_col_name = 'no.'



# List of Transform Functions
function_options = [
    {'label': 'Arithmetic', 'value':'arithmetic'},
    {'label': 'Comparison', 'value':'comparison'},
    {'label': 'Aggregate', 'value':'aggregate', 'disabled':True},
    {'label': 'Sliding Window', 'value':'slidingwindow', 'disabled':True},
    {'label': 'Format Date', 'value':'formatdate', 'disabled':True},
    {'label': 'Cumulative', 'value':'cumulative', 'disabled':True},
    {'label': 'Shift', 'value':'shift', 'disabled':True},
]

arithmetic_options = [
    {'label': '[+] Add', 'value':'add'},
    {'label': '[-] Subtract', 'value':'subtract'},
    {'label': '[/] Divide', 'value':'divide'},
    {'label': '[*] Multiply', 'value':'multiply'},
    {'label': '[**] Exponent', 'value':'exponent'},
    {'label': '[%] Modulus', 'value':'modulus'},
]

comparison_options = [
    {'label': '[>] Greater than', 'value':'gt'},
    {'label': '[<] Less than', 'value':'lt'},
    {'label': '[>=] Greater than or Equal to', 'value':'ge'},
    {'label': '[<=] Less than or Equal to', 'value':'le'},
    {'label': '[==] Equal to', 'value':'eq'},
    {'label': '[!=] Not equal to', 'value':'ne'},
]

aggregate_options = [
    {'label': 'Sum', 'value':'sum'},
    {'label': 'Average', 'value':'avg'},
    {'label': 'Minimum', 'value':'min'},
    {'label': 'Maximum', 'value':'max'},
]

slidingwindow_options = [
    {'label': 'Sum', 'value':'sum'},
    {'label': 'Average', 'value':'avg'},
    {'label': 'Minimum', 'value':'min'},
    {'label': 'Maximum', 'value':'max'},
]

dateformat_options = [
    {'label': 'DD-MM-YYYY', 'value':'YYYY-MM-DD'},
    {'label': 'MM-DD-YYYY', 'value':'YYYY-MM-DD'},
    {'label': 'YYYY-MM-DD', 'value':'YYYY-MM-DD'},
]



# Define path for images used
HOMEPAGELOGO = "../assets/static/polymath-ai-0research-logo.svg"
YOUTUBE = "../assets/static/youtube-icon.svg"
GITHUB = "../assets/static/github-icon.svg"
DOCKER = "../assets/static/docker-icon.svg"
GITHUBACTION = "../assets/static/githubaction-icon.svg"



# Datatypes
THRESHOLD = 0.8