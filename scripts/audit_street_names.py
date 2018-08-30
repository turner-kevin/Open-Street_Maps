import xml.etree.cElementTree as ET 
from collections import defaultdict
import re
import pprint

osm_file = open('../data/Laguna_Hills_CA_map.osm', encoding='utf8')

street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
street_types = defaultdict(set)

expected = ['Street', 'Avenue', 'Boulevard', 'Drive', 'Court', 'Place', 'Square', 'Lane', 'Road', 
            'Trail', 'Parkway', 'Commons', 'Bend', 'Chase', 'Circle', 'Cove', 'Crossing', 'Hill',
            'Hollow', 'Loop', 'Park', 'Pass', 'Overlook', 'Path', 'Plaza', 'Point', 'Ridge', 'Row',
            'Run', 'Terrace', 'Walk', 'Way', 'Trace', 'View', 'Vista']


def audit_street_type(street_types, street_name):                       # called from audit()
    m = street_type_re.search(street_name)                              # function looks for the last word in the street address using a regular expression
    if m:
        street_type = m.group()                                         
        if street_type not in expected:                                 # if returned street name is not in expected list, add it to the dictionary
            street_types[street_type].add(street_name)


def is_street_name(elem):                                               # called from audit()
    return ('street' in elem.attrib['k'])                          # function determines if the element has a 'addr:street' attribute. Returns True if exists, else False



def audit():                                                            # function parses through OSM file and finds all 'way' elements
    for event, elem in ET.iterparse(osm_file, events=('start',)):
        if elem.tag == 'way':
            for tag in elem.iter('tag'):
                if is_street_name(tag):                                 # sends results to is_street_name function to determine if the 'way' element' has an 'addr:street' attribute
                    audit_street_type(street_types, tag.attrib['v'])    # if an 'addr:street' attribute is found, sends that value to audit_street_type function
    pprint.pprint(dict(street_types))

if __name__ == '__main__':
    audit()