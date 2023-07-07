FROM highcanfly/pretix:latest

COPY . /pretix-sumup
RUN cd /pretix-sumup && python setup.py develop

VOLUME ["/etc/pretix", "/data"]
EXPOSE 80
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["all"]
