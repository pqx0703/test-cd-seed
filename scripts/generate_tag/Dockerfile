FROM jfloff/alpine-python
RUN pip install semver
RUN pip install pyyaml
RUN pip install requests

COPY ./mars/mars /bin/mars

CMD ["ajenti-panel"]
