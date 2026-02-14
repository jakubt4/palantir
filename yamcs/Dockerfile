# Project Palantir - Ground Segment
FROM yamcs/example-simulation:5.12.2

# Inject strict server and instance configurations
COPY etc/yamcs.yaml /opt/yamcs/etc/yamcs.yaml
COPY etc/yamcs.palantir.yaml /opt/yamcs/etc/yamcs.palantir.yaml
COPY etc/processor.yaml /opt/yamcs/etc/processor.yaml

# Inject the XTCE Mission Database
COPY mdb/palantir.xml /opt/yamcs/mdb/palantir.xml

EXPOSE 8090
