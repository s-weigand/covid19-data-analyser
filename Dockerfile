FROM python:3.6
ENV PRODUCTION_DOCKER=true

USER root

WORKDIR /app

ADD . /app

RUN pip install -r requirements_dashboard.txt

EXPOSE 8050

CMD ["python", "dashboard.py"]
