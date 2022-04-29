FROM python:3.8-slim-buster

WORKDIR /app

COPY . .

RUN ls

RUN pip3 install -r requirements.txt

CMD [ "python3", "-m" , "tg_bot"]