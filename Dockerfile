FROM python:3.9-slim

WORKDIR /app

COPY weatherAppINADEV.py .

RUN pip install requests Flask

CMD [ "python", "./weatherAppINADEV.py" ]

EXPOSE 80
