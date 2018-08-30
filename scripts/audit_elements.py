# To audit additional elements:
#   1. Add new alement to audit_elem set 
#   2. Create regular expression to match element variable
#   3. Create a new dictionary variable
#   4. Create an if statement in audit_element_type function to handle audit logic
#   5. Add new dictionary to print statement in audit function 

import xml.etree.cElementTree as ET 
from collections import defaultdict
import re
import pprint

osm_file = open('../data/Laguna_Hills_CA_map.osm', encoding='utf8')


# add elements to be audited to audit_elem set
audit_elem = {'street', 'zip', 'phone'}

# add regular expression to match new element variables
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
zipcode_type_re = re.compile(r'\d{5}$')
phone_type_re = re.compile(r'^\+\d{1}[\-]\d{3}[\-]\d{3}[\-]\d{4}$')

# add new dictionary variable for additional elements to audit
street_types = defaultdict(set)
phone_numbers = defaultdict(set)
zipcodes = defaultdict(set)


# add new if statement to handle additional elements to audit
# called from audit() function
def audit_element_type(element, attribute_value):                       
    
    # audits the street information
    # creates a dictionary of street types and street name that are not found in expected street names
    if element == 'street':
        expected_street_names = ['Street', 'Avenue', 'Boulevard', 'Drive', 'Court', 'Place', 'Square', 'Lane', 'Road', 
            'Trail', 'Parkway', 'Commons', 'Bend', 'Chase', 'Circle', 'Cove', 'Crossing', 'Hill',
            'Hollow', 'Loop', 'Park', 'Pass', 'Overlook', 'Path', 'Plaza', 'Point', 'Ridge', 'Row',
            'Run', 'Terrace', 'Walk', 'Way', 'Trace', 'View', 'Vista']
        m = street_type_re.search(attribute_value)                              
        if m:
            street_type = m.group()                                         
            if street_type not in expected_street_names:                    
                street_types[street_type].add(attribute_value)

    # audits the zipcode variable
    # creates creates a dictionary of zipcodes that do match a 5 digit length
    elif element == 'zip':
        m = zipcode_type_re.match(attribute_value)
        if not m:
            zipcodes[attribute_value].add(attribute_value)

    # audits the phone number variable
    # creates a dictionary of phone numbers that do not match the pattern country code - area code - phone number (+1-111-111-1111)
    elif element == 'phone':
        m = phone_type_re.match(attribute_value)
        if not m:
            phone_numbers[attribute_value].add(attribute_value)
    

# called from audit() function
# determines if the element is found in the attribute tag to be audited
def is_element_to_audit(element, tag):                                    
    return (element in tag.attrib['k'])                              

# takes a set of elements to be audited, loops through the osm file and passes them to audit_element_type function for auditing
def audit(audit_elem):                                                     
    for event, elem in ET.iterparse(osm_file, events=('start',)):
        for element in audit_elem:
            if elem.tag == 'way':
                for tag in elem.iter('tag'):
                    if is_element_to_audit(element, tag):            
                        audit_element_type(element, tag.attrib['v']) 
        
    # add print statement for each element to audit
    # include a couple line breaks (\n) so output is readable in the terminal
    print('\n\nStreet Type to review:')
    pprint.pprint(dict(street_types))
    print('\n\nZipcodes to review:')
    pprint.pprint(dict(zipcodes))
    print('\n\nPhone Numbers to reveiw:')
    pprint.pprint(dict(phone_numbers))

if __name__ == '__main__':
    audit(audit_elem)
    