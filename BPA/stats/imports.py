import imp

base_dir = '/home/nonroot/Projects/swc-api/'

imp.load_source('config', base_dir + 'config.py')
imp.load_source('swc_regex_config', base_dir + 'swc_regex_config.py')
imp.load_source('swc_helpers', base_dir + 'swc_helpers.py')
imp.load_source('swc_parse', base_dir + 'swc_parse.py')
imp.load_source('swc_db', base_dir + 'swc_db.py')

db = imp.load_source('swc_django', base_dir + 'swc_django.py')
