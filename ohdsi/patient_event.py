import requests
import json
import string
import configparser
import psycopg2
import psycopg2.extras
import re
import os
import datetime

# Function to identify query based on domain
def get_query(name):
    if name == "Drugs":
        query = """ SELECT DISTINCT person_id, drug_concept_id, drug_era_start_date, drug_era_end_date FROM mimic_v5.drug_era a
                    INNER JOIN (SELECT subject_id FROM mimic_v5.cohort WHERE cohort_definition_id = %s) b ON a.person_id = b.subject_id
                    WHERE a.drug_concept_id IN %s
                """

    elif name == "Conditions":
        query = """ SELECT DISTINCT person_id, condition_concept_id, condition_era_start_date, condition_era_end_date FROM mimic_v5.condition_era a
                    INNER JOIN (SELECT subject_id FROM mimic_v5.cohort WHERE cohort_definition_id = %s) b ON a.person_id = b.subject_id
                    WHERE a.condition_concept_id IN %s
                """

    elif name == "Procedures":
        query = """ SELECT DISTINCT person_id, procedure_concept_id, procedure_date FROM mimic_v5.procedure_occurrence a
                    INNER JOIN (SELECT subject_id FROM mimic_v5.cohort WHERE cohort_definition_id = %s) b ON a.person_id = b.subject_id
                    WHERE a.procedure_concept_id IN %s
                """
    elif name == "Observations":
        query = """ SELECT DISTINCT person_id, observation_concept_id, observation_date FROM mimic_v5.observation a
                    INNER JOIN (SELECT subject_id FROM mimic_v5.cohort WHERE cohort_definition_id = %s) b ON a.person_id = b.subject_id
                    WHERE a.observation_concept_id IN %s
                """
    elif name == "Visits":
        query = """ SELECT DISTINCT person_id, visit_concept_id, visit_start_date, visit_end_date FROM mimic_v5.visit_occurrence a
                    INNER JOIN (SELECT subject_id FROM mimic_v5.cohort WHERE cohort_definition_id = %s) b ON a.person_id = b.subject_id
                    WHERE a.visit_concept_id IN %s
                """
    elif name == "Measurements":
        query = """ SELECT DISTINCT person_id, measurement_concept_id, measurement_date FROM mimic_v5.measurement a
                    INNER JOIN (SELECT subject_id FROM mimic_v5.cohort WHERE cohort_definition_id = %s) b ON a.person_id = b.subject_id
                    WHERE a.measurement_concept_id IN %s
                """
    else:
        return -1

    return query


# Function to construct JSON output
def construct_output(result):
    output = []
    for i in result:
        if len(i) == 4:
            output.append({'person_id': i[0], 'concept_id': i[1], 'start_date': str(i[2]), 'end_date': str(i[3])})
        else:
            output.append({'person_id': i[0], 'concept_id': i[1], 'start_date': str(i[2]), 'end_date': None})

    return output


def getPatientEvent(cohort_id, domain, conceptset, conn_string):

    # DB connection
    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor()

    # Querying DB
    output = []
    try:
        query = get_query(domain)
        if query == -1:
            return "Domain name does not exist."

        cursor.execute(query,(cohort_id, conceptset))
        result = cursor.fetchall()
        output = construct_output(result)


    except Exception as ex:
        print ("Failed to extract data from DB")
        print (ex)

    # Constructing output
    if len(output) > 0:
        return json.dumps(output)
    else:
        return "No patient events for given criteria"






# For testing only
# TODO: remove once stable
if __name__=='__main__':
    config = configparser.RawConfigParser()
    config.read('../project.cfg')
    conn_string = "host='%s' dbname='%s' user='%s' password='%s' port=%s" % (os.environ.get('NLP_PG_HOSTNAME', config.get('pg2', 'host')),
                                                                             os.environ.get('NLP_PG_DATABASE', config.get('pg2', 'dbname')),
                                                                             os.environ.get('NLP_PG_USER', config.get('pg2', 'user')),
                                                                             os.environ.get('NLP_PG_PASSWORD', config.get('pg2', 'password')),
                                                                             str(os.environ.get('NLP_PG_CONTAINER_PORT', config.get('pg2', 'port'))))
    print (conn_string)
    #getPatientEvent(10,"Drugs",(919345,1717327), conn_string)
    #getPatientEvent(20,"Conditions",(132797,40481816), conn_string)
    #getPatientEvent(30,"Procedures",(2514413,2514409), conn_string)
    #getPatientEvent(40,"Observations",(441054,4015724), conn_string)
    output = getPatientEvent(50,"Measurements",(3023103,3037278), conn_string)
    #output = getPatientEvent(60,"Visits",(9203,), conn_string)
    print (output)