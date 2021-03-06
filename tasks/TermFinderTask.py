import luigi
from data_access import solr_data
from data_access import pipeline_config as config
from nlp import *
from data_access import jobs
from pymongo import MongoClient
import datetime
import util
import traceback
import sys

provider_assertion_filters = {
    'negex': ["Affirmed"],
    "temporality": ["Recent", "Historical"],
    "experiencer": ["Patient"]
}
SECTIONS_FILTER = "sections"


def mongo_writer(client, pipeline, job, batch, pipeline_config, term, doc, type):
    db = client[util.mongo_db]

    obj = {
        "pipeline_type": type,
        "pipeline_id": pipeline,
        "job_id": job,
        "batch": batch,
        "owner": pipeline_config.owner,
        "sentence": term.sentence,
        "report_type": doc["report_type"],
        "nlpql_feature": pipeline_config.name,
        "inserted_date": datetime.datetime.now(),
        "report_id": doc["report_id"],
        "subject": doc["subject"],
        "report_date": doc["report_date"],
        "section": term.section,
        "term": term.term,
        "start": term.start,
        "end": term.end,
        "concept_code": pipeline_config.concept_code,
        "negation": term.negex,
        "temporality": term.temporality,
        "experiencer": term.experiencer,
        "phenotype_final": False
    }

    inserted = config.insert_pipeline_results(pipeline_config, db, obj)

    return inserted


class TermFinderBatchTask(luigi.Task):
    pipeline = luigi.IntParameter()
    job = luigi.IntParameter()
    start = luigi.IntParameter()
    batch = luigi.IntParameter()
    solr_query = luigi.Parameter()
    segment = segmentation.Segmentation()

    def run(self):
        client = MongoClient(util.mongo_host, util.mongo_port)

        try:
            jobs.update_job_status(str(self.job), util.conn_string, jobs.IN_PROGRESS, "Running TermFinder Batch %s" %
                                   self.batch)

            pipeline_config = config.get_pipeline_config(self.pipeline, util.conn_string)

            jobs.update_job_status(str(self.job), util.conn_string, jobs.IN_PROGRESS, "Running Solr query")
            docs = solr_data.query(self.solr_query, rows=util.row_count, start=self.start, solr_url=util.solr_url,
                                   tags=pipeline_config.report_tags, mapper_inst=util.report_mapper_inst,
                                   mapper_url=util.report_mapper_url, mapper_key=util.report_mapper_key)
            term_matcher = TermFinder(pipeline_config.terms, pipeline_config.include_synonyms, pipeline_config
                                      .include_descendants, pipeline_config.include_ancestors, pipeline_config
                                      .vocabulary)
            filters = dict()
            if pipeline_config.sections and len(pipeline_config.sections) > 0:
                filters[SECTIONS_FILTER] = pipeline_config.sections

            with self.output().open('w') as outfile:
                jobs.update_job_status(str(self.job), util.conn_string, jobs.IN_PROGRESS,
                                       "Finding terms with TermFinder")
                for doc in docs:
                    terms_found = term_matcher.get_term_full_text_matches(doc["report_text"], filters)
                    for term in terms_found:
                        inserted = mongo_writer(client, self.pipeline, self.job, self.batch, pipeline_config, term, doc,
                                                "TermFinder")
                        outfile.write(str(inserted))
                        outfile.write('\n')
                    del terms_found
            del docs
        except Exception as ex:
            traceback.print_exc(file=sys.stderr)
            jobs.update_job_status(str(self.job), util.conn_string, jobs.WARNING, ''.join(traceback.format_stack()))
            print(ex)
        finally:
            client.close()

    def output(self):
        return luigi.LocalTarget("%s/pipeline_job%s_term_finder_batch%s.txt" % (util.tmp_dir, str(self.job),
                                                                                str(self.start)))


class ProviderAssertionBatchTask(luigi.Task):
    pipeline = luigi.IntParameter()
    job = luigi.IntParameter()
    start = luigi.IntParameter()
    batch = luigi.IntParameter()
    solr_query = luigi.Parameter()
    segment = segmentation.Segmentation()
    client = MongoClient(util.mongo_host, util.mongo_port)

    def run(self):

        client = MongoClient(util.mongo_host, util.mongo_port)

        try:
            jobs.update_job_status(str(self.job), util.conn_string, jobs.IN_PROGRESS,
                                   "Running ProviderAssertion Batch %s" %
                                   self.batch)

            pipeline_config = config.get_pipeline_config(self.pipeline, util.conn_string)

            jobs.update_job_status(str(self.job), util.conn_string, jobs.IN_PROGRESS, "Running Solr query")
            docs = solr_data.query(self.solr_query, rows=util.row_count, start=self.start, solr_url=util.solr_url,
                                   tags=pipeline_config.report_tags, report_type_query=pipeline_config.report_type_query, mapper_inst=util.report_mapper_inst,
                                   mapper_url=util.report_mapper_url, mapper_key=util.report_mapper_key,
                                   cohort_ids=pipeline_config.cohort)
            term_matcher = TermFinder(pipeline_config.terms, pipeline_config.include_synonyms, pipeline_config
                                      .include_descendants, pipeline_config.include_ancestors, pipeline_config
                                      .vocabulary)
            pa_filters = provider_assertion_filters
            if pipeline_config.sections and len(pipeline_config.sections) > 0:
                pa_filters[SECTIONS_FILTER] = pipeline_config.sections

            with self.output().open('w') as outfile:
                jobs.update_job_status(str(self.job), util.conn_string, jobs.IN_PROGRESS,
                                       "Finding terms with TermFinder")
                for doc in docs:
                    terms_found = term_matcher.get_term_full_text_matches(doc["report_text"], pa_filters)
                    for term in terms_found:
                        inserted = mongo_writer(client, self.pipeline, self.job, self.batch, pipeline_config, term, doc,
                                                "ProviderAssertion")
                        outfile.write(str(inserted))
                        outfile.write('\n')
                    del terms_found
            del docs
        except Exception as ex:
            traceback.print_exc(file=sys.stderr)
            jobs.update_job_status(str(self.job), util.conn_string, jobs.WARNING, ''.join(traceback.format_stack()))
            print(ex)
        finally:
            client.close()

    def output(self):
        return luigi.LocalTarget("%s/pipeline_job%s_provider_assertion_batch%s.txt" % (util.tmp_dir, str(self.job),
                                                                                str(self.start)))
