# =======================================================
# First stage: Build and install loxprox and dependencies
# =======================================================
FROM python:3.11-alpine as builder

# Install build dependencies
RUN apk add --no-cache --virtual .build-deps \
    build-base \
    python3-dev

# Copy the source code to the container
COPY . /tmp/loxprox

# Install loxprox and its dependencies
RUN pip install --prefix=/install /tmp/loxprox

# Cleanup
RUN apk del .build-deps

# =======================================================
# Second stage: Create the final image
# =======================================================
FROM python:3.11-alpine

# Copy installed package from the first stage
COPY --from=builder /install /usr/local

# Install supervisord and other runtime dependencies
RUN apk add --no-cache supervisor

# Copy default loxprox-supervisor.ini
COPY config.in/loxprox-supervisor.ini /opt/nivos/loxprox/loxprox-supervisor.ini

# Create a symbolic link to loxprox-supervisor.ini
RUN mkdir /etc/supervisor.d
RUN ln -s /opt/nivos/loxprox/loxprox-supervisor.ini /etc/supervisor.d/loxprox-supervisor.ini

# Create directories for configuration and logs
RUN mkdir -p /opt/nivos/loxprox/log

# Expose the UDP port for control server
EXPOSE 52001/udp

# Expose the Supervisor web interface
EXPOSE 52080

# Debug
#CMD ["/bin/sh"]

# Run supervisord
CMD ["/usr/bin/supervisord","--nodaemon","--configuration","/etc/supervisord.conf"]
