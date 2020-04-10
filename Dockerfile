FROM python:3.6
ENV PRODUCTION_DOCKER=true

USER root

WORKDIR /app

ADD . /app

RUN pip install -r requirements_dashboard.txt
RUN pip install -e .

EXPOSE 8050

CMD ["python", "covid19_data_analyzer/dashboard/index.py"]
