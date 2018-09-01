import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET
import sys

import cerberus

import schema

OSM_PATH = "../data/Laguna_Hills_CA_map.osm"

NODES_PATH = "../data/nodes.csv"
NODE_TAGS_PATH = "../data/nodes_tags.csv"
WAYS_PATH = "../data/ways.csv"
WAY_NODES_PATH = "../data/ways_nodes.csv"
WAY_TAGS_PATH = "../data/ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SCHEMA = schema.schema

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']



# ================================================== #
#         Fix Attribute Value Function               #
# ================================================== #

def fix_value(key, value):
    if 'street' in key:
        street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
        mapping =   {'Ave' : 'Avenue',
                    'Blvd' : 'Boulevard',
                    'Ct.' : 'Court',
                    'Dr' : 'Drive',
                    'Dr.' : 'Drive',
                    'Pkwy' : 'Parkway',
                    'Pkwy.' : 'Parkway',
                    'Rd' : 'Road'}
        m = street_type_re.search(value)
                                     
        if m:
            street_type = m.group()                                         
            if street_type in mapping:
                fixed_value = value.replace(street_type, mapping[street_type])
                return fixed_value
            else:
                return value

    elif 'phone' in key:
        phone_type_re = re.compile(r'^\+\d{1}[\-]\d{3}[\-]\d{3}[\-]\d{4}$')

        m = phone_type_re.search(value)

        if not m:
            remove_spec_char = ''.join(e for e in value if e.isalnum())
            remove_lead_one = remove_spec_char[1:]
            fixed_phone = '+1-' + remove_lead_one[:3] + '-' + remove_lead_one[3:6] + '-' + remove_lead_one[6:]

            return fixed_phone

        else:
            return value

    return value

  


def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements

    if element.tag == 'node':
        # Iterate over node fields
               
        for tag in element.iter('node'):
            for field in node_attr_fields:
                node_attribs[field] = tag.attrib[field]
        
            node_id = tag.attrib['id']       
            
        for tag in element.iter('tag'):
            entries = {}
            entries['id'] = node_attribs['id']
            
            entries['key']= tag.attrib['k']
            entries['value']= fix_value(tag.attrib['k'], tag.attrib['v'])
            entries['type']= 'regular'

            tags.append(entries)

        return {'node': node_attribs, 'node_tags': tags}

    elif element.tag == 'way':
        for tag in element.iter('way'):
            for field in way_attr_fields:
                way_attribs[field]= tag.attrib[field]

            for tag in element.iter('tag'):
                entries = {}
                         
                entries['id'] = way_attribs['id']
                entries['key']= tag.attrib['k']
                entries['value'] = fix_value(tag.attrib['k'], tag.attrib['v'])               
                entries['type']= 'regular'
    
                tags.append(entries)

            position = 0
            for tag in element.iter('nd'):
                entries_nd = {}
                entries_nd['id'] = way_attribs['id']
                entries_nd['node_id'] = tag.attrib['ref']
                entries_nd['position'] = position
                position += 1

            way_nodes.append(entries_nd)


        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}


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
        error_string = pprint.pformat(errors)
        
        raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    #def writerow(self, row):
    #    super(UnicodeDictWriter, self).writerow({
    #        k: (v.encode('utf-8') if isinstance(v, str) else v) for k, v in row.items()
    #    })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w', encoding='utf8') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w', encoding='utf8') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w', encoding='utf8') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'w', encoding='utf8') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w', encoding='utf8') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS, lineterminator='\n')
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS, lineterminator='\n')
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS, lineterminator='\n')
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS, lineterminator='\n')
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS, lineterminator='\n')

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
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


if __name__ == '__main__':
    # Note: Validation is ~ 10X slower. For the project consider using a small
    # sample of the map when validating.
    process_map(OSM_PATH, validate=True)
