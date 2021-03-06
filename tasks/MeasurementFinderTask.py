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

SECTIONS_FILTER = "sections"


def mongo_writer(client, pipeline, job, batch, pipeline_config:config.PipelineConfig, meas: Measurement, doc, type):
    db = client[util.mongo_db]
    value = meas['X']

    obj = {
        "pipeline_type": type,
        "pipeline_id": pipeline,
        "job_id": job,
        "batch": batch,
        "owner": pipeline_config.owner,
        "sentence": meas.sentence,
        "report_type": doc["report_type"],
        "nlpql_feature": pipeline_config.name,
        "inserted_date": datetime.datetime.now(),
        "report_id": doc["report_id"],
        "subject": doc["subject"],
        "report_date": doc["report_date"],
        "section": "",
        "concept_code": pipeline_config.concept_code,
        "text": meas.text,
        "start": meas.start,
        "value": value,
        "end": meas.end,
        "term": meas.subject,
        "dimension_X": meas.X,
        "dimension_Y": meas.Y,
        "dimension_Z": meas.Z,
        "units": meas.units,
        "location": meas.location,
        "condition": meas.condition,
        "value1": meas.value1,
        "value2": meas.value2,
        "temporality": meas.temporality,
        "phenotype_final": False
    }

    inserted = config.insert_pipeline_results(pipeline_config, db, obj)

    return inserted


class MeasurementFinderTask(luigi.Task):
    pipeline = luigi.IntParameter()
    job = luigi.IntParameter()
    start = luigi.IntParameter()
    batch = luigi.IntParameter()
    solr_query = luigi.Parameter()
    segment = segmentation.Segmentation()

    def run(self):
        client = MongoClient(util.mongo_host, util.mongo_port)

        try:
            jobs.update_job_status(str(self.job), util.conn_string, jobs.IN_PROGRESS,
                                   "Running MeasurementFinder Batch %s" %
                                   self.batch)

            pipeline_config = config.get_pipeline_config(self.pipeline, util.conn_string)

            jobs.update_job_status(str(self.job), util.conn_string, jobs.IN_PROGRESS, "Running Solr query")
            docs = solr_data.query(self.solr_query, rows=util.row_count, start=self.start, solr_url=util.solr_url,
                                   tags=pipeline_config.report_tags, mapper_inst=util.report_mapper_inst,
                                   mapper_url=util.report_mapper_url, mapper_key=util.report_mapper_key,
                                   cohort_ids=pipeline_config.cohort)

            filters = dict()
            if pipeline_config.sections and len(pipeline_config.sections) > 0:
                filters[SECTIONS_FILTER] = pipeline_config.sections

            with self.output().open('w') as outfile:
                jobs.update_job_status(str(self.job), util.conn_string, jobs.IN_PROGRESS,
                                       "Finding terms with MeasurementFinder")
                # TODO incorporate sections and filters
                for doc in docs:
                    meas_results = run_measurement_finder_full(doc["report_text"], pipeline_config.terms)
                    for meas in meas_results:
                        inserted = mongo_writer(client, self.pipeline, self.job, self.batch, pipeline_config, meas, doc,
                                                "MeasurementFinder")
                        outfile.write(str(inserted))
                        outfile.write('\n')
                    del meas_results
            del docs
        except Exception as ex:
            traceback.print_exc(file=sys.stderr)
            jobs.update_job_status(str(self.job), util.conn_string, jobs.WARNING, ''.join(traceback.format_stack()))
            print(ex)
        finally:
            client.close()

    def output(self):
        return luigi.LocalTarget("%s/pipeline_job%s_measurement_finder_batch%s.txt" % (util.tmp_dir, str(self.job),
                                                                                       str(self.start)))
