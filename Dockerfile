FROM python:3

WORKDIR /project

COPY requirements.txt ./

COPY . .

CMD [ "python", "./main.py" ]