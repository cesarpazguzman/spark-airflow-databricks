FROM python:3.9

WORKDIR /mlflow/

ARG MLFLOW_VERSION=1.14.0
RUN mkdir -p /mlflow/ \
  && apt-get update && apt-get -y install --no-install-recommends default-libmysqlclient-dev libpq-dev build-essential \
  && pip install \
    mlflow==$MLFLOW_VERSION \
    sqlalchemy \
    boto3 \
    psycopg2 \
    mysql

EXPOSE 5000

ENV BACKEND_URI /mlflow/store
ENV ARTIFACT_ROOT /mlflow/mlflow-artifacts
CMD echo "Artifact Root is ${ARTIFACT_ROOT}" && \
  mlflow server \
  --backend-store-uri ${BACKEND_URI} \
  --default-artifact-root ${ARTIFACT_ROOT} \
  --host 0.0.0.0