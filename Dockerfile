FROM python:3.8

ENV FLASK_APP flaskr
ENV FLASK_ENV development

COPY ./backend /backend
WORKDIR /backend

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 5000

CMD flask run --host=0.0.0.0