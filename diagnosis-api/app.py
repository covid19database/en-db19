import db19_pb2_grpc
import db19_pb2
import time
import logging
from concurrent import futures
import grpc
from datetime import datetime
from util import dt_to_enin
import psycopg2
import psycopg2.extras
logging.basicConfig(level=logging.INFO)


class DB19Server(db19_pb2_grpc.DiagnosisDBServicer):
    def __init__(self):
        while True:
            try:
                self.conn = psycopg2.connect("dbname=covid19 user=covid19 \
                                             port=5432 host=diagnosis-db \
                                             password=covid19databasepassword")
                # psycopg2.extras.register_hstore(conn)
                break
            except psycopg2.OperationalError:
                logging.info("Could not connect to DB; retrying...")
                time.sleep(1)
                continue

    def check_authority(self, hak):
        with self.conn.cursor() as cur:
            cur.execute("SELECT * FROM health_authorities WHERE HAK=%s",
                        (hak,))
            return cur.fetchone() is not None

    def insert_report(self, reports):
        with self.conn.cursor() as cur:
            ins = "INSERT INTO reported_keys(TEK, ENIN, HAK) VALUES \
                   (%s, %s, %s) ON CONFLICT DO NOTHING"
            cur.executemany(ins, reports)
        self.conn.commit()

    def AddReport(self, request, context):
        # TODO: check validity of authority
        try:
            authority_key = request.authority
            if len(authority_key) != 16:
                raise Exception("Invalid authority length")
            if not self.check_authority(authority_key):
                raise Exception("Invalid authority value")

            to_insert = []
            logging.info(f"validating reports: {len(request.reports)}")
            for report in request.reports:
                tek = report.TEK
                if len(tek) != 16:
                    raise Exception("Invalid TEK")
                timestamp = datetime.utcfromtimestamp(report.ENIN * 600)
                to_insert.append((tek, timestamp, authority_key))
            logging.info(f"inserting reports: {len(to_insert)}")
            self.insert_report(to_insert)
            return db19_pb2.AddReportResponse()
        except Exception as e:
            return db19_pb2.AddReportResponse(error=str(e))

    def GetDiagnosisKeys(self, request, context):
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT TEK, ENIN FROM reported_keys")
                for row in cur:
                    tek_b, enin_ts = row
                    tek = bytes(tek_b)
                    enin = dt_to_enin(enin_ts)
                    yield db19_pb2.GetDiagnosisKeyResponse(
                        record=db19_pb2.TimestampedTEK(TEK=tek, ENIN=enin)
                    )
        except Exception as e:
            yield db19_pb2.GetDiagnosisKeyResponse(error=str(e))


if __name__ == '__main__':
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    db19_pb2_grpc.add_DiagnosisDBServicer_to_server(DB19Server(), server)
    server.add_insecure_port('[::]:5000')
    logging.info("Starting server")
    server.start()
    server.wait_for_termination()
