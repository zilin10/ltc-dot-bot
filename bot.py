import os
import sys
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from aiohttp import web

BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not BOT_TOKEN and os.path.exists("token.txt"):
    with open("token.txt", "r", encoding="utf-8") as f:
        BOT_TOKEN = f.read().strip()

# Keep-alive web server to satisfy Render health checks
async def handle_ping(request):
    return web.Response(text="LTC Bot is operational!")

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
        custom_id="agree_ltc_button"
    )
    async def agree_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Acknowledge immediately to prevent button click timeouts
        await interaction.response.defer(ephemeral=False)
        
        ltc_address = "LP8sXJmG44nYJzq7RmumzdUmcHFcSfwoQ1"
        await interaction.followup.send(
            f"✅ **{interaction.user.mention} has agreed to the rules.**\n\n"
            "**LTC Address (Tap/Hold below to copy):**\n"
            f"```{ltc_address}```"
        )

class DotBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await start_web_server()
        self.add_view(LtcAgreementView())
        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} command(s) successfully.")
        except Exception as e:
            print(f"Command sync failed: {e}")

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")

bot = DotBot()

@bot.tree.command(name="pay", description="Displays LTC rules and agreement")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def pay(interaction: discord.Interaction):
    # Acknowledge immediately to beat Discord's 3-second deadline
    await interaction.response.defer(ephemeral=False)
    
    embed = discord.Embed(title="Rules:", color=0x3498DB)
    embed.description = (
        "• Send a screenshot of payment.\n"
        "• send exact amnt\n"
        "• fluctuations arent covered\n\n"
        "Click **I Agree** to continue."
    )
    await interaction.followup.send(embed=embed, view=LtcAgreementView())

async def main():
    if not BOT_TOKEN:
        print("ERROR: DISCORD_BOT_TOKEN environment variable is missing.", file=sys.stderr)
        sys.exit(1)
    
    retry_delay = 5
    while True:
        try:
            async with bot:
                await bot.start(BOT_TOKEN)
        except (discord.HTTPException, discord.GatewayNotFound) as err:
            print(f"Gateway connection error ({err}). Retrying in {retry_delay}s...")
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 60)
        except Exception as e:
            print(f"Fatal error: {e}", file=sys.stderr)
            raise e

if __name__ == "__main__":
    asyncio.run(main())
