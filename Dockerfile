FROM python:3.8-alpine

COPY requirements.txt /opt/pluto-atomresponder/requirements.txt
ADD gnmvidispine /tmp/gnmvidispine
WORKDIR /opt/pluto-atomresponder
RUN apk add --no-cache alpine-sdk linux-headers openssl-dev libffi-dev mailcap libxml2-dev libxml2 libxslt-dev libxslt postgresql-dev postgresql-libs && \
    pip install -r /tmp/gnmvidispine/requirements.txt && \
    cd /tmp/gnmvidispine && python /tmp/gnmvidispine/setup.py install && cd /opt/pluto-atomresponder && \
    pip install -r requirements.txt uwsgi && \
    rm -rf /tmp/gnmvidispine && \
    apk --no-cache del alpine-sdk linux-headers openssl-dev libffi-dev postgresql-dev libxml2-dev libxslt-dev && \
    rm -rf /root/.cache
COPY *.py /opt/pluto-atomresponder/
ADD --chown=nobody:root atomresponder /opt/pluto-atomresponder/atomresponder/
ADD --chown=nobody:root kinesisresponder /opt/pluto-atomresponder/kinesisresponder/
ADD --chown=nobody:root rabbitmq /opt/pluto-atomresponder/rabbitmq/
ENV PYTHONPATH=/opt/pluto-atomresponder
RUN mkdir static && python manage.py collectstatic --noinput
USER nobody
CMD uwsgi --http :9000 --enable-threads --static-map /static=/opt/pluto-atomresponder/static --static-expires-type application/javascript=3600 -L --module wsgi
