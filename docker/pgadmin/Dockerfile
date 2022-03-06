FROM dpage/pgadmin4

COPY config/servers.json /pgadmin4/servers.json
COPY sql/ /var/lib/pgadmin/storage/ing.jlllopezp_gmail.com/

# the following commands are used for debug purposes only
USER root
RUN apk add bash curl jq vim