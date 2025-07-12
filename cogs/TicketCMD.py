import discord
from discord.ext import commands
from cogs.TicketSystem import MenuButton, TicketCloseButton
import json

class TicketCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_application_command_error(self, ctx, error):
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.send("**Commands are not allowed in private messages!**")
        elif isinstance(error, commands.CheckFailure):
            pass  
        else:
            print(f"Unhandled error: {error}")

    @commands.slash_command(name="menu", description="Open Ticket System Menu")
    @commands.has_permissions(administrator=True)
    async def menu(self, ctx):
        menu = discord.Embed(title="Ticket System Menu", description="Click the button below to open a ticket.", color=discord.Color.blue())
        menu.set_author(name=self.bot.user.name, icon_url=self.bot.user.display_avatar.url)
        menu.set_footer(text="Created by Yi3849")
        with open("./data/config.json", "r") as file:
            data = json.load(file)
            guild_id = str(ctx.guild.id)
            if guild_id not in data:
                data[guild_id] = {
                    "ticket_channel_id": None,
                    "ticket_channel_name": None,
                    "ticket_category_id": None,
                    "ticket_category_name": None,
                }
                with open("./data/config.json", "w") as file:
                    json.dump(data, file, indent=4)
        await ctx.respond(embed=menu, view=MenuButton())

    @commands.slash_command(name="close", description="Close the current ticket")
    @commands.has_permissions(manage_channels=True)
    async def close(self, ctx):
        if isinstance(ctx.channel, discord.TextChannel) and ctx.channel.name.startswith("ticket-"):
            closeEmbed = discord.Embed(title="Close Ticket", description="Are you sure you want to close this ticket?", color=discord.Color.red())
            await ctx.respond(embed=closeEmbed, view=TicketCloseButton())
        else:
            await ctx.respond("This command can only be used in a ticket channel.", ephemeral=True)

    @commands.slash_command(name="help", description="Get help with the Ticket System")
    async def help(self, ctx):
        helpEmbed = discord.Embed(title="Ticket System Help", description="Here are the commands you can use:", color=discord.Color.green())
        helpEmbed.add_field(name="/menu", value="Open the Ticket System Menu.", inline=False)
        helpEmbed.add_field(name="/close", value="Close the current ticket.", inline=False)
        helpEmbed.set_footer(text="Created by Yi3849")
        await ctx.respond(embed=helpEmbed)
    
    @commands.slash_command(name="ping", description="Check the bot's latency")
    async def ping(self, ctx):
        latency = round(self.bot.latency * 1000)
        pingEmbed = discord.Embed(title="Pong!", description=f"Latency: {latency} ms", color=discord.Color.green())
        await ctx.respond(embed=pingEmbed)

def setup(bot):
    bot.add_cog(TicketCMD(bot))