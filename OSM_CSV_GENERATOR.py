#DOF OSM to CSV converter, shape data updated. Ver2.

filename = 'C:\Users\Donal\Downloads\dublin_ireland'
#filename = 'C:\Users\Donal\Downloads\map_of_dublin_mini'
filepath = r"C:\Users\Donal\Downloads\\"

import csv
import codecs
import re
import xml.etree.cElementTree as ET

import cerberus

import schema

OSM_PATH = filepath + 'map_of_dublin.csv'
NODES_PATH = filepath +  "nodes.csv"
NODE_TAGS_PATH = filepath +  "nodes_tags.csv"
WAYS_PATH = filepath +  "ways.csv"
WAY_NODES_PATH = filepath +  "ways_nodes.csv"
WAY_TAGS_PATH = filepath +  "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SCHEMA = schema.schema

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

# for each xml element, parse out nodes/ways/tags and return dict with the way/node and tags. 
def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements
    #print 'tag = ', element.tag , 'keys = ' , element.keys(), element.attrib
    if element.tag == 'node':
        for attr in node_attr_fields:
            node_attribs[attr] =  element.attrib[attr]
        tags = tag_handler(element, default_tag_type)
        return {'node': node_attribs, 'node_tags': tags}
    elif element.tag == 'way':
        for attr in way_attr_fields:
            way_attribs[attr] =  element.attrib[attr]
        tags = tag_handler(element, default_tag_type)
        way_nodes = way_node_handler(element)
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}

#function to take tag tree, nested in way or node and extract tags in correct format
#First tests for problem chars and then call conversion funtions if needed
def tag_handler(element, default_tag_type):
    tags = []
    for e in element.iter('tag'):
        tag = {}
        tag['id'] = element.attrib['id']
        key = e.attrib['k']
        tag_type = default_tag_type
        if re.search(PROBLEMCHARS, key):
            key = None
            print key, 'problem key'
        else:
            #default tag value is current 'v', if statements used to modify if needed
            tag_value = e.attrib['v']        
            #Checking for sub types delimited by ":"
            if re.search(LOWER_COLON, key):
                colon = key.find(':')
                tag_type = key[:colon]
                #If addr:city call city converter function to modify tag value 
                if key == 'addr:city':
                    tag_value = city_converter(e.attrib['v'])
                #Add ther other fixes here...
                elif key == 'addr:street':
                    pass
                #Update key to remove type last for accurate conversion functions
                key = key[colon + 1 :] 
        tag['key'] =  key      
        tag['value'] = tag_value
        tag['type'] = tag_type
        tags.append(tag)
    #print tags
    return tags



def way_node_handler(element):
    way_nodes = []
    pos = 0
    for e in element.iter('nd'):
        way_node = {}
        way_node['id'] = element.attrib['id']
        way_node['node_id'] = e.attrib['ref']
        way_node['position'] = pos
        pos += 1
        way_nodes.append(way_node)
    return way_nodes

############ Update functions to handle data cleaning:  
      
dublin_re = re.compile(r'Dublin ?[0-9]?[0-9W]?$')
#Towns/villages seperate from Dublin, some are within the county of Dublin so this
#is somewhat subjective classififcation. It should be noted some of these towns are
#not in the county of Dublin at all.
not_dublin = ['Celbridge','Lucan','Leixlip','Malahide','Bray','Portmarnock',\
    'Kilternan','Dunshaughlin','Donabate','Batterstown','Baldonnel']
#Areas of Dublin are assigned, though not consistantly, using the Dublin area
#code. Again assignment of areas on the outskirts of the city but within 
#the county is subjective.
in_dublin = {'Dublin':['Killiney','Blackrock','Harristown','Swords','Stillorgan',\
    'Dún Laoghaire','Monkstown','Mount Merrion','Cornelscourt'],\
    'Dublin 15':['Ongar','Blanchardstown'], 'Dublin 18': ['Cabinteely'],\
    'Dublin 14': ['Rathfarnham','Churchtown'], 'Dublin 4':['Donnybrook'],\
    'Dublin 24':['Tallaght'],'Dublin 22': ['Clondalkin'],'Dublin 3': ['Clontarf'] }
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
				#Many unicode related frustrations before unicode converter was added due to non-equality of unicode and stings.
                    match = True
                    return d            				
    if match == False:        
        return 'Dublin'

########Street name fixer
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

#Creating regular expressions to locate abreviations to street naming.
avenue_re = re.compile(r'\bave?\.?\b', re.IGNORECASE)
street_re = re.compile(r'\stre?\.?\b', re.IGNORECASE)
road_re = re.compile(r'\rd\.?\b', re.IGNORECASE)

expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons"]

# Updated to have regular expressions for finding street name mappings
mapping = { street_re: "Street",
            avenue_re: "Avenue",
            road_re: "Road"
            }
            
def street_converter(name, mapping):
    m = street_type_re.search(name)
    if m:
        street_type = m.group()
        #Look for street names not in regular convention and update based on re mapping
        if street_type not in expected:
            for reg_exp in mapping:
                if reg_exp.search(name[name.find(street_type):]):
                    name = name[:name.find(street_type)] + mapping[reg_exp]               
    return name



# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_strings = (
            "{0}: {1}".format(k, v if isinstance(v, str) else ", ".join(v))
            for k, v in errors.iteritems()
        )
        raise cerberus.ValidationError(
            message_string.format(field, "\n".join(error_strings))
        )


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            #print el
            if el:

                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])
                elif element.tag == 'relation':
                    pass
                    #account for relation



if __name__ == '__main__':
    # Note: Validation is ~ 10X slower. For the project consider using a small
    # sample of the map when validating.
    process_map(filename, validate=False)
