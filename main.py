import discord

import aiohttp
import asyncio
import datetime
import time
import json

from mcrcon import MCRcon, MCRconException

from redbot.core import commands
from redbot.core import checks, Config

from discord.ext import tasks
from discord.ext.commands import has_permissions

def authorcheck(author):
    def msg_check(message):
        if message.author == author:
            return True
        else:
            return False
    return msg_check


def channel_check():
    async def checker(ctx):
        if ctx.channel.id == await ctx.cog.config.guild(ctx.guild).commands_channel():
            return True
    return commands.check(checker)


class MinecraftDiscordCommands(commands.Cog):

    '''
    Simple cog allowing you to access your Minecraft server's console through a discord channel using the command [p]console
    Before using [p]console use [p]mcsetup to set up the cog beforehand
    '''

    __author__ = "Raff"
    __version__ = "1.0"


    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=8008135)
        default_guild = {
            "server_ip": None,
            "rcon_password": None,
            "rcon_port": None,
            "commands_channel": None,
            "setup_complete": False
        }
        self.config.register_guild(
            **default_guild
            )


    @commands.command()
    @commands.has_permissions(administrator=True)
    async def mcsetup(self, ctx):
        ip_confirmed = False
        rcon_password_confirmed = False
        rcon_port_confirmed = False
        channel_confirmed = False


        await ctx.send("**Welcome to Discord-Minecraft!**")
        await ctx.send("You will now be taken through the setup process for this cog.")
        await asyncio.sleep(0.3)
        await ctx.send(".\n.\n.")
        try:
            while ip_confirmed == False:
                await ctx.send("Please enter the IP address of your minecraft server (without port).")
                serverip = await self.bot.wait_for(
                    'message',
                    check=authorcheck(ctx.message.author),
                    timeout=30
                )
                await ctx.send(f"Please double check and ensure `{serverip.content}` is your servers IP address. Have you entered it correctly? y/n")
                ip_check = await self.bot.wait_for(
                    'message',
                    check=authorcheck(ctx.message.author),
                    timeout=30
                )
                if (ip_check.content).lower() == "y":
                    ip_confirmed = True
                    await self.config.guild(ctx.guild).server_ip.set(serverip.content)
                    await ctx.send(f"Successfully set `{serverip.content}` as the server IP.")
                else:
                    ip_confirmed = False

            while rcon_port_confirmed == False:
                await ctx.send(
                    ".\n.\n."
                    )
                await ctx.send("Please enter the RCON port for your server (Default 25575).")
                rconport = await self.bot.wait_for(
                    'message',
                    check=authorcheck(ctx.message.author),
                    timeout=30
                )
                await ctx.send(f"Please double check and ensure `{rconport.content}` is your servers RCON port. Have you entered it correctly? y/n")
                rcon_check = await self.bot.wait_for(
                    'message',
                    check=authorcheck(ctx.message.author),
                    timeout=30
                )
                if (rcon_check.content).lower() == "y":
                    rcon_port_confirmed = True
                    await self.config.guild(ctx.guild).rcon_port.set(int(rconport.content))
                    await ctx.send(f"Successfully set `{rconport.content}` as the server RCON port.")
                else:
                    rcon_port_confirmed = False

            while rcon_password_confirmed == False:
                await ctx.send(".\n.\n.")
                await ctx.send("Please enter the RCON password for your server.")
                rconpassword = await self.bot.wait_for(
                    'message',
                    check=authorcheck(ctx.message.author),
                    timeout=30
                )
                rconpassword_temp = rconpassword
                await rconpassword.delete()
                await ctx.send(f"Please double check and ensure ||{rconpassword_temp.content}|| is your servers RCON password. Have you entered it correctly? y/n")
                rcon_pass_check = await self.bot.wait_for('message',
                check=authorcheck(ctx.message.author),
                timeout=30
                )
                if (rcon_pass_check.content).lower() == "y":
                    rcon_password_confirmed = True
                    await self.config.guild(ctx.guild).rcon_password.set(
                        rconpassword_temp.content
                    )
                    await ctx.send(f"Successfully set ||{rconpassword_temp.content}|| as the server RCON password.")
                else:
                    rcon_password_confirmed = False


            await ctx.send(".\n.\n.")
            await ctx.send("Attempting to connect to server")
            await ctx.send(".\n.\n.")

            try:
                with MCRcon(
                    str(await self.config.guild(
                        ctx.guild
                    ).server_ip()),
                    str(await self.config.guild(
                        ctx.guild
                    ).rcon_password()),
                    int(await self.config.guild(
                        ctx.guild
                    ).rcon_port()))\
                            as mcr:
                    
                    mcr.command("say TEST COMMAND WITH MINECRAFT-DISCORD COMMANDS")
                    await ctx.send(f"Successfully connected to server!")

                while channel_confirmed == False:
                    await ctx.send(".\n.\n.")
                    await ctx.send("Please enter the channel ID of the channel you wish to write commands in.")
                    channelid = await self.bot.wait_for(
                        'message',
                        check=authorcheck(
                            ctx.message.author
                            ),
                        timeout=30
                    )
                    await ctx.send(f"Please double check and ensure `{channelid.content}` is the correct channel ID. Have you entered it correctly? y/n")
                    channel_check = await self.bot.wait_for(
                        'message',
                        check=authorcheck(
                            ctx.message.author
                            ),
                        timeout=30
                    )
                    if (channel_check.content).lower() == "y":
                        channel_confirmed = True
                        await self.config.guild(ctx.guild).commands_channel.set(int(channelid.content))
                        await ctx.send(f"Successfully set `{channelid.content}` as the commands channel ID.")
                    else:
                        channel_confirmed = False


                    await ctx.send(".\n.\n.")
                    await ctx.send(f"Setup complete! You can now use `{ctx.prefix}console` in <#{channelid.content}> to communicate with your Minecraft server's console.")
                    await self.config.guild(ctx.guild).setup_complete.set(True)
            except (ConnectionRefusedError, TimeoutError, MCRconException) as e:
                await ctx.send(f"Connection failed with error ```{e}``` Please try again using `{ctx.prefix}mcsetup`")

        except asyncio.TimeoutError:
            await ctx.send(f"{ctx.message.author.mention} You did not respond in time. To continue with your setup type `{ctx.prefix}mcsetup`")


    @commands.command()
    @channel_check()
    async def console(
        self,
        ctx,
        command: str,
        *,
        values = None
    ):
        if await self.config.guild(ctx.guild).setup_complete() == True:
            try:
                with MCRcon(
                    str(await self.config.guild(ctx.guild).server_ip()),
                    str(await self.config.guild(ctx.guild).rcon_password()),
                    int(await self.config.guild(ctx.guild).rcon_port())) as mcr:

                    if values != None:
                        returned = mcr.command(f"{command} {values}")
                        await ctx.send(
                            f"**Executed Command:** `/{command} {values}`")
                        await ctx.send(
                            f"**Returned:** {returned}")
                    else:
                        returned = mcr.command(f"{command}")
                        await ctx.send(
                            f"**Executed Command:** `/{command}`")
                        await ctx.send(
                            f"**Returned:** {returned}")
            except (ConnectionRefusedError, TimeoutError, MCRconException) as e:
                await ctx.send(f"Connection failed with error ```{e}``` The server may be down/restarting please try again in a couple of minutes.\nIf not, make sure that your details to connect to the server again are correct. You may want to run the [p]mcsetup process again.")
        else:
            await ctx.send(f"Please complete setup using `{ctx.prefix}mcsetup` before using this command")
