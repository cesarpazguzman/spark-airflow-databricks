FROM hdfs-base
ENV HADOOP_CONF_DIR=/etc/hadoop
COPY run.sh /run.sh
RUN chmod a+x run.sh

EXPOSE 9000 9870 22 

ENTRYPOINT ["sh", "-c", "service ssh restart; ./run.sh; sleep infinity"]