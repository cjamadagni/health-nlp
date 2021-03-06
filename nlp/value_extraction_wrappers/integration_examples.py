# !/usr/bin/env python3
"""

This code illustrates the use of these modules:

        date_finder.py
        size_measurement_finder.py
        value_extractor.py
        tnm_stager.py

"""

import json
from nlp.finder.date_finder import run as run_date_finder, DateValue, EMPTY_FIELD as EMPTY_DATE_FIELD
from nlp.value_extraction.value_extractor import run as run_value_extractor, ValueResult, Value, \
    EMPTY_FIELD as EMPTY_VALUE_FIELD
from nlp.finder.size_measurement_finder import run as run_size_measurement, SizeMeasurement, \
    EMPTY_FIELD as EMPTY_SMF_FIELD
from nlp.value_extraction.tnm_stage_extractor import run as run_tnm_stager, TNM_FIELDS, TnmCode, \
    EMPTY_FIELD as EMPTY_TNM_FIELD


###############################################################################
#
#  date finder
#
###############################################################################

sentences = [
    'The dates 2012/11/28 and 2012/03/15 are in iso_YYYYMMDD format.',
    'The dates 30-June 2008, 22DEC78, and 14 MAR 1879 use a string for the month.',
    'Johannes Brahms was born on May 7, 1833.',
    'The numbers 2004, 1968, 1492 are individual years.',
    'The words January, Feb., Sept. and December are individual months.'
]

print('\n\n***** DATE FINDER EXAMPLES ***** \n')

for sentence in sentences:

    # scan the sentence for dates
    json_string = run_date_finder(sentence)

    # parse the JSON result
    json_data = json.loads(json_string)

    # unpack to a list of DateValue namedtuples
    date_results = [DateValue(**m) for m in json_data]

    print('   sentence: ' + sentence)

    index = 0
    for d in date_results:
        print('       text[{0}]: {1}'.format(index, d.text))
        print('      start[{0}]: {1}'.format(index, d.start))
        print('        end[{0}]: {1}'.format(index, d.end))
        if EMPTY_DATE_FIELD != d.year:
            print('       year[{0}]: {1}'.format(index, d.year))
        if EMPTY_DATE_FIELD != d.month:
            print('      month[{0}]: {1}'.format(index, d.month))
        if EMPTY_DATE_FIELD != d.day:
            print('        day[{0}]: {1}'.format(index, d.day))
        print()
        index += 1

###############################################################################
#
#  size measurements
#
###############################################################################

sentences = [
    'The cyst measured 1.2 x 1.3 cm.',
    'The fluid had a volume of 15 cm3.',
    'The feature was 1.5 cm craniocaudal x 2.2 cm traverse.',
    'The various features measured 2.3, 1.5, 1.1, and 2.2 cm.',
    'Today the lesion measures 1.5 x 2 cm; previously it was 1.9cm x 2.3mm.'
]

print('\n\n***** SIZE MEASUREMENT EXAMPLES ***** \n')

for sentence in sentences:

    # scan the sentence for size measurements
    json_string = run_size_measurement(sentence)

    # parse the JSON result
    json_data = json.loads(json_string)

    # unpack to a list of SizeMeasurement namedtuples
    measurements = [SizeMeasurement(**m) for m in json_data]

    print('   sentence: ' + sentence)

    index = 0
    for m in measurements:
        print('       text[{0}]: {1}'.format(index, m.text))
        print('      start[{0}]: {1}'.format(index, m.start))
        print('        end[{0}]: {1}'.format(index, m.end))
        print('temporality[{0}]: {1}'.format(index, m.temporality))
        print('      units[{0}]: {1}'.format(index, m.units))
        print('  condition[{0}]: {1}'.format(index, m.condition))
        if EMPTY_SMF_FIELD != m.x:
            print('          x[{0}]: {1}'.format(index, m.x))
        if EMPTY_SMF_FIELD != m.y:
            print('          y[{0}]: {1}'.format(index, m.y))
        if EMPTY_SMF_FIELD != m.z:
            print('          z[{0}]: {1}'.format(index, m.z))
        if EMPTY_SMF_FIELD != m.values:
            print('     values[{0}]: {1}'.format(index, m.values))
        if EMPTY_SMF_FIELD != m.x_view:
            print('     x_view[{0}]: {1}'.format(index, m.x_view))
        if EMPTY_SMF_FIELD != m.y_view:
            print('     y_view[{0}]: {1}'.format(index, m.y_view))
        if EMPTY_SMF_FIELD != m.z_view:
            print('     z_view[{0}]: {1}'.format(index, m.z_view))
        print()
        index += 1

###############################################################################
#
#  value extraction
#
###############################################################################

sentences = [
    'Vitals: T: 99 BP: 115/68 P: 79 R:21 O2: 97',
    'Her BP on 3/27 from her 12 cm x 9 cm x 6 cm heart was 110/70.',
    'her BP was less than 120/80, his BP was gt 110 /70, BP lt. 110/70',
    'CTAB Pertinent Results: BLOOD WBC-7.0# RBC-4.02* Hgb-13.4* Hct-38.4* ' + \
    'MCV-96 MCH-33.2* MCHC-34.7 RDW-12.9 Plt Ct-172 02:24AM BLOOD WBC-4.4 RBC-4.21*',
]

print('\n\n***** VALUE EXTRACTION EXAMPLES *****\n')

search_terms = 'T, BP, WBC'

# limits can be either string or int
minval = 0
maxval = 1000

for sentence in sentences:

    # scan the sentence for the desired values
    json_string = run_value_extractor(search_terms, sentence, minval, maxval)

    # parse the JSON result
    json_data = json.loads(json_string)

    # unpack to a ValueResult namedtuple
    result = ValueResult(**json_data)
    print('        sentence: {0}'.format(result.sentence))
    print('           terms: {0}'.format(result.terms))
    print('    querySuccess: {0}'.format(result.querySuccess))
    print('measurementCount: {0}'.format(result.measurementCount))

    # get the array of measurements
    measurements = result.measurementList

    # unpack to a list of Value namedtuples
    values = [Value(**m) for m in measurements]

    index = 0
    for v in values:
        print('         text[{0}]: {1}'.format(index, v.text))
        print('        start[{0}]: {1}'.format(index, v.start))
        print('          end[{0}]: {1}'.format(index, v.end))
        print('    condition[{0}]: {1}'.format(index, v.condition))
        print(' matchingTerm[{0}]: {1}'.format(index, v.matchingTerm))
        print('            x[{0}]: {1}'.format(index, v.x))
        if EMPTY_VALUE_FIELD != v.y:
            print('            y[{0}]: {1}'.format(index, v.y))
        print()
        index += 1

###############################################################################
#
#  TNM stager
#
###############################################################################

sentences = [
    'The tumor is classified as pT0pN1M0.',
    'The tumor is classified as ypT0pN0M0, R0.',
    'The tumor is classified as pT4bpN1bM0 (stage IIIC).',
    'The tumor is classified as T4a N1a M1pul L1.',
    'The tumor is classified as pT1bpN0(1/34) pM1 LYM.',
    'The tumor is classified as ypT2C4(3) N1(2/16) pM1 G1-2VX L1 Pn0; R0 (liver), R1(cy+) (lung).'
]

print('\n\n***** TNM STAGING EXAMPLES *****\n')

for sentence in sentences:

    # scan the sentence for TNM codes
    json_string = run_tnm_stager(sentence)

    # parse the JSON result
    json_data = json.loads(json_string)

    # unpack to a list of TnmCode namedtuples
    tnm_codes = [TnmCode(**m) for m in json_data]

    # find the max length of all the field names:
    maxlen = len(max(TNM_FIELDS, key=len))

    print('   sentence: ' + sentence)

    index = 0
    for c in tnm_codes:

        # for each field in the field list
        for f in TNM_FIELDS:

            # get the value of this field for this code c
            attr = getattr(c, f)

            # print if field value is meaningful
            if EMPTY_TNM_FIELD != attr:
                indent = ' ' * (maxlen - len(f))
                print('{0}{1}: {2}'.format(indent, f, attr))
        print()
        index += 1