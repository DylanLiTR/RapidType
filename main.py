from ping import ping
import discord
import os
import requests
import json
import time
from random import randrange
import Levenshtein

client = discord.Client()

## Things to implement
##    * styling the quote + cancel reaction
##    * allow the user to add their own tests

## get quote from API
def get_quote():
  response = requests.get("https://type.fit/api/quotes")
  index = randrange(1643)
  raw_quote = json.loads(response.text)[index]
  return raw_quote

## calculates CPM, WPM, and accuracy
def calculate_stats(start, msg, quote):
  end = time.time()
  char_count = len(msg.content)
  words = msg.content.split()
  word_count = len(words)

  duration = (end - start) / 60
  cpm = char_count / duration
  sgwpm = cpm / 5
  wpm = word_count / duration
  accuracy = Levenshtein.ratio(quote, msg.content) * 100
  stats = [cpm, sgwpm, wpm, accuracy]
  return stats

## print that the bot is ready in console
@client.event
async def on_ready():
  print('Logged in as {0.user}'.format(client))

## message events
@client.event
async def on_message(message):
  if message.author == client.user:
    return

  if message.content.startswith('>quote'):
    ## retrieves and sends a quote
    raw_quote = get_quote()
    content = raw_quote['text']
    author = raw_quote['author']
    quote = quote_embed(content, author, message.author)
    await message.channel.send(embed=quote)
    start = time.time()

    ## checks whether the user is the one who started the test
    def check_response(msg):
      return msg.channel == message.channel and msg.author == message.author

    ## waits for the user's response and sends their typing test statistics
    msg = await client.wait_for('message', check=check_response, timeout=180)
    stat_list = calculate_stats(start, msg, content)
    stats = stats_embed(stat_list, message.author)
    await message.channel.send(embed=stats)

## creates a quote embed
def quote_embed(content, author, user):
  embed = discord.Embed(
    title = content,
    description = "-" + author,
    colour = 0xFFFFFF
  )

  embed.set_author(name=user.display_name, url=user.avatar_url, icon_url=user.avatar_url)
  return embed

## creates a quote embed
def stats_embed(stats, user):
  embed = discord.Embed(
    title = "Stats",
    colour = 0xFFFFFF
  )

  embed.set_author(name=user.display_name, url=user.avatar_url, icon_url=user.avatar_url)

  embed.add_field(name="CPM", value="{0:.02f}".format(stats[0]), inline=True)
  embed.add_field(name="Standard WPM", value="{0:.02f}".format(stats[1]), inline=True)
  embed.add_field(name="Actual WPM", value="{0:.02f}".format(stats[2]), inline=True)

  embed.add_field(name="Accuracy", value="{0:.02f}%".format(stats[3]), inline=True)
  embed.add_field(name="ㅤ", value="ㅤ", inline=True)
  embed.add_field(name="ㅤ", value="ㅤ", inline=True)
  return embed

ping()
client.run(os.environ['TOKEN'])