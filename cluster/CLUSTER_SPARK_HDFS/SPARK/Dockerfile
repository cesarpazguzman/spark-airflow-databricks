FROM bitnami/spark:3-debian-10

USER root
RUN apt-get update && \
    apt-get install -y software-properties-common && \
    apt-get install -y gnupg2 && \
    apt-key adv --keyserver keyserver.ubuntu.com --recv-keys EB9B1D8886F44E2A && \
    add-apt-repository "deb http://security.debian.org/debian-security stretch/updates main" && \ 
    apt-get update && \
    apt-get install -y iputils-ping && \
    apt-get install -y telnet && \ 
    apt-get install -y net-tools && \
    apt-get install -y python3-pip

RUN pip install fbprophet
RUN pip install holidays
RUN pip install pyspark
RUN pip install PyArrow
RUN pip install sklearn
RUN pip install mlflow==1.14.0