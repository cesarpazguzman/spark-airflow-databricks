FROM python:3.6-stretch

WORKDIR /app

COPY . .

RUN pip install flask
RUN pip install fbprophet
RUN pip install holidays
RUN pip install pyspark
RUN pip install PyArrow
RUN pip install sklearn
RUN pip install mlflow==1.14.0
RUN pip install Flask-RESTful
RUN pip install joblib
RUN pip install numpy

ENV FLASK_APP app

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0","--port=1080"]


