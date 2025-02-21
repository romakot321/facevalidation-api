FROM python:3.10 AS PackageBuilder
COPY ./requirements.txt ./requirements.txt
RUN apt update && apt install -y cmake
RUN pip3 wheel -r requirements.txt
RUN pip3 wheel gunicorn


FROM python:3.10-slim
EXPOSE 80

# Setup user
ENV UID=2000
ENV GID=2000

RUN groupadd -g "${GID}" python \
  && useradd --create-home --no-log-init --shell /bin/bash -u "${UID}" -g "${GID}" python

RUN apt-get clean && apt-get -y update && apt-get install -y build-essential cmake libopenblas-dev liblapack-dev libopenblas-dev liblapack-dev ffmpeg libsm6 libxext6

USER python
WORKDIR /home/python

RUN mkdir ./wheels
COPY --from=PackageBuilder ./*.whl ./wheels/
RUN pip install --upgrade pip setuptools
RUN pip3 install ./wheels/*.whl --no-warn-script-location

COPY ./ ./

ENV PATH="$PATH:/home/python/.local/bin"
CMD python3 cv.py
