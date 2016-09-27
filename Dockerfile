FROM alpine:3.4

ENV PYTHONUNBUFFERED=1

RUN set -x \
    && apk add --no-cache --virtual .run-deps \
        python3 \
    && apk add --no-cache --virtual .build-deps \
        python3-dev \
        musl-dev \
        gcc \
    && pip3 install \
        python-dateutil \
        gevent flask \
        flask-bootstrap \
        flask-basicauth \
        flask-restful \
        pyyaml \
        requests \
    && : "---------- remove build deps ----------" \
    && apk del .build-deps \
    && mkdir /hud \
    && mkdir /hud/templates \
    && mkdir /hud/sensors \
    && mkdir /hud/work


COPY *.py /hud
COPY templates/ /hud/templates/
COPY sensors/ /hud/sensors/

VOLUME /hud/work
WORKDIR /hud/work

CMD ["python3", "/im/srv.py"]
