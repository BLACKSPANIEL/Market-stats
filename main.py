"""
Main entry point for Majestic RP Marketplace Bot
Initializes and runs the Discord bot with proper error handling
"""

import discord
from discord.ext import commands
import logging
import sys
from dotenv import load_dotenv
from config import (
    DISCORD_TOKEN,
    BOT_STATUS,
    BOT_TYPE,
    LOG_LEVEL,
    LOG_FORMAT,
    LOG_DATE_FORMAT
)

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

# Create formatter
formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

# Create console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(LOG_LEVEL)
console_handler.setFormatter(formatter)

# Create file handler
file_handler = logging.FileHandler("bot.log", encoding="utf-8")
file_handler.setLevel(LOG_LEVEL)
file_handler.setFormatter(formatter)

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(LOG_LEVEL)
root_logger.addHandler(console_handler)
root_logger.addHandler(file_handler)

# Get logger for this module
logger = logging.getLogger(__name__)

# ============================================================================
# DISCORD INTENTS
# ============================================================================

# Configure intents (only enable what's needed)
intents = discord.Intents.default()
intents.message_content = False  # Not needed for slash commands
intents.members = False  # Not needed for basic functionality
intents.presences = False  # Not needed

# ============================================================================
# BOT CLASS
# ============================================================================

class MajesticBot(commands.Bot):
    """
    Main bot class for Majestic RP Marketplace
    
    Handles bot lifecycle, command synchronization, and error handling
    """
    
    def __init__(self):
        """Initialize bot with command prefix and intents"""
        super().__init__(
            command_prefix="!",  # Not used for slash commands, but required
            intents=intents,
            help_command=None,  # We'll use custom help command
            case_insensitive=True
        )
        logger.info("MajesticBot instance created")
    
    async def setup_hook(self):
        """
        Setup hook - called when bot is starting
        Loads all cogs and syncs commands
        """
        logger.info("=" * 60)
        logger.info("Starting bot setup...")
        logger.info("=" * 60)
        
        try:
            # Load cogs
            logger.info("Loading cogs...")
            await self.load_extension("cogs.market_cog")
            logger.info("✓ All cogs loaded successfully")
            
            # Sync slash commands
            logger.info("Syncing slash commands...")
            synced = await self.tree.sync()
            logger.info(f"✓ Synced {len(synced)} slash commands")
            
            logger.info("=" * 60)
            logger.info("Bot setup completed successfully!")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"✗ Failed to load cogs: {e}", exc_info=True)
            raise
    
    async def on_ready(self):
        """Called when bot is ready and connected to Discord"""
        logger.info("=" * 60)
        logger.info(f"✓ Bot logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"✓ Connected to {len(self.guilds)} guilds")
        logger.info(f"✓ Serving {len(set(self.get_all_members()))} users")
        logger.info("=" * 60)
        
        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=BOT_TYPE,
                name=BOT_STATUS
            )
        )
        logger.info(f"✓ Bot status set: '{BOT_TYPE.name} {BOT_STATUS}'")
    
    async def on_guild_join(self, guild: discord.Guild):
        """Called when bot joins a new guild"""
        logger.info(f"✓ Joined new guild: {guild.name} (ID: {guild.id})")
        logger.info(f"  - Members: {guild.member_count}")
        logger.info(f"  - Owner: {guild.owner}")
    
    async def on_guild_remove(self, guild: discord.Guild):
        """Called when bot leaves a guild"""
        logger.info(f"✗ Left guild: {guild.name} (ID: {guild.id})")
    
    async def on_command_error(self, ctx: commands.Context, error: Exception):
        """
        Global error handler for prefix commands
        
        Args:
            ctx: Command context
            error: Exception that occurred
        """
        logger.error(f"Prefix command error: {error}", exc_info=True)
    
    async def on_app_command_error(self, interaction: discord.Interaction, error: Exception):
        """
        Global error handler for slash commands
        
        Args:
            interaction: Command interaction
            error: Exception that occurred
        """
        logger.error(f"Slash command error: {error}", exc_info=True)
        
        # Try to send error message to user
        try:
            error_message = "Произошла ошибка при выполнении команды. Попробуйте позже."
            
            if not interaction.response.is_done():
                await interaction.response.send_message(error_message, ephemeral=True)
            else:
                await interaction.followup.send(error_message, ephemeral=True)
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")


# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """Main entry point for the bot"""
    # Load environment variables
    load_dotenv()
    
    # Validate configuration
    if not DISCORD_TOKEN:
        logger.critical("DISCORD_TOKEN not found in environment variables!")
        logger.critical("Please create a .env file with your Discord bot token.")
        sys.exit(1)
    
    # Create bot instance
    bot = MajesticBot()
    
    try:
        logger.info("Starting bot...")
        bot.run(DISCORD_TOKEN, log_handler=None)  # Disable default discord.py logging
        
    except discord.LoginFailure:
        logger.critical("Failed to login: Invalid Discord token")
        sys.exit(1)
    
    except discord.PrivilegedIntentsRequired:
        logger.critical("Failed to login: Privileged intents not enabled")
        logger.critical("Please enable required intents in Discord Developer Portal")
        sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("Bot stopped by user (KeyboardInterrupt)")
    
    except Exception as e:
        logger.critical(f"Failed to start bot: {e}", exc_info=True)
        sys.exit(1)


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot shutdown complete")
        sys.exit(0)