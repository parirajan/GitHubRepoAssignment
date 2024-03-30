# Dockerfile
FROM registry.access.redhat.com/ubi8/ubi:8.4

# Install Docker
RUN dnf install -y dnf-plugins-core \
    && dnf config-manager --add-repo=https://download.docker.com/linux/centos/docker-ce.repo \
    && dnf install -y docker-ce docker-ce-cli containerd.io --nobest \
    && dnf clean all

# Verify Docker installation
RUN docker --version

# Any additional setup here
