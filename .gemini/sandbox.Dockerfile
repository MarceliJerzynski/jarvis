# Wlasna baza (Node LTS na Debianie), zamiast polegac na niepewnym/zmiennym
# adresie oficjalnego obrazu sandboxa gemini-cli.
FROM node:22-bookworm

# Java + Maven
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget apt-transport-https gnupg \
    && wget -O - https://packages.adoptium.net/artifactory/api/gpg/key/public | gpg --dearmor -o /usr/share/keyrings/adoptium.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/adoptium.gpg] https://packages.adoptium.net/artifactory/deb $(awk -F= '/^VERSION_CODENAME/{print$2}' /etc/os-release) main" > /etc/apt/sources.list.d/adoptium.list \
    && apt-get update && apt-get install -y --no-install-recommends temurin-25-jdk git \
    && rm -rf /var/lib/apt/lists/*

# Pobranie i instalacja Maven 3.9.16
RUN wget -q https://archive.apache.org/dist/maven/maven-3/3.9.16/binaries/apache-maven-3.9.16-bin.tar.gz \
    && tar -xzf apache-maven-3.9.16-bin.tar.gz -C /opt \
    && ln -s /opt/apache-maven-3.9.16 /opt/maven \
    && rm apache-maven-3.9.16-bin.tar.gz

ENV JAVA_HOME=/usr/lib/jvm/temurin-25-jdk-amd64
ENV MAVEN_HOME=/opt/maven
ENV PATH="${JAVA_HOME}/bin:${MAVEN_HOME}/bin:${PATH}"

# Instalujemy gemini-cli tak samo jak Ty to zrobiles lokalnie (npm)
RUN npm install -g @google/gemini-cli

# Copy uv and uvx binaries from the official Astral image for fast Python package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Tworzymy nie-rootowego usera (bezpieczniejsze, i zgodne z tym co robil oficjalny obraz)
RUN useradd -m -s /bin/bash node-user || true
USER node-user
WORKDIR /home/node-user

# Konfiguracja bezpiecznego katalogu w gicie, aby zapobiec "dubious ownership" dla zamontowanych repozytoriów
RUN git config --global --add safe.directory '*' \
    && git config --global http.sslVerify false \
    && git config --global credential.helper 'store --file=/home/node-user/.gemini/.git-credentials' \
    && git config --global user.name "mjerzynski" \
    && git config --global user.email "mjerzynski@psi.pl"
