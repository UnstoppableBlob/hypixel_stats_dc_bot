# ignore this

import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

cringer = 'Cringineer'

bot = commands.Bot(command_prefix='!', intents = intents)


@bot.event
async def on_ready():
    print(f'We are ready to go in, {bot.user.name}')

@bot.event
async def on_member_join(member):
    await member.send(f'Welcome {member.name} to the server!')
    
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if "kevin" in message.content.lower():
        await message.delete()
        await message.channel.send(f'{message.author.mention} Please do not mention Kevin!')

    await bot.process_commands(message)
    
@bot.command()
async def hello(ctx):
    await ctx.send(f'Hello {ctx.author.name}')

@bot.command()
async def assign(ctx):
    role = discord.utils.get(ctx.guild.roles, name=cringer)
    if role:
        await ctx.author.add_roles(role)
        await ctx.send(f'{ctx.author.mention} is now assigned to {cringer}')
    else:
        await ctx.send(f"Role doesn't exist")

@bot.command()
async def unassign(ctx):
    role = discord.utils.get(ctx.guild.roles, name=cringer)
    if role in ctx.author.roles:
        await ctx.author.remove_roles(role)
        await ctx.send(f'{ctx.author.mention} removed the role of {cringer}')
    elif role not in ctx.author.roles:
        await ctx.send(f'{ctx.author.mention} is not assigned to {cringer}')
    else:
        await ctx.send(f"Role doesn't exist")

@bot.command() 
async def dm(ctx, *, msg):
    await ctx.author.send(msg)
    
@bot.command()
async def reply(ctx):
    await ctx.reply("This is a reply to your message!")
        
@bot.command()
@commands.has_role(cringer)
async def admin(ctx):
    await ctx.send("welcome to the admin command")
    
@admin.error
async def admin_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send(f"{ctx.author.mention} doesn't have the role required to use this command. GET OUT!")

bot.run(token, log_handler=handler, log_level=logging.DEBUG)