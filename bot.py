import os
import discord
from discord import app_commands
from discord.ext import commands
from aiohttp import web

BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not BOT_TOKEN and os.path.exists("token.txt"):
    with open("token.txt", "r", encoding="utf-8") as f:
        BOT_TOKEN = f.read().strip()

# Keep-alive web server to prevent Render free tier errors
async def handle_ping(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

class LtcAgreementView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="I Agree", 
        style=discord.ButtonStyle.success, 
        emoji="✅", 
        custom_id="dot_bot_agree_ltc"
    )
    async def agree_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        ltc_address = "LP8sXJmG44nYJzq7RmumzdUmcHFcSfwoQ1"
        # Triple backticks create a monospace code block for one-tap copy on mobile
        await interaction.response.send_message(
            f"✅ **{interaction.user.mention} has agreed to the rules.**\n\n"
            "**LTC Address (Tap/Hold below to copy):**\n"
            f"```{ltc_address}```",
            ephemeral=False
        )

class DotBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await start_web_server()
        self.add_view(LtcAgreementView())
        await self.tree.sync()
        print("Slash commands synced successfully.")

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")

bot = DotBot()

# Enabled for servers, personal user apps, DMs, and group DMs
@bot.tree.command(name="pay", description="Displays LTC rules and agreement")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def pay(interaction: discord.Interaction):
    embed = discord.Embed(title="Rules:", color=0x3498DB)
    embed.description = (
        "• Send a screenshot of payment.\n"
        "• send exact amnt\n"
        "• fluctuations arent covered\n\n"
        "Click I agree to continue."
    )
    await interaction.response.send_message(embed=embed, view=LtcAgreementView())

if __name__ == "__main__":
    if not BOT_TOKEN:
        raise ValueError("DISCORD_BOT_TOKEN environment variable is missing.")
    bot.run(BOT_TOKEN)
