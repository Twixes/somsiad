FROM clickhouse/clickhouse-server:22.3
RUN sed -i "s/<!-- <access_management>1<\/access_management> -->/<access_management>1<\/access_management>/g" /etc/clickhouse-server/users.xml
