FROM python:3.8-slim

RUN useradd --create-home afini

WORKDIR /home/afini/
RUN apt update \
 && apt install -y gcc \
 && apt install -y libmariadbclient-dev \
 && apt install -y sudo \
 && python3 -m pip install pipenv \
 && rm -rf /var/lib/apt/lists/*

RUN echo "\nafini ALL=(ALL) NOPASSWD: ALL\n" | tee -a /etc/sudoers

USER afini
COPY --chown=afini Pipfile.lock /home/afini/
RUN  pipenv sync
COPY --chown=afini . /home/afini/
RUN  rm .env*

ENTRYPOINT ["./entrypoint.sh"]
