import discord
from discord.ext import commands
import json
from bs4 import BeautifulSoup
import os

class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(TicketButton())
        self.bot.add_view(MenuButton())
        self.bot.add_view(TicketCloseButton())

    @commands.Cog.listener()
    async def on_application_command_error(self, ctx, error):
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.send("**Commands are not allowed in private messages!**")
        elif isinstance(error, commands.CheckFailure):
            pass  
        else:
            print(f"Unhandled error: {error}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if isinstance(message.channel, discord.DMChannel):
            return
        if message.author.bot:
            return
        guild_id_str = str(message.guild.id)
        channel_id = message.channel.id

        with open("./data/config.json", "r") as file:
            data = json.load(file)

        if guild_id_str not in data:
            return
        if "workingTicket" not in data[guild_id_str]:
            return

        working_ticket = data[guild_id_str]["workingTicket"]

        for user_id_str, channels in working_ticket.items():
            if channel_id in channels:
                with open(f"./data/ChatHistory/{channel_id}.json", "r") as chat_file:
                    chat_data = json.load(chat_file)

                content = message.content
                if not content:
                    if message.attachments:
                        content = "[Attachment] " + ", ".join([a.url for a in message.attachments])
                    elif message.embeds:
                        content = "[Embed] (We will try to show it in the future)"
                    elif message.stickers:
                        content = "[Sticker] (We will try to show it in the future)"
                    else:
                        content = "[Unknown content]"

                chat_data[str(message.id)] = {
                    "author": message.author.display_name,
                    "content": content,
                    "timestamp": message.created_at.strftime('%Y-%m-%d %H:%M')
                }

                with open(f"./data/ChatHistory/{channel_id}.json", "w") as chat_file:
                    json.dump(chat_data, chat_file, indent=4)
                break

def update_html_with_chat(channel_id):
    history = f"./data/ChatHistory/{channel_id}.json"
    html_path = f"./data/ChatHistoryHTML/{channel_id}.html"

    with open(history, "r", encoding="utf-8") as file:
        chat_data = json.load(file)

    with open("././index.html", "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "html.parser")

    chat_log_div = soup.find("div", {"id": "chat-area"})
    if not chat_log_div:
        return

    chat_log_div.clear()

    for msg_id in sorted(chat_data):
        author = chat_data[msg_id]["author"]
        timestamp = chat_data[msg_id]["timestamp"]
        content = chat_data[msg_id]["content"]

        msg_block = soup.new_tag("div", attrs={"class": "message"})

        avatar_div = soup.new_tag("div", attrs={"class": "message-avatar"})
        avatar_div.string = author
        msg_block.append(avatar_div)

        content_div = soup.new_tag("div", attrs={"class": "message-content"})

        header_div = soup.new_tag("div", attrs={"class": "message-header"})

        author_div = soup.new_tag("div", attrs={"class": "message-author"})
        author_div.string = author
        header_div.append(author_div)

        timestamp_div = soup.new_tag("div", attrs={"class": "message-timestamp"})
        timestamp_div.string = timestamp
        header_div.append(timestamp_div)

        content_div.append(header_div)

        text_div = soup.new_tag("div", attrs={"class": "message-text"})
        text_div.string = content
        content_div.append(text_div)

        msg_block.append(content_div)

        chat_log_div.append(msg_block)

    with open(html_path, "w", encoding="utf-8") as file:
        file.write(str(soup))

class ChannelSelectView(discord.ui.View):
    def __init__(self, channels):
        super().__init__()
        self.add_item(ChannelSelect(channels))

class CategorySelectView(discord.ui.View):
    def __init__(self, categories):
        super().__init__()
        self.add_item(CategorySelect(categories))

class SystemConfigSelectView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction):
        super().__init__()
        self.add_item(SystemConfigSelect(interaction))
        
    @discord.ui.button(label="Return to Menu", style=discord.ButtonStyle.secondary, custom_id="return_to_menu")
    async def return_to_menu(self, button: discord.ui.Button, interaction: discord.Interaction):
        menu = discord.Embed(
            title="Ticket System Menu",
            description="Click the button below to open a ticket.",
            color=discord.Color.blue()
        )
        menu.set_author(name=interaction.client.user.name, icon_url=interaction.client.user.display_avatar.url)
        menu.set_footer(text="Created by Yi3849")
        await interaction.response.edit_message(embed=menu, view=MenuButton())

class EmbedSetupModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Ticket System Embed Setup")

        self.add_item(discord.ui.InputText(label="Embed Title", placeholder="Enter the embed title"))
        self.add_item(discord.ui.InputText(label="Embed Description", placeholder="Enter the embed description", style=discord.InputTextStyle.long))

    async def callback(self, interaction: discord.Interaction):
        title = self.children[0].value
        description = self.children[1].value

        with open("./data/config.json", "r") as file:
            data = json.load(file)
            data[str(interaction.guild.id)]["embed_title"] = title
            data[str(interaction.guild.id)]["embed_description"] = description
        with open("./data/config.json", "w") as file:
            json.dump(data, file, indent=4)
        success = discord.Embed(title="Embed Setup", description="Embed setup completed successfully.", color=discord.Color.green())
        success.add_field(name="Title", value=title, inline=False)
        success.add_field(name="Description", value=description, inline=False)
        await interaction.response.edit_message(embed=success, view=MenuButton())

class TicketCloseButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket", emoji="🔒")
    async def CT_callback(self, button, interaction):
        channel = interaction.channel
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)

        with open("./data/config.json", "r") as file:
            data = json.load(file)

        config = data[guild_id]
        working_tickets = config.get("workingTicket", {})

        ticket_owner_id = None
        for uid, channels in working_tickets.items():
            if channel.id in channels:
                ticket_owner_id = uid
                break

        permissions = channel.permissions_for(interaction.user)
        is_admin = permissions.manage_channels
        is_owner = user_id == ticket_owner_id
        user_can_close = config.get("user_can_close_ticket", False)

        if not is_admin:
            if not is_owner or not user_can_close:
                await interaction.response.send_message("You do not have permission to close this ticket.", ephemeral=True)
                return
        if ticket_owner_id is None or channel.id not in working_tickets[ticket_owner_id]:
            await interaction.response.send_message("This ticket is not created by our system.", ephemeral=True)
            return
        if ticket_owner_id and channel.id in working_tickets[ticket_owner_id]:
            working_tickets[ticket_owner_id].remove(channel.id)
            if not working_tickets[ticket_owner_id]:
                del working_tickets[ticket_owner_id]

        with open("./data/config.json", "w") as file:
            json.dump(data, file, indent=4)

        update_html_with_chat(channel.id)
        file1 = discord.File(f"./data/ChatHistoryHTML/{channel.id}.html", filename=f"ChatHistory-{channel.id}.html")
        file2 = discord.File(f"./data/ChatHistory/{channel.id}.json", filename=f"ChatHistory-{channel.id}.json")
        user = await interaction.client.fetch_user(int(ticket_owner_id))

        if config.get("send_to_user_chat_history", False):
            await user.send("Your ticket has been closed. You can view the chat history here:", files=[file1, file2])

        os.remove(f"./data/ChatHistoryHTML/{channel.id}.html")
        os.remove(f"./data/ChatHistory/{channel.id}.json")
        await channel.delete()

class TicketButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Create Ticket", style=discord.ButtonStyle.primary, custom_id="create_ticket", emoji="🎫")
    async def CT_callback(self, button, interaction):
        with open("./data/config.json", "r") as file:
            data = json.load(file)
            if data[str(interaction.guild.id)]["status"] != "active":
                await interaction.response.send_message("Ticket system is not active.", ephemeral=True)
                return
            try:
                category = interaction.guild.get_channel(data[str(interaction.guild.id)]["ticket_category_id"])
                overwrites = {
                    interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False),
                    interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                }
                channel = await interaction.guild.create_text_channel(
                    name=f"Ticket-{interaction.user.name}",
                    category=category,
                    topic=f"Ticket created by {interaction.user.name} ({interaction.user.id})",
                    overwrites=overwrites
                )
                channelEmbed = discord.Embed(title=f"Ticket-{interaction.user.name}", description=f"{interaction.user.mention} Please describe your issue and wait!", color=discord.Color.green())
                with open(f"./data/ChatHistory/{channel.id}.json", "w") as chat_file:
                    chat_data = {}
                    json.dump(chat_data, chat_file, indent=4)
                if "workingTicket" not in data[str(interaction.guild.id)]:
                    data[str(interaction.guild.id)]["workingTicket"] = {}
                if str(interaction.user.id) not in data[str(interaction.guild.id)]["workingTicket"]:
                    data[str(interaction.guild.id)]["workingTicket"][str(interaction.user.id)] = []
                data[str(interaction.guild.id)]["workingTicket"][str(interaction.user.id)].append(channel.id)
                with open("./data/config.json", "w") as file:
                    json.dump(data, file, indent=4)
                await channel.send(embed=channelEmbed, view=TicketCloseButton())
                await interaction.response.send_message(f"Ticket created: {channel.mention}", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)
                return

class MenuButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Setup Ticket Channel", style=discord.ButtonStyle.primary, custom_id="setup_ticket_channel")
    async def STCh_callback(self, button, interaction):
        try:
            STCh = discord.Embed(title="Ticket Channel Setup", description="Please select a channel:", color=discord.Color.green())
            channels = [ch for ch in interaction.guild.text_channels]
            view = ChannelSelectView(channels)
            await interaction.response.edit_message(embed=STCh, view=view)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)
            return
    @discord.ui.button(label="Setup Ticket Category", style=discord.ButtonStyle.primary, custom_id="setup_ticket_category")
    async def STCa_callback(self, button, interaction):
        try:
            STCa = discord.Embed(title="Ticket Category Setup", description="Please select a category:", color=discord.Color.green())
            categories = [cat for cat in interaction.guild.categories]
            view = CategorySelectView(categories)
            await interaction.response.edit_message(embed=STCa, view=view)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)
            return
    @discord.ui.button(label="Delete Ticket Channel Setup", style=discord.ButtonStyle.danger, custom_id="delete_ticket_channel_setup", row=1)
    async def DTCh_callback(self, button, interaction):
        try:
            with open("./data/config.json", "r") as file:
                data = json.load(file)
                guild_id = str(interaction.guild.id)
                if guild_id in data and data[guild_id]["ticket_channel_id"]:
                    del data[guild_id]["ticket_channel_id"]
                    del data[guild_id]["ticket_channel_name"]
                    with open("./data/config.json", "w") as file:
                        json.dump(data, file, indent=4)
                    success = discord.Embed(title="Ticket Channel Setup", description="Ticket channel setup deleted successfully.", color=discord.Color.green())
                    await interaction.response.edit_message(embed=success, view=MenuButton())
                else:
                    await interaction.response.send_message("No ticket channel setup found.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)
            return
    @discord.ui.button(label="Delete Ticket Category Setup", style=discord.ButtonStyle.danger, custom_id="delete_ticket_category_setup", row=1)
    async def DTCa_callback(self, button, interaction):
        try:
            with open("./data/config.json", "r") as file:
                data = json.load(file)
                guild_id = str(interaction.guild.id)
                if guild_id in data and data[guild_id]["ticket_category_id"]:
                    del data[guild_id]["ticket_category_id"]
                    del data[guild_id]["ticket_category_name"]
                    with open("./data/config.json", "w") as file:
                        json.dump(data, file, indent=4)
                    success = discord.Embed(title="Ticket Category Setup", description="Ticket category setup deleted successfully.", color=discord.Color.green())
                    await interaction.response.edit_message(embed=success, view=MenuButton())
                else:
                    await interaction.response.send_message("No ticket category setup found.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)
            return

    @discord.ui.button(label="Setup Embed", style=discord.ButtonStyle.secondary, custom_id="setup_embed", row=2)
    async def SE_callback(self, button, interaction):
        try:
            await interaction.response.send_modal(EmbedSetupModal())
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)
            return
    @discord.ui.button(label="Start Ticket System", style=discord.ButtonStyle.success, custom_id="start_ticket_system", row=2)
    async def STS_callback(self, button, interaction):
        try:
            with open("./data/config.json", "r") as file:
                data = json.load(file)
                data[str(interaction.guild.id)]["status"] = "active"
            with open("./data/config.json", "w") as file:
                json.dump(data, file, indent=4)
                if data[str(interaction.guild.id)]["ticket_channel_id"] and data[str(interaction.guild.id)]["ticket_category_id"] and data[str(interaction.guild.id)]["embed_title"] and data[str(interaction.guild.id)]["embed_description"]:
                    channel = interaction.guild.get_channel(int(data[str(interaction.guild.id)]["ticket_channel_id"]))
                    if channel:
                        embed = discord.Embed(
                            title=data[str(interaction.guild.id)]["embed_title"],
                            description=data[str(interaction.guild.id)]["embed_description"],
                            color=discord.Color.blue()
                        )
                        embed.set_author(name=interaction.client.user.name, icon_url=interaction.client.user.display_avatar.url)
                        embed.set_footer(text="Created by Yi3849")
                        await channel.send(embed=embed, view=TicketButton())
                    else:
                        await interaction.response.send_message("Ticket channel not found. Please set up the ticket channel first.", ephemeral=True)
                        return
                    success = discord.Embed(title="Ticket System", description="Ticket system is ready to use!", color=discord.Color.green())
                    await interaction.response.edit_message(embed=success, view=MenuButton())
                else:
                    error = discord.Embed(title="Ticket System Error", description="Please complete the setup first.", color=discord.Color.red())
                    await interaction.response.edit_message(embed=error, view=MenuButton())
                    return
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)
            return
    @discord.ui.button(label="Stop Ticket System", style=discord.ButtonStyle.danger, custom_id="stop_ticket_system", row=2)
    async def STP_callback(self, button, interaction):
        try:
            with open("./data/config.json", "r") as file:
                data = json.load(file)
                data[str(interaction.guild.id)]["status"] = "inactive"
            with open("./data/config.json", "w") as file:
                json.dump(data, file, indent=4)
                success = discord.Embed(title="Ticket System", description="Ticket system has been stopped.", color=discord.Color.red())
                await interaction.response.edit_message(embed=success, view=MenuButton())
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)
            return
    @discord.ui.button(label="System Config", style=discord.ButtonStyle.secondary, custom_id="system_config", row=3)
    async def SC_callback(self, button, interaction):
        try:
            with open("./data/config.json", "r") as file:
                data = json.load(file)
                if "send_to_user_chat_history" not in data[str(interaction.guild.id)] or "user_can_close_ticket" not in data[str(interaction.guild.id)]:
                    data[str(interaction.guild.id)]["send_to_user_chat_history"] = False
                    data[str(interaction.guild.id)]["user_can_close_ticket"] = False
                    with open("./data/config.json", "w") as file:
                        json.dump(data, file, indent=4)
            config=discord.Embed(title="System Configuration", description="This is the system configuration.", color=discord.Color.blue())
            config.add_field(
                name="Send to User Chat History：",
                value="🟢 Enabled" if data[str(interaction.guild.id)].get("send_to_user_chat_history", False) else "🔴 Disabled",
                inline=False
            )
            config.add_field(
                name="User Can Close Ticket：",
                value="🟢 Enabled" if data[str(interaction.guild.id)].get("user_can_close_ticket", False) else "🔴 Disabled",
                inline=False
            )
            await interaction.response.edit_message(embed=config, view=SystemConfigSelectView(interaction))
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)
            return

class ChannelSelect(discord.ui.Select):
    def __init__(self, channels: list[discord.TextChannel]):
        options = [
            discord.SelectOption(
                label = channel.name,
                description = f"ID: {channel.id}",
                value = str(channel.id)
            )
            for channel in channels
        ]

        super().__init__(
            placeholder="Select a channel",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="channel_select"
        )

    async def callback(self, interaction: discord.Interaction):
        selected_channel_id = int(self.values[0])
        channel = interaction.guild.get_channel(selected_channel_id)
        if channel:
            try:
                with open("./data/config.json", "r") as file:
                    data = json.load(file)
                    data[str(interaction.guild.id)]["ticket_channel_id"] = selected_channel_id
                    data[str(interaction.guild.id)]["ticket_channel_name"] = channel.name
                with open("./data/config.json", "w") as file:
                    json.dump(data, file, indent=4)
                success = discord.Embed(title="Ticket Channel Setup", description=f"Ticket channel set to {channel.mention}.", color=discord.Color.green())
                await interaction.response.edit_message(embed=success, view=MenuButton())
            except Exception as e:
                await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)
                return
        else:
            await interaction.response.send_message("Channel not found.", ephemeral=True)

class CategorySelect(discord.ui.Select):
    def __init__(self, categories: list[discord.CategoryChannel]):
        options = [
            discord.SelectOption(
                label=category.name,
                description=f"ID: {category.id}",
                value=str(category.id)
            )
            for category in categories
        ]

        super().__init__(
            placeholder="Select a category",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="category_select"
        )

    async def callback(self, interaction: discord.Interaction):
        selected_category_id = int(self.values[0])
        category = interaction.guild.get_channel(selected_category_id)
        if category:
            try:
                with open("./data/config.json", "r") as file:
                    data = json.load(file)
                    data[str(interaction.guild.id)]["ticket_category_id"] = selected_category_id
                    data[str(interaction.guild.id)]["ticket_category_name"] = category.name
                with open("./data/config.json", "w") as file:
                    json.dump(data, file, indent=4)
                success = discord.Embed(title="Ticket category Setup", description=f"Ticket category set to {category.name}.", color=discord.Color.green())
                await interaction.response.edit_message(embed=success, view=MenuButton())
            except Exception as e:
                await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)
                return
        else:
            await interaction.response.send_message("Category not found.", ephemeral=True)

class SystemConfigSelect(discord.ui.Select):
    def __init__(self, interaction: discord.Interaction):
        with open("./data/config.json", "r") as file:
            data = json.load(file)
        options = [
            discord.SelectOption(
                label="Send to User Chat History",
                description=f"Do you want to send ticket chat history to user?",
                value="send_to_user_chat_history"
            ),
            discord.SelectOption(
                label="User Can Close Ticket",
                description="Can the user close their own ticket?",
                value="user_can_close_ticket"
            )
        ]

        super().__init__(
            placeholder="Select a configuration option",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="system_config_select"
        )
    
    async def callback(self, interaction: discord.Interaction):
        selected_option = self.values[0]
        with open("./data/config.json", "r") as file:
            data = json.load(file)
            guild_id = str(interaction.guild.id)
            data[guild_id][selected_option] = not data[guild_id][selected_option]
        with open("./data/config.json", "w") as file:
            json.dump(data, file, indent=4)
        config=discord.Embed(title="System Configuration", description="This is the system configuration.", color=discord.Color.blue())
        config.add_field(
            name="Send to User Chat History：",
            value="🟢 Enabled" if data[guild_id].get("send_to_user_chat_history", False) else "🔴 Disabled",
            inline=False
        )
        config.add_field(
            name="User Can Close Ticket：",
            value="🟢 Enabled" if data[guild_id].get("user_can_close_ticket", False) else "🔴 Disabled",
            inline=False
        )
        await interaction.response.edit_message(embed=config, view=SystemConfigSelectView(interaction))

def setup(bot):
    bot.add_cog(TicketSystem(bot))