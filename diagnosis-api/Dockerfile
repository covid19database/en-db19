FROM python:3.8-slim-buster

# ENV FLASK_APP /opt/app.py
# ENV FLASK_RUN_HOST 0.0.0.0

ADD requirements.txt /opt/requirements.txt
RUN pip install -r /opt/requirements.txt

ADD app.py /opt/app.py
ADD util.py /opt/util.py
ADD db19_pb2_grpc.py /opt/db19_pb2_grpc.py
ADD db19_pb2.py /opt/db19_pb2.py

WORKDIR /opt

CMD ["python", "app.py"]
