FROM mambaorg/micromamba:1.5.10

ARG RMSX_REPO=https://github.com/AntunesLab/rmsx.git
ARG RMSX_REF=v0.2.3

COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml

RUN micromamba install -y -n base -f /tmp/environment.yml \
    && micromamba clean --all --yes

ENV PATH=/opt/conda/bin:$PATH

RUN set -eux; \
    if git clone --depth 1 --branch "${RMSX_REF}" "${RMSX_REPO}" /tmp/rmsx-src; then \
        :; \
    else \
        rm -rf /tmp/rmsx-src; \
        git clone "${RMSX_REPO}" /tmp/rmsx-src; \
        cd /tmp/rmsx-src; \
        git checkout "${RMSX_REF}"; \
    fi; \
    /opt/conda/bin/pip install --no-cache-dir /tmp/rmsx-src; \
    rm -rf /tmp/rmsx-src

ENV RMSX_NO_CITATION=1

ENTRYPOINT []
CMD ["rmsx", "--help"]
