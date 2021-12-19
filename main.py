from ping import ping
import discord
from discord.ext import commands
import os
import requests
import json
import sqlite3
import time
from random import randrange
import Levenshtein

db = sqlite3.connect('main.sqlite')
cursor = db.cursor()

## Things to implement next:
## - Server/Global Leaderboard
## - Race Against Friends

def get_prefix(client, message):
  try:
    cursor.execute("SELECT prefix FROM prefixes WHERE guild = ?", ("guild" + str(message.guild.id),))
  except:
    return ">"
  prefix = cursor.fetchone()[0]
  
  return prefix

client = commands.Bot(command_prefix = get_prefix, help_command=None)

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
  results = process_data(char_count, word_count, accuracy, duration)

  if accuracy > 80 and char_count > 10:
    update_stats(raw_data, msg.author)

  return results

## processes the raw data to create stats
def process_data(char_count, word_count, accuracy, duration):
  cpm = char_count / duration
  sgwpm = cpm / 5
  wpm = word_count / duration

  return [cpm, sgwpm, wpm, accuracy]

## updates the stats of the user upon completing a typing test
def update_stats(stats, tag):
  ## accesses the database and selects the user's stats
  cursor.execute("SELECT chars_typed, words_typed, accuracy, total_time, tests_completed FROM main WHERE tag = ?", (str(tag),))
  result = cursor.fetchone()

  ## updates the stats if the user is in the database, otherwise creating a new entry for the user
  if result is None:
    cursor.execute("INSERT INTO main (tag, chars_typed, words_typed, accuracy, total_time, tests_completed) VALUES (?, ?, ?, ?, ?, ?)", (str(tag), stats[0], stats[1], stats[2], stats[3], 1))
  else:
    cursor.execute("UPDATE main SET chars_typed = ?, words_typed = ?, accuracy = ?, total_time = ?, tests_completed = ? WHERE tag = ?", (result[0] + stats[0], result[1] + stats[1], (result[2] * result[4] + stats[2]) / (result[4] + 1), result[3] + stats[3], result[4] + 1, str(tag)))
  db.commit()

## print that the bot is ready in console
@client.event
async def on_ready():
  cursor.execute('''
    CREATE TABLE IF NOT EXISTS main(
      tag VARCHAR(64) UNIQUE,
      chars_typed BIGINT,
      words_typed BIGINT,
      accuracy FLOAT,
      total_time FLOAT,
      tests_completed INT
    )
  ''')
  cursor.execute('''
    CREATE TABLE IF NOT EXISTS prefixes(
      guild VARCHAR(64) UNIQUE,
      prefix VARCHAR(64)
    )
  ''')
  print('Logged in as {0.user}'.format(client))

## sets the server's prefix in the SQLite database
@client.event
async def on_guild_join(guild):
  cursor.execute("INSERT INTO prefixes (guild, prefix) VALUES (?, ?)", ("guild" + str(guild.id), ">"))

## changes the server's prefix in the SQLite database
@client.command()
@commands.has_permissions(administrator = True)
async def prefix(ctx, pfx):
  cursor.execute("UPDATE prefixes SET prefix = ? WHERE guild = ?", (pfx, "guild" + str(ctx.guild.id)))
  db.commit()

  await ctx.send("The prefix is now " + pfx)

## sends a list of commands
@client.command()
async def help(ctx):
  commands = help_embed()
  await ctx.channel.send(embed=commands)

## starts a typing test with a quote from our database
@client.command()
async def test(ctx):
  ## formats the quote from the json database
  raw_quote = get_quote()
  while True:
    content = raw_quote['text']
    author = raw_quote['author']
    if not (content is None or author is None):
      break
    raw_quote = get_quote()
  
  await typing(ctx, content, author)

## starts a typing test with a quote that was added from the server
@client.command()
async def quote(ctx):
  ## gets a quote from the server's table in the SQLite database
  store_guild(ctx.guild.id)
  cursor.execute("SELECT id, quote, author FROM guild" + str(ctx.guild.id))
  rows = cursor.fetchall()
  if len(rows) == 0:
    await ctx.channel.send("No quotes have been added from this server! Use >add to add a new quote.")
    return 0
  index = randrange(len(rows))
  content = rows[index][1]
  author = rows[index][2] + ", Quote #" + str(rows[index][0])

  await typing(ctx, content, author)

## starts the typing test
async def typing(ctx, content, author):
  quote = quote_embed(content, author, ctx.author)
  await ctx.channel.send(embed=quote)
  start = time.time()

  ## checks whether the user is the one who started the test
  def check_response(m):
    return m.channel == ctx.channel and m.author == ctx.author

  ## waits for the user's response and sends their typing test statistics
  response = await client.wait_for('message', check=check_response, timeout=180)

  ## cancels the test if the user says >cancel
  if response.content.startswith('>cancel'):
    await ctx.channel.send("The test was cancelled.")
    return 0
  
  ## sends results of the test
  stat_list = calculate_stats(start, response, content)
  stats = results_embed(stat_list, ctx.author, "Results")
  await ctx.channel.send(embed=stats)

## adds a quote to the server's table in the database
@client.command()
async def add(ctx, content, name, exception=None):
  store_guild(ctx.guild.id)

  if exception:
    await ctx.channel.send('Please enter a non-empty quote within quotation marks, followed by the author\'s name in quotation marks (Ex. >add "Hello, world." "Lei Bei")')
    return 0
  cursor.execute("INSERT INTO " + "guild" + str(ctx.guild.id) + " (quote, author) VALUES (?, ?)", (content, name))
  await ctx.channel.send("The quote has been successfully added to the server's list of quotes!")
  db.commit()

## deletes a quote from the server's table in the database
@client.command()
async def delete(ctx, arg):
  id = arg.split(" ")[-1]

  try:
    cursor.execute("DELETE FROM " + "guild" + str(ctx.guild.id) + " WHERE id = ?", (id,))
  except:
    await ctx.channel.send("To delete a quote, use the command >delete, followed by the number of the quote (Ex. >delete 1)")
    return 0
  await ctx.channel.send("The quote has been successfully deleted from the server's list of quotes!")
  db.commit()

## lists the quotes from the server
@client.command()
async def quotes(ctx):
  store_guild(ctx.guild.id)
  cursor.execute("SELECT id, quote, author FROM guild" + str(ctx.guild.id))
  rows = cursor.fetchall()
  if len(rows) == 0:
    await ctx.channel.send("No quotes have been added from this server! Use >add to add a new quote.")
    return 0

  qlist = quotes_embed(rows)

  buttons = [u"\u23EA", u"\u2B05", u"\u27A1", u"\u23E9"]
  current = 0
  msg = await ctx.send(embed=qlist[current])

  for button in buttons:
      await msg.add_reaction(button)
  
  ## edits the embed when the user adds a reaction
  while True:
    try:
      reaction, user = await client.wait_for("reaction_add", check=lambda reaction, user: user == ctx.author and reaction.emoji in buttons, timeout=60.0)
    except:
        return 0
    else:
        previous_page = current
        if reaction.emoji == u"\u23EA":
            current = 0
            
        elif reaction.emoji == u"\u2B05":
            if current > 0:
                current -= 1
                
        elif reaction.emoji == u"\u27A1":
            if current < len(qlist) - 1:
                current += 1

        elif reaction.emoji == u"\u23E9":
            current = len(qlist)-1

        for button in buttons:
            await msg.remove_reaction(button, ctx.author)

        if current != previous_page:
            await msg.edit(embed=qlist[current])

## sends user stats
@client.command()
async def stats(ctx):
  ## accesses the database and finds the user's stats
  cursor.execute("SELECT chars_typed, words_typed, accuracy, total_time FROM main WHERE tag = ?", (str(ctx.author),))
  result = cursor.fetchone()

  ## sends an embed of the user's stats or sends a message if the user is not in the database yet
  if result is None:
    await ctx.channel.send("No stats yet! Start a typing test using >quote.")
  else:
    stat_list = process_data(result[0], result[1], result[2], result[3])
    stats = results_embed(stat_list, ctx.author, "Lifetime Stats")
    await ctx.channel.send(embed=stats)

## manage command errors
@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        pass
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing a required argument. Use the help command!")
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send("I'm missing the required permssions to do that!")
    else:
        print(error) 

## message events
@client.event
async def on_message(message):
  if message.author == client.user:
    return 0

  ## tells the user the bot's prefix when mentioned
  if client.user.mentioned_in(message):
    cursor.execute("SELECT prefix FROM prefixes WHERE guild = ?", ("guild" + str(message.guild.id),))
    prefix = cursor.fetchone()[0]
    await message.channel.send("My prefix is " + prefix)
    return 0

  await client.process_commands(message)

## creates a help embed
def help_embed():
  embed = discord.Embed(
    title = "Commands",
    colour = 0xFFFFFF
  )

  embed.add_field(name="test", value="Starts a typing test with a quote from our database", inline=False)
  embed.add_field(name="quote", value="Starts a typing test with a quote that was added from this server", inline=False)
  embed.add_field(name="cancel", value="Cancels an ongoing typing test", inline=False)
  embed.add_field(name="prefix", value="Changes the prefix (Ex. >prefix !)", inline=False)
  embed.add_field(name="add", value='Add a quote by typing the quote in quotation marks and the author\'s name in another pair of quotation marks (Ex. >add "Hello, world." "Lei Bei")', inline=False)
  embed.add_field(name="delete", value='Delete the quote with the specified number (Ex. >delete 1)', inline=False)
  embed.add_field(name="quotes", value="Lists all the quotes added from this server", inline=False)
  embed.add_field(name="stats", value="Shows your typing stats", inline=False)
  return embed

## creates a quote embed
def quote_embed(content, author, user):
  embed = discord.Embed(
    title = content,
    description = "-" + author,
    colour = 0xFFFFFF
  )

  embed.set_author(name=user.display_name, url=user.avatar_url, icon_url=user.avatar_url)
  return embed

## creates a list of pages for the list of quotes
def quotes_embed(rows):
  embeds = []
  pages = [rows[x:x+8] for x in range(0, len(rows), 8)]
  for pgnum, page in enumerate(pages, start=1):
    embed = discord.Embed(
      title = "Quotes",
      colour = 0xFFFFFF
    )

    for quote in page:
      embed.add_field(name="#" + str(quote[0]), value='"' + quote[1] + '" -' + quote[2], inline=False)
    embed.set_footer(text="Page " + str(pgnum) + " of " + str(len(pages)))
    embeds.append(embed)

  return embeds

## creates an embed of the user's stats
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

## creates a table in the SQLite database if it doesn't exist
def store_guild(guild_id):
  cursor.execute('''
    CREATE TABLE IF NOT EXISTS ''' + "guild" + str(guild_id) + '''(
      id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
      quote VARCHAR,
      author VARCHAR
    )
  ''')

ping()
client.run(os.environ['TOKEN'])