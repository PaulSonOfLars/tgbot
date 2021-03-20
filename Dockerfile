FROM python:3.8

COPY . .

RUN pip3 install -r requirements.txt

CMD [ "python3", "-m" , "tg_bot"]
