FROM yandex/clickhouse-server
RUN sed -i "s/<!-- <access_management>1<\/access_management> -->/<access_management>1<\/access_management>/g" /etc/clickhouse-server/users.xml
