FROM flink:1.18.1-scala_2.12-java11

USER root

# Instala Python 3 e pip
RUN apt-get update && apt-get install -y python3 python3-pip build-essential libpq-dev
RUN ln -s /usr/bin/python3 /usr/bin/python

# Copia os JARs dos conectores para /opt/flink/lib (NÃO sobrescreve, adiciona)
COPY lib/ /opt/flink/lib/

# Copia o job
COPY SalesAggregationJob.py /opt/flink/usrlib/

# Instala PyFlink
RUN pip3 install apache-flink==1.18.1 psycopg2-binary