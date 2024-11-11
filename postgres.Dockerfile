FROM pgvector/pgvector:pg16

# Variables needed at runtime to configure postgres and run the initdb scripts
ENV POSTGRES_DB ''
ENV POSTGRES_USER ''
ENV POSTGRES_PASSWORD ''

# Copy in the load-extensions script
COPY load-extensions.sh /docker-entrypoint-initdb.d/
