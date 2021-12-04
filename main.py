from ping import ping
import discord
import os
import requests
import json
import sqlite3
import time
from random import randrange
import Levenshtein

client = discord.Client()

## Things to implement
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
  accuracy = Levenshtein.ratio(quote, msg.content) * 100

  raw_data = [char_count, word_count, accuracy, duration]
  results = calculate(char_count, word_count, accuracy, duration)

  if accuracy > 80:
    update_stats(raw_data, msg.author)

  return results

## processes the raw data to create stats
def calculate(char_count, word_count, accuracy, duration):
  cpm = char_count / duration
  sgwpm = cpm / 5
  wpm = word_count / duration

  return [cpm, sgwpm, wpm, accuracy]

## updates the stats of the user upon completing a typing test
def update_stats(stats, tag):
  ## accesses the database and selects the user's stats
  db = sqlite3.connect('main.sqlite')
  cursor = db.cursor()
  cursor.execute("SELECT chars_typed, words_typed, accuracy, total_time, tests_completed FROM main WHERE tag = ?", (str(tag),))
  result = cursor.fetchone()

  ## updates the stats if the user is in the database, otherwise creating a new entry for the user
  if result is None:
    cursor.execute("INSERT INTO main(tag, chars_typed, words_typed, accuracy, total_time, tests_completed) VALUES (?, ?, ?, ?, ?, ?)", (str(tag), stats[0], stats[1], stats[2], stats[3], 1))
  else:
    cursor.execute("UPDATE main SET chars_typed = ?, words_typed = ?, accuracy = ?, total_time = ?, tests_completed = ? WHERE tag = ?", (result[0] + stats[0], result[1] + stats[1], (result[2] * result[4] + stats[2]) / (result[4] + 1), result[3] + stats[3], result[4] + 1, str(tag)))
  db.commit()
  cursor.close()

## print that the bot is ready in console
@client.event
async def on_ready():
  db = sqlite3.connect('main.sqlite')
  cursor = db.cursor()
  cursor.execute('''
    CREATE TABLE IF NOT EXISTS main(
      tag TEXT,
      chars_typed BIGINT,
      words_typed BIGINT,
      accuracy FLOAT,
      total_time FLOAT,
      tests_completed INT
    )
  ''')
  print('Logged in as {0.user}'.format(client))

## message events
@client.event
async def on_message(message):
  if message.author == client.user:
    return

  if message.content.startswith('>quote'):
    ## retrieves and sends a quote
    raw_quote = get_quote()
    while True:
      content = raw_quote['text']
      author = raw_quote['author']
      if not (content is None or author is None):
        break
      raw_quote = get_quote()
    quote = quote_embed(content, author, message.author)
    await message.channel.send(embed=quote)
    start = time.time()

    ## checks whether the user is the one who started the test
    def check_response(m):
      return m.channel == message.channel and m.author == message.author

    ## waits for the user's response and sends their typing test statistics
    response = await client.wait_for('message', check=check_response, timeout=180)

    ## cancels the test if the user says >cancel
    if response.content.startswith('>cancel'):
      await message.channel.send("The test was cancelled.")
      return 0
    
    ## sends the stats
    stat_list = calculate_stats(start, response, content)
    stats = results_embed(stat_list, message.author, "Results")
    await message.channel.send(embed=stats)

  ## sends user stats
  if message.content.startswith('>stats'):
    ## accesses the database and finds the user's stats
    db = sqlite3.connect('main.sqlite')
    cursor = db.cursor()
    cursor.execute("SELECT chars_typed, words_typed, accuracy, total_time FROM main WHERE tag = ?", (str(message.author),))
    result = cursor.fetchone()

    ## sends an embed of the user's stats or sends a message if the user is not in the database yet
    if result is None:
      await message.channel.send("No stats yet! Start a typing test using >quote.")
    else:
      stat_list = calculate(result[0], result[1], result[2], result[3])
      stats = results_embed(stat_list, message.author, "Lifetime Stats")
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
def results_embed(stats, user, title):
  embed = discord.Embed(
    title = title,
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