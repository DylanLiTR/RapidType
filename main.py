from ping import ping
import discord
import os
import requests
import json
import time
from random import randrange

client = discord.Client()

## Things to implement
##    * take next message of user and calculate cpm/wpm
##    * check accuracy of message compared to quote
##    * styling the quote + cancel reaction
##    * allow the user to add their own tests

## get quote from API
def get_quote():
  response = requests.get("https://type.fit/api/quotes")
  json_data = json.loads(response.text)
  index = randrange(1644)
  quote = json_data[index]['text']
  author = json_data[index]['author']
  output = quote + " -" + author
  return(output)

## calculates CPM, WPM, and accuracy
def calculate_stats(start, msg):
  end = time.time()
  char_count = len(msg.content)
  words = msg.content.split()
  word_count = len(words)

  duration = (end - start) / 60
  cpm = char_count / duration
  wpm = word_count / duration
  return wpm

## print that the bot is ready in console
@client.event
async def on_ready():
  print('We have logged in as {0.user}'.format(client))

## message events
@client.event
async def on_message(message):
  if message.author == client.user:
    return

  if message.content.startswith('>quote'):
    quote = get_quote()
    await message.channel.send(quote)
    start = time.time()

    ## checks whether the user is the one who started the test
    def check_response(msg):
      return msg.channel == message.channel and msg.author == message.author

    msg = await client.wait_for('message', check=check_response, timeout=180)
    wpm = calculate_stats(start, msg)
    await message.channel.send("Your WPM was: %.2f" % wpm)

ping()
client.run(os.environ['TOKEN'])