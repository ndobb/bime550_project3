import os
import csv
from string import Template

data_file_name = 'bmc_cancer_staging_dataset.csv'
ontology_file_name = 'tnm-2020.owl'

'''
    LungCancerPatient class. Represents a real lung cancer patient
    that is mapped from the csv file to the ontology.
'''
class LungCancerPatient:
    def __init__(self, src, i):
        self.raw = src
        self.location = self.map_location_to_ontology(src['source.location'])
        self.M = self.clean_stage(src['characteristics.tag.stage.mets'])
        self.N = self.clean_stage(src['characteristics.tag.stage.nodes'])
        self.T = self.clean_stage(src['characteristics.tag.stage.primary.tumor'])
        self.size = self.clean_size(src['characteristics.tag.tumor.size.maximumdiameter'])
        self.num = i

    def clean_stage(self, val):
        return str.replace(val, 'p', '')

    def clean_size(self, val):
        if val != '':
            return float(val)
        return None

    def map_location_to_ontology(self, loc):
        splt = [ s for s in loc.split(' ') if s != '' ]
        if len(splt) != 3:
            return None

        # "Left Lower Lung" -> "LowerLobeOfLeftLung"
        return splt[1] + splt[2] + "Of" + splt[0] + "Lung"

    def map_size_to_ontology(self):
        if self.size == None:
            return 'TumorSizeUnknown'
        if self.size < 2:
            return "TumorSmaller2cm"
        elif self.size >= 2 and self.size < 3:
            return "TumorBetween2cm3cm"
        elif self.size >= 3 and self.size < 5:
            return "TumorBetween3cm5cm"
        elif self.size >= 5 and self.size < 7:
            return "TumorBetween5cm7cm"
        elif self.size >= 7:
            return "TumorGreater7cm"
        return None

    def to_ontology_individual(self):
        t = Template('''###  http://smi.stanford.edu/people/dameron/ontology/tnm-lung-olivier.owl#EvalPatient$numinst
tnm-lung-olivier:EvalPatient$numinst rdf:type owl:NamedIndividual ,
                                           tnm-lung-olivier:EvalPatient$num .''')
        v = t.safe_substitute(num = self.num, numinst = f'{self.num}Instance')
        return v

    def to_ontology_class(self):
        t = Template('''###  http://smi.stanford.edu/people/dameron/ontology/tnm-lung-olivier.owl#EvalPatient$num
                tnm-lung-olivier:EvalPatient$num rdf:type owl:Class ;
                          rdfs:subClassOf tnm-lung-olivier:EvalPatient ,
                                          [ rdf:type owl:Restriction ;
                                            owl:onProperty tnm-lung-olivier:hasLocation ;
                                            owl:someValuesFrom tnm-lung-olivier:$loc
                                          ] ,
                                          [ rdf:type owl:Restriction ;
                                            owl:onProperty tnm-lung-olivier:hasPrimaryTumor ;
                                            owl:someValuesFrom tnm-lung-olivier:$size
                                          ] ,
                                          [ rdf:type owl:Restriction ;
                                            owl:onProperty tnm-lung-olivier:hasMetastasis ;
                                            owl:cardinality "$metas"^^xsd:nonNegativeInteger
                                          ] .''')

        metas="0"
        if self.M != "M0":
            metas="1"

        v = t.safe_substitute(num=self.num, 
                              loc=self.location, 
                              size=self.map_size_to_ontology(), 
                              metas=metas)
        return v

def main():
    pts = get_patients()
    ont = read_ontology()
    new_ont = insert_classes(ont, pts)
    new_ont = insert_individuals(new_ont, pts)
    write_new_ontology_to_file(new_ont, 'tnm_2020_eval.owl')

    x=1
    
def read_ontology():
    with open(ontology_file_name, 'r') as f:
        return f.read()

def get_classes_insert_line(ont):
    return get_insert_line(ont, '###  http://smi.stanford.edu/people/dameron/ontology/tnm-lung-olivier.owl#EvalPatient') + 3

def get_individuals_insert_line(ont):
    return get_insert_line(ont, '#    Individuals') + 2

def get_insert_line(ont, substr):
    i = 0
    for ln in ont.split('\n'):
        if ln.strip() == substr:
            return i
        i += 1

def insert_at_line(ont, insert_ln, substr):
    lines =  [ ln for ln in ont.split('\n')]
    new_lines = lines[:insert_ln] + [ substr ] + lines[insert_ln:]
    return str.join('\n', new_lines)

def write_new_ontology_to_file(ont, name):
    with open(name, 'w') as f:
        f.write(ont)

def insert_classes(ont, pts):
    insert_line = get_classes_insert_line(ont)
    pt_classes = str.join('\n\n\n', [ pt.to_ontology_class() for pt in pts ])
    new_ont = insert_at_line(ont, insert_line, pt_classes)
    return new_ont

def insert_individuals(ont, pts):
    insert_line = get_individuals_insert_line(ont)
    pt_individuals = str.join('\n\n\n', [ pt.to_ontology_individual() for pt in pts ])
    new_ont = insert_at_line(ont, insert_line, pt_individuals)
    return new_ont

def get_patients():
    pts = []
    with open(data_file_name, 'r', encoding='latin1') as csvfile:
        reader = csv.reader(csvfile)
        headers = next(reader, None)
        for i,row in enumerate(reader, 1):
            d = dict(zip(headers, row))
            pt = LungCancerPatient(d,i)
            pts.append(pt)
    return pts

main()