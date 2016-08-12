
# coding: utf-8

# 

# In[ ]:

#Step 1: Created subset of the metro extract of Dublin city using a version of the extract code provided as part of project intoductions.
#Sample file is ~26 KB.


import xml.etree.ElementTree as ET  # Use cElementTree or lxml if too slow

OSM_FILE = "C:\Users\Donal\Downloads\dublin_ireland"  # Replace this with your osm file
SAMPLE_FILE = "C:\Users\Donal\Downloads\dublin_sample.osm"

k = 10 # Parameter: take every k-th top level element

def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag

    Reference:
    http://stackoverflow.com/questions/3095434/inserting-newlines-in-xml-file-generated-via-xml-etree-elementtree-in-python
    """
    context = iter(ET.iterparse(osm_file, events=('start', 'end')))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


with open(SAMPLE_FILE, 'wb') as output:
    output.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    output.write('<osm>\n  ')

    # Write every kth top level element
    for i, element in enumerate(get_element(OSM_FILE)):
        if i % k == 0:
            output.write(ET.tostring(element, encoding='utf-8'))

    output.write('</osm>')


# In[21]:

#Creating a dictionary of all tags in dublin ireland OSM file to find most common tag types and potential issues with tag naming.

import xml.etree.ElementTree as ET
import pprint
import csv

filename = 'C:\\Users\\Donal\\Downloads\\dublin_ireland' #osm file being parsed
filepath = 'C:\\Users\\Donal\\Downloads\\tag_list.csv' # csv output of parsing

#For element, check if tag name already listed and add if not. For tag names aleady listed, update count by one.
def tag_lister(element, tag_types):
    if element.tag == "tag":
        tag_key = element.attrib['k']
        if tag_key not in tag_types:
            tag_types[tag_key] = 1
        else:
            tag_types[tag_key] += 1
    return tag_types

#cycle trhough second level of xml elements and update tag_types dict with tag and number o instances 
def tag_list(filename):
    tag_types = {}
    for _, element in ET.iterparse(filename):
        tag_types = tag_lister(element, tag_types)
    return tag_types

#write dictionary as CSV file to local drive specified in filepath. So this code does not have to be run again.
#This could be optimized by writing to the csv for each element but it was only ever used once.
def csv_dictwriter(csv_dict, filepath):
    with open(filepath, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['tag','count'])
        writer.writeheader()
        for e in csv_dict:
            writer.writerow({'tag':e, 'count':csv_dict[e]})



csv_dictwriter(tag_list(filename), filepath)


# Looking throught the listed tags, there are several groups of similar tags taht interest me:
# 
# Some address tags contain a seperate ga, presumably to store the Gaelic version of the street name:
# addr:street: 84535,
# addr:street:ga: 30,
# 
# There is also a similar problem for addr:city but this as less of a problem as I am focusing on Dublin only so it sould always be Bhaile Athá Cliath [Dubh Linn]
# 'addr:city': 15557,
# 'addr:city:ga': 28,
# 
# http://wiki.openstreetmap.org/wiki/Multilingual_names#Ireland_.28Republic.29
# 
# There is an even longer list of languages (?) for the name attribute:
# A lot of these letter correspond to languages under the ISO 639.2 but the
#  'name': 47554,
#  'name:absent': 4,
#  'name:ace': 1,
#  'name:ady': 1,
#  'name:af': 2,
#  ...
# Curious to know what 'name:griffithsvaluation' and 'name:absent' could be.
#  
# There are also name tags that are confusing or redundant and could be updated to name:en or name:ga. May have to move the origional name to alt_name. Will need to figure out a way to be consistant with this.
#  
#  'official_name': 15,
#  'official_name:en': 93,
#  'official_name:eo': 1,
#  'official_name:ga': 97,
#  'official_name:la': 1,
#  'official_name:pt': 1,
#  'old_name': 158,
#  'old_name2': 1,
#  'old_name:en': 1,
#  'old_name:ga': 1,
#  'old_name:ku': 1,
#  'old_name:vi': 1,
#  'old_name_1': 1,
#  'old_name_2': 1

# In[61]:

#Creating a dictionary of all tags in dublin ireland OSM file to find most common tag types and potential issues with tag naming.

import xml.etree.ElementTree as ET
import pprint
import re

filename = 'C:\Users\Donal\Downloads\dublin_ireland'

lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

tag_values = {'FIXME':[],'amenity':[],'addr:street':[],'addr:city':[],'addr:city:ga':[], 'name:ga':[],'building:use':[],'type':[],                  'service':[],'year_built':[]}

def tag_value_finder(element, tag_values):
    if element.tag == "tag":
        tag_key = element.attrib['k']
        tag_value = element.attrib['v']
        if tag_key in tag_values:
            tag_values[tag_key].append(tag_value)
    return tag_values

def tag_value_lister(filename,tag_values):
    for n, element in ET.iterparse(filename):
        tag_values = tag_value_finder(element, tag_values)
    return tag_values

tag_value_list = tag_value_lister(filename,tag_values)


# In[63]:

#issue 1: city address 
import codecs

dublin_re = re.compile(r'Dublin ?[0-9]?[0-9W]?$')
not_dublin = ['Celbridge','Lucan','Leixlip','Malahide','Bray','Portmarnock','Kilternan','Dunshaughlin','Donabate','Batterstown','Baldonnel']

in_dublin = {'Dublin':['Killiney','Blackrock','Harristown','Swords','Stillorgan','Dún Laoghaire','Monkstown','Mount Merrion','Cornelscourt'],    'Dublin 15':['Ongar','Blanchardstown'], 'Dublin 18': ['Cabinteely'],    'Dublin 14': ['Rathfarnham','Churchtown'], 'Dublin 4':['Donnybrook'],    'Dublin 24':['Tallaght'],'Dublin 22': ['Clondalkin'],'Dublin 3': ['Clontarf'] }
    
def city_converter(value):
    #value = str(value_unicode)  -fails when converting ú in Dún Laoghaire
    match = False
    if re.search(dublin_re,value):
        match = True
        return value
    elif value in not_dublin:
        match = True
        return value
    else:
        for d in in_dublin:
            for address in in_dublin[d]:
                if value == unicode(address, 'utf-8'):
                    match = True
                    return d              
    if match == False:
        print value
        return 'Dublin'
                    
for value in tag_value_list['addr:city']:
    city_converter(value)
                    


# In[37]:

#So thats why process map uses uncode dict writer...
u_utc = u'\xfa'
u_str = 'ú'
#u_utc.encode('ascii')   ~UnicodeEncodeError
type(u_str)

u = unicode(u_str, "utf-8")
u == u_utc


# In[ ]:

gealge_fada = ['á','é', 'í','ó','ú']
unicode_fada = {u'\xc1':'Á',u'\xc9':'É',u'\xda':'Ú',u'\xcd':'Í',u'\xda':'Ú',u'\xe1':'á',u'\xe9':'é',u'\xed':'í', u'\xf3':'ó',u'\xfa':'ú'}


# In[2]:

#Using Python sqlite3 DB API to update sqlite DB with csv files created above and using schema already existing.

import sqlite3
Tables = ['nodes', 'node_tags', 'ways', 'way_tags','ways_nodes', 'users']

db = sqlite3.connect(r"C:\Users\Donal\Downloads\sqlite_windows\osm_dublin.db")

c = db.cursor()

#select COUNT(*) from (select distinct "id" from ways)
#'select "key", COUNT(*) as num from node_tags group by "key" order by "key" DESC;'

#QUERY = 'SELECT *  FROM node_tags n0, (select "node id" from node_tags where "key" = "alt_name") n1 WHERE n0."node id" = n1."node id" ;'

QUERY = 'Select * from nodes limit 5;'

# = "SELECT name FROM sqlite_master WHERE type='table';"
c.execute(QUERY)

result = c.fetchall()

print result


# In[ ]:



