import discord
import io
from redbot.core import checks, commands, Config
import re
import aiohttp

IS_LINK_REGEX = re.compile(r"(http(s?):)([/|.|\w|\s|-])*\.(?:png)")

class APNGFilter(getattr(commands, "Cog", object)):
    """Filter those pesky APNG images"""

    def __init__(self, bot):
        self.bot = bot
        default = {"enabled":False}
        self.config = Config.get_conf(self, 435457347654)
        self.config.register_guild(**default)

    @commands.command()
    @checks.mod_or_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def apngfilter(self, ctx):
        """
            Toggle APNG filters on the server
        """
        if await self.config.guild(ctx.guild).enabled():
            await self.config.guild(ctx.guild).enabled.set(False)
            msg = "Disabled"
        else:
            await self.config.guild(ctx.guild).enabled.set(True)
            msg = "Enabled"
        await ctx.send("APNG Filter " + msg)

    async def on_message(self, message):
        if not message.guild:
            return
        if not await self.config.guild(message.guild).enabled():
            return
        channel = message.channel
        if not channel.permissions_for(channel.guild.me).manage_messages:
            return
        is_link = IS_LINK_REGEX.findall(message.content)

        autoimmune = getattr(self.bot, "is_automod_immune", None)
        if autoimmune and await autoimmune(message):
            return

        for attachment in message.attachments:
            print(attachment)
            if attachment.filename.split(".")[-1] not in ("apng", "png"):
                continue  # discord attempts to render by file extension, not mime type
            # keeps requests on the bot's session, prventing a unauthenticated ratelimit for attachments
            temp = io.BytesIO()
            await attachment.save(temp)  
            temp.seek(0)
            # https://stackoverflow.com/questions/4525152/can-i-programmatically-determine-if-a-png-is-animated                    
            if b"acTL" in temp.getvalue():
                await message.delete()
                break
        if is_link:
            for file in IS_LINK_REGEX.finditer(message.content):
                async with aiohttp.ClientSession() as session:
                    async with session.get(file.group()) as file:
                        temp = io.BytesIO()
                        data = await file.read()
                        temp.write(data)
                        temp.seek(0)
                if b"acTL" in temp.getvalue():
                    await message.delete()