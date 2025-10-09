# Build a very thin wrapper around the official MQ image
FROM icr.io/ibm-messaging/mq:latest

# Put your assets somewhere that won't mask IBM's /etc/mqm
COPY init/common.mqsc.tpl /opt/mq-init/common.mqsc.tpl
COPY init/render-mqsc.sh   /usr/local/bin/render-mqsc.sh

# Make sure the script is executable
RUN chmod +x /usr/local/bin/render-mqsc.sh
