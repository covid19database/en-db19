from flask import Flask, json, request
from jsonschema import validate
import time
import logging
import base64
from datetime import datetime
import psycopg2
import psycopg2.extras
from util import encodeb64, dt_to_enin
logging.basicConfig(level=logging.INFO)

app = Flask(__name__, static_url_path='')
while True:
    try:
        conn = psycopg2.connect("dbname=covid19 user=covid19 port=5432\
                                 password=covid19databasepassword \
                                 host=diagnosis-db")
        # psycopg2.extras.register_hstore(conn)
        break
    except psycopg2.OperationalError:
        logging.info("Could not connect to DB; retrying...")
        time.sleep(1)
        continue


report_schema = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        # health authority opaque key
        "authority": {"type": "string"},
        # reports from user
        "reports": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "TEK": {"type": "string"},
                    "ENIN": {"type": "integer"}
                }
            }
        },
        "metadata": {"type": "object"}
    }
}


def check_authority(hak):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM health_authorities WHERE HAK=%s", (hak,))
        return cur.fetchone() is not None


def insert_report(reports):
    with conn.cursor() as cur:
        ins = "INSERT INTO reported_keys(TEK, ENIN, HAK) VALUES (%s, %s, %s)"
        cur.executemany(ins, reports)
        conn.commit()


@app.route('/add-report', methods=['POST'])
def add_report():
    try:
        datum = request.get_json(force=True)
        validate(datum, schema=report_schema)

        # TODO: check validity of authority
        authority_key = base64.decodebytes(bytes(datum['authority'], 'utf8'))
        if len(authority_key) != 16:
            raise Exception("Invalid authority length")
        if not check_authority(authority_key):
            raise Exception("Invalid authority value")

        to_insert = []
        logging.info(f"validating reports: {len(datum['reports'])}")
        for report in datum['reports']:
            tek = base64.decodebytes(bytes(report['TEK'], 'utf8'))
            if len(tek) != 16:
                raise Exception("Invalid TEK")
            timestamp = datetime.utcfromtimestamp(int(report['ENIN']) * 600)
            to_insert.append((tek, timestamp, authority_key))
        logging.info(f"inserting reports: {len(to_insert)}")
        insert_report(to_insert)
        return json.jsonify({}), 200
    except Exception as e:
        logging.error(e)
        return json.jsonify({'error': str(e)}), 500


@app.route('/get-diagnosis-keys', methods=['GET'])
def get_diagnosis_keys():
    result = []
    with conn.cursor() as cur:
        cur.execute("SELECT TEK, ENIN FROM reported_keys")
        for row in cur:
            tek_b, enin_ts = row
            tek = encodeb64(bytes(tek_b))
            enin = dt_to_enin(enin_ts)
            result.append({'TEK': tek, 'ENIN': enin})
    return json.jsonify(result), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port='8080', debug=True)
