import db19_pb2_grpc
import db19_pb2
import grpc
import base64
from util import generate_random_tek

channel = grpc.insecure_channel('localhost:5000')
stub = db19_pb2_grpc.DiagnosisDBStub(channel)

tek, enin = generate_random_tek()
authority_b64 = '2iUNf7/8pjS/mzjpQwUIuw=='
authority = base64.decodebytes(bytes(authority_b64, 'utf8'))

resp = stub.AddReport(db19_pb2.Report(
    authority=authority,
    reports=[
        db19_pb2.TimestampedTEK(
            TEK=tek,
            ENIN=enin
        )
    ]
))
print(resp)

resp = stub.GetDiagnosisKeys(db19_pb2.GetKeyRequest())
for r in resp:
    print(type(r), r)
