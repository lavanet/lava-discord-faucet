FROM python:3.10
COPY . /app
WORKDIR /app
RUN pip3 install --default-timeout=1000 -r requirements.txt
CMD [ "python3", "src/discord_faucet_bot.py" ]
