import db19_pb2_grpc
import db19_pb2
import time
import logging
from concurrent import futures
import grpc
from datetime import datetime, timedelta
from util import dt_to_enin, generate_authorization_key
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

    def check_api_key(self, api_key):
        with self.conn.cursor() as cur:
            cur.execute("SELECT * FROM health_authorities WHERE api_key=%s",
                        (api_key,))
            return cur.fetchone() is not None

    def insert_report(self, reports):
        with self.conn.cursor() as cur:
            ins = "INSERT INTO reported_keys(TEK, ENIN, authorization_key) \
                    VALUES (%s, %s, %s) ON CONFLICT DO NOTHING"
            cur.executemany(ins, reports)
        self.conn.commit()

    def generate_authorization_key(self, health_authority_api_key, key_type):
        """
        Returns generated authorization key after storing the mapping in the
        database
        """
        assert key_type in ['DIAGNOSED']
        auth_key = generate_authorization_key()
        with self.conn.cursor() as cur:
            cur.execute("INSERT INTO authorization_keys(authorization_key, \
                         api_key, key_type) VALUES (%s, %s, %s);",
                         (auth_key, health_authority_api_key, key_type))
        self.conn.commit()
        return auth_key

    def check_authorization_key(self, auth_key):
        with self.conn.cursor() as cur:
            cur.execute("SELECT * FROM authorization_keys WHERE \
                         authorization_key = %s", (auth_key, ))
            return cur.fetchone() is not None


    def AddReport(self, request, context):
        try:
            auth_key = request.authorization_key
            if len(auth_key) != 16:
                raise Exception("Invalid auth_key length")
            if not self.check_authorization_key(auth_key):
                raise Exception("Invalid auth_key value")

            to_insert = []
            logging.info(f"validating reports: {len(request.reports)}")
            for report in request.reports:
                tek = report.TEK
                if len(tek) != 16:
                    raise Exception("Invalid TEK")
                timestamp = datetime.utcfromtimestamp(report.ENIN * 600)
                to_insert.append((tek, timestamp, auth_key))
            logging.info(f"inserting reports: {len(to_insert)}")
            self.insert_report(to_insert)
            return db19_pb2.AddReportResponse()
        except Exception as e:
            return db19_pb2.AddReportResponse(error=str(e))

    def GetDiagnosisKeys(self, request, context):
        # request.HAK
        # request.ENIN # round to nearest day
        values = []

        authority_query = "SELECT TEK, ENIN FROM reported_keys \
                           WHERE authority_id = %s \
                           JOIN authorization_keys USING (authorization_key) \
                           JOIN health_authorities USING (api_key)"

        enin_query = "SELECT TEK, ENIN FROM reported_keys \
                      WHERE ENIN >= %s AND ENIN <= %s"

        queries = []
        values = []
        # query = f"( {authority_query} ) UNION ( {enin_query} )"

        if len(request.HAK) > 0:
            queries.append(authority_key)
            values.append(request.HAK)
        if request.ENIN > 0:
            ts = datetime.utcfromtimestamp(request.ENIN * 600)
            enin_start = datetime(year=ts.year, month=ts.month,
                                  day=ts.day, tzinfo=ts.tzinfo)
            enin_end = enin_start + timedelta(days=1)
            queries.append(enin_query)
            values.append(enin_start)
            values.append(enin_end)
        if len(request.hrange.start_date) > 0 or request.hrange.days > 0:
            logging.info(f"hrange: {request.hrange}")
            # default to current date if start_date not defined
            if len(request.hrange.start_date) == 0:
                n = datetime.now()
                end_time = datetime(year=n.year, month=n.month, day=n.day)
            else:
                end_time = datetime.strptime(request.hrange.start_date, '%Y-%m-%d')

            # default to at least 1 day
            num_days = max(request.hrange.days, 1)

            start_time = end_time - timedelta(days=num_days)

            queries.append(enin_query)
            values.append(start_time)
            values.append(end_time)

        if len(queries) == 0:
            query = "SELECT TEK, ENIN FROM reported_keys"
            values = []
        elif len(queries) == 1:
            query = queries[0]
        else:
            query = " UNION ".join([f"( {q} )" for q in queries])
        try:
            with self.conn.cursor() as cur:
                logging.info(f"query {cur.mogrify(query, values)}")
                cur.execute(query, values)
                for row in cur:
                    tek_b, enin_ts = row
                    tek = bytes(tek_b)
                    enin = dt_to_enin(enin_ts)
                    yield db19_pb2.GetDiagnosisKeyResponse(
                        record=db19_pb2.TimestampedTEK(TEK=tek, ENIN=enin)
                    )
        except Exception as e:
            yield db19_pb2.GetDiagnosisKeyResponse(error=str(e))

    def GetAuthorizationToken(self, request, context):
        try:
            api_key = request.api_key
            if len(api_key) != 16:
                raise Exception("Invalid api_key length")
            if not self.check_api_key(api_key):
                raise Exception("Invalid api_key value")
            if request.key_type == db19_pb2.UNKNOWN:
                raise Exception("Unknown key type")
            elif request.key_type == db19_pb2.DIAGNOSED:
                key_type = "DIAGNOSED"
            else:
                raise Exception("Unknown key type")

            auth_key = self.generate_authorization_key(api_key, key_type)
            return db19_pb2.TokenResponse(authorization_key=auth_key)
        except Exception as e:
            return db19_pb2.TokenResponse(error=str(e))


if __name__ == '__main__':
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    db19_pb2_grpc.add_DiagnosisDBServicer_to_server(DB19Server(), server)
    server.add_insecure_port('[::]:5000')
    logging.info("Starting server")
    server.start()
    server.wait_for_termination()
