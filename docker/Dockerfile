FROM debian:7.9

MAINTAINER Eric Dill <edill@bnl.gov>

RUN apt-get update && apt-get install -y \
                   autoconf \
                   bzip2 \
                   gcc \
                   git \
                   make \
                   patch \
                   tar \
                   wget

RUN wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh --no-verbose && \
    bash Miniconda3-latest-Linux-x86_64.sh -b -p /opt/conda && rm Miniconda*.sh && \
    export PATH=/opt/conda/bin:$PATH && \
    conda config --set show_channel_urls True && \
    conda config --set always_yes True && \
    conda update --all && conda clean -t -p

ENV PATH /opt/conda/bin:$PATH

ENV LANG en_US.UTF-8