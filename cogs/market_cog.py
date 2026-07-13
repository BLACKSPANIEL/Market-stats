"""
Marketplace Cog - Main cog with all slash commands
Handles marketplace statistics, API key management, and interactive UI
"""

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Select, View, Button, Modal, TextInput
import logging
from typing import Optional, Dict, Any, List
from config import CATEGORIES, SUPPORTED_SERVERS, DEFAULT_SERVER, COLORS, MIN_API_KEY_LENGTH
from utils.storage import get_api_key, set_api_key, remove_api_key, get_key_info
from utils.api_client import APIClient, InvalidAPIKeyError, RateLimitError, MajesticAPIError
from utils.embeds import (
    create_stats_embed,
    create_listings_embed,
    create_error_embed,
    create_success_embed,
    create_info_embed,
    create_warning_embed,
    create_help_embed,
    create_categories_embed,
    create_servers_embed,
    create_key_set_embed,
    create_key_status_embed,
    create_category_select_embed
)

logger = logging.getLogger(__name__)


# ============================================================================
# UI COMPONENTS (Views, Selects, Modals)
# ============================================================================

class CategorySelect(Select):
    """Dropdown select for category selection"""
    
    def __init__(self, author: discord.Member, server: int, api_key: str):
        """
        Initialize category select
        
        Args:
            author: Discord member who initiated the interaction
            server: Server number
            api_key: API key for requests
        """
        self.author = author
        self.server = server
        self.api_key = api_key
        
        # Create options from categories
        options = [
            discord.SelectOption(
                label=name,
                value=key,
                emoji=emoji.split()[0]  # Extract emoji
            )
            for key, name in CATEGORIES.items()
            for emoji in [name.split()[0]]  # Get emoji from name
        ]
        
        super().__init__(
            placeholder="Выберите категорию...",
            min_values=1,
            max_values=1,
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        """Handle category selection"""
        category = self.values[0]
        
        # Defer the interaction
        await interaction.response.defer()
        
        try:
            async with APIClient(self.api_key) as client:
                data = await client.get_market_stats(category, self.server)
                
                embed = create_stats_embed(
                    category,
                    self.server,
                    data,
                    self.author
                )
                
                await interaction.followup.send(embed=embed)
                logger.info(
                    f"Stats shown to {self.author} for {category} on server {self.server}"
                )
                
        except InvalidAPIKeyError:
            embed = create_error_embed(
                "Неверный API ключ",
                "Ваш API ключ недействителен. Используйте `/setkey` для обновления."
            )
            await interaction.followup.send(embed=embed)
            
        except RateLimitError:
            embed = create_error_embed(
                "Лимит запросов",
                "Превышен лимит запросов к API. Попробуйте позже.",
                error_type="warning"
            )
            await interaction.followup.send(embed=embed)
            
        except MajesticAPIError as e:
            embed = create_error_embed(
                "Ошибка API",
                str(e)
            )
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Unexpected error in category select: {e}", exc_info=True)
            embed = create_error_embed(
                "Неожиданная ошибка",
                "Произошла ошибка при получении статистики. Попробуйте позже."
            )
            await interaction.followup.send(embed=embed)
        
        # Disable the select after use
        self.disabled = True


class CategorySelectView(View):
    """View containing category select dropdown"""
    
    def __init__(self, author: discord.Member, server: int, api_key: str):
        """
        Initialize view with category select
        
        Args:
            author: Discord member who initiated
            server: Server number
            api_key: API key for requests
        """
        super().__init__(timeout=60)
        self.author = author
        self.server = server
        self.api_key = api_key
        
        # Add category select
        self.add_item(CategorySelect(author, server, api_key))
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Only allow the original author to use this view"""
        if interaction.user != self.author:
            await interaction.response.send_message(
                "Это меню не для вас!",
                ephemeral=True
            )
            return False
        return True


class ServerSelectView(View):
    """View for server selection"""
    
    def __init__(self, author: discord.Member, category: str, api_key: str):
        """
        Initialize view with server buttons
        
        Args:
            author: Discord member who initiated
            category: Category name
            api_key: API key for requests
        """
        super().__init__(timeout=60)
        self.author = author
        self.category = category
        self.api_key = api_key
        
        # Add server buttons
        for server in SUPPORTED_SERVERS:
            button = Button(
                label=f"Сервер {server}",
                style=discord.ButtonStyle.primary,
                custom_id=f"server_{server}"
            )
            button.callback = lambda s, server=server: self.show_stats(s, server)
            self.add_item(button)
    
    async def show_stats(self, interaction: discord.Interaction, server: int):
        """Show statistics for selected server"""
        await interaction.response.defer()
        
        try:
            async with APIClient(self.api_key) as client:
                data = await client.get_market_stats(self.category, server)
                
                embed = create_stats_embed(
                    self.category,
                    server,
                    data,
                    self.author
                )
                
                await interaction.followup.send(embed=embed)
                
                # Disable all buttons
                for item in self.children:
                    item.disabled = True
                
        except Exception as e:
            logger.error(f"Error showing stats: {e}")
            embed = create_error_embed(
                "Ошибка",
                str(e)
            )
            await interaction.followup.send(embed=embed)
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Only allow the original author to use this view"""
        if interaction.user != self.author:
            await interaction.response.send_message(
                "Это меню не для вас!",
                ephemeral=True
            )
            return False
        return True


# ============================================================================
# MAIN COG
# ============================================================================

class MarketCog(commands.Cog):
    """Marketplace statistics commands cog"""
    
    def __init__(self, bot: commands.Bot):
        """Initialize cog"""
        self.bot = bot
        logger.info("MarketCog initialized")
    
    # ========================================================================
    # API KEY COMMANDS
    # ========================================================================
    
    @app_commands.command(name="setkey", description="Установить API ключ Majestic RP")
    @app_commands.describe(
        api_key="Ваш API ключ от Majestic RP",
        personal="Установить ключ лично (только для вас) или для всего сервера"
    )
    async def setkey(
        self,
        interaction: discord.Interaction,
        api_key: str,
        personal: bool = False
    ):
        """
        Set API key for guild or user
        
        Args:
            interaction: Discord interaction
            api_key: API key to set
            personal: If True, set for user only. If False, set for guild
        """
        await interaction.response.defer(ephemeral=True)
        
        # Validate API key format
        if not api_key or len(api_key) < MIN_API_KEY_LENGTH:
            embed = create_error_embed(
                "Неверный формат ключа",
                f"API ключ должен содержать минимум {MIN_API_KEY_LENGTH} символов"
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Try to validate the key
        try:
            async with APIClient(api_key) as client:
                is_valid = await client.validate_key()
                
                if not is_valid:
                    embed = create_error_embed(
                        "Неверный API ключ",
                        "Указанный ключ недействителен. Проверьте ключ и попробуйте снова."
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return
                
                # Save key
                if personal:
                    set_api_key(interaction.guild_id, api_key, interaction.user.id)
                    scope = "личный"
                else:
                    # Check permissions for guild-wide key
                    if not interaction.user.guild_permissions.administrator:
                        embed = create_error_embed(
                            "Недостаточно прав",
                            "Для установки ключа на весь сервер нужны права администратора."
                        )
                        await interaction.followup.send(embed=embed, ephemeral=True)
                        return
                    
                    set_api_key(interaction.guild_id, api_key)
                    scope = "серверный"
                
                # Show key ONLY ONCE
                embed = create_key_set_embed(api_key, scope)
                await interaction.followup.send(embed=embed, ephemeral=True)
                
                logger.info(
                    f"API key set by {interaction.user} (ID: {interaction.user.id}) "
                    f"in guild {interaction.guild_id} (scope: {scope})"
                )
                
        except Exception as e:
            logger.error(f"Error setting API key: {e}", exc_info=True)
            embed = create_error_embed(
                "Ошибка",
                f"Не удалось проверить ключ: {str(e)}"
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name="mykey", description="Проверить, установлен ли API ключ")
    async def mykey(self, interaction: discord.Interaction):
        """Check if API key is set"""
        await interaction.response.defer(ephemeral=True)
        
        # Get key info
        key_info = get_key_info(interaction.guild_id, interaction.user.id)
        
        embed = create_key_status_embed(
            key_info["has_personal_key"],
            key_info["has_guild_key"]
        )
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name="removekey", description="Удалить сохраненный API ключ")
    @app_commands.describe(
        personal="Удалить личный ключ (только для вас) или серверный"
    )
    async def removekey(
        self,
        interaction: discord.Interaction,
        personal: bool = False
    ):
        """Remove saved API key"""
        await interaction.response.defer(ephemeral=True)
        
        # Check permissions for guild-wide key removal
        if not personal and not interaction.user.guild_permissions.administrator:
            embed = create_error_embed(
                "Недостаточно прав",
                "Для удаления серверного ключа нужны права администратора."
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Try to remove key
        removed = remove_api_key(
            interaction.guild_id,
            interaction.user.id if personal else None
        )
        
        if removed:
            scope = "личный" if personal else "серверный"
            embed = create_success_embed(
                "Ключ удален",
                f"API ключ ({scope}) успешно удален."
            )
        else:
            embed = create_info_embed(
                "Ключ не найден",
                "Сохраненный ключ не найден."
            )
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    # ========================================================================
    # MARKETPLACE COMMANDS
    # ========================================================================
    
    @app_commands.command(name="market", description="Статистика маркетплейса с интерактивными кнопками")
    @app_commands.describe(
        category="Категория для просмотра (оставьте пустым для выбора)",
        server="Номер сервера (оставьте пустым для сервера по умолчанию)"
    )
    @app_commands.choices(category=[
        app_commands.Choice(name=name, value=key)
        for key, name in CATEGORIES.items()
    ])
    async def market(
        self,
        interaction: discord.Interaction,
        category: Optional[str] = None,
        server: Optional[int] = None
    ):
        """
        Main marketplace command with interactive buttons
        
        Args:
            interaction: Discord interaction
            category: Category name (optional)
            server: Server number (optional)
        """
        await interaction.response.defer()
        
        # Use default server if not specified
        if server is None:
            server = DEFAULT_SERVER
        
        # Validate server
        if server not in SUPPORTED_SERVERS:
            embed = create_error_embed(
                "Неверный сервер",
                f"Поддерживаемые серверы: {', '.join(map(str, SUPPORTED_SERVERS))}"
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Get API key
        api_key = get_api_key(interaction.guild_id, interaction.user.id)
        
        if not api_key:
            embed = create_error_embed(
                "API ключ не найден",
                "Используйте `/setkey` для установки API ключа."
            )
            await interaction.followup.send(embed=embed)
            return
        
        # If category specified, show stats directly
        if category:
            try:
                async with APIClient(api_key) as client:
                    data = await client.get_market_stats(category, server)
                    
                    embed = create_stats_embed(
                        category,
                        server,
                        data,
                        interaction.user
                    )
                    
                    await interaction.followup.send(embed=embed)
                    logger.info(
                        f"Market stats requested by {interaction.user} for {category} on server {server}"
                    )
                    
            except InvalidAPIKeyError:
                embed = create_error_embed(
                    "Неверный API ключ",
                    "Ваш API ключ недействителен. Используйте `/setkey` для обновления."
                )
                await interaction.followup.send(embed=embed)
                
            except RateLimitError:
                embed = create_error_embed(
                    "Лимит запросов",
                    "Превышен лимит запросов к API. Попробуйте позже.",
                    error_type="warning"
                )
                await interaction.followup.send(embed=embed)
                
            except MajesticAPIError as e:
                embed = create_error_embed(
                    "Ошибка API",
                    str(e)
                )
                await interaction.followup.send(embed=embed)
                
            except Exception as e:
                logger.error(f"Unexpected error in market command: {e}", exc_info=True)
                embed = create_error_embed(
                    "Неожиданная ошибка",
                    "Произошла ошибка при получении статистики. Попробуйте позже."
                )
                await interaction.followup.send(embed=embed)
        else:
            # Show category selection dropdown
            view = CategorySelectView(interaction.user, server, api_key)
            embed = create_category_select_embed(server)
            
            await interaction.followup.send(embed=embed, view=view)
            logger.info(
                f"Market category selection shown to {interaction.user} for server {server}"
            )
    
    @app_commands.command(name="stats", description="Статистика с выбором категории")
    @app_commands.describe(
        server="Номер сервера (оставьте пустым для сервера по умолчанию)"
    )
    async def stats(self, interaction: discord.Interaction, server: Optional[int] = None):
        """
        Show statistics with interactive category selection
        
        Args:
            interaction: Discord interaction
            server: Server number (optional)
        """
        await interaction.response.defer()
        
        # Use default server if not specified
        if server is None:
            server = DEFAULT_SERVER
        
        # Validate server
        if server not in SUPPORTED_SERVERS:
            embed = create_error_embed(
                "Неверный сервер",
                f"Поддерживаемые серверы: {', '.join(map(str, SUPPORTED_SERVERS))}"
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Get API key
        api_key = get_api_key(interaction.guild_id, interaction.user.id)
        
        if not api_key:
            embed = create_error_embed(
                "API ключ не найден",
                "Используйте `/setkey` для установки API ключа."
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Show category selection dropdown
        view = CategorySelectView(interaction.user, server, api_key)
        embed = create_category_select_embed(server)
        
        await interaction.followup.send(embed=embed, view=view)
        logger.info(
            f"Stats category selection shown to {interaction.user} for server {server}"
        )
    
    @app_commands.command(name="listings", description="Показать объявления категории")
    @app_commands.describe(
        category="Категория для просмотра",
        server="Номер сервера",
        page="Номер страницы (по умолчанию 1)"
    )
    @app_commands.choices(category=[
        app_commands.Choice(name=name, value=key)
        for key, name in CATEGORIES.items()
    ])
    async def listings(
        self,
        interaction: discord.Interaction,
        category: str,
        server: int,
        page: int = 1
    ):
        """
        Get marketplace listings
        
        Args:
            interaction: Discord interaction
            category: Category name
            server: Server number
            page: Page number
        """
        await interaction.response.defer()
        
        # Validate server
        if server not in SUPPORTED_SERVERS:
            embed = create_error_embed(
                "Неверный сервер",
                f"Поддерживаемые серверы: {', '.join(map(str, SUPPORTED_SERVERS))}"
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Validate page
        if page < 1:
            page = 1
        
        # Get API key
        api_key = get_api_key(interaction.guild_id, interaction.user.id)
        
        if not api_key:
            embed = create_error_embed(
                "API ключ не найден",
                "Используйте `/setkey` для установки API ключа."
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Fetch listings
        try:
            async with APIClient(api_key) as client:
                offset = (page - 1) * LISTINGS_PER_PAGE
                
                listings = await client.get_category_listings(
                    category,
                    server,
                    limit=LISTINGS_PER_PAGE,
                    offset=offset
                )
                
                # Calculate total pages (estimate)
                total_pages = max(1, page + 1) if len(listings) == LISTINGS_PER_PAGE else page
                
                embed = create_listings_embed(
                    category,
                    server,
                    listings,
                    page=page,
                    total_pages=total_pages,
                    author=interaction.user
                )
                
                await interaction.followup.send(embed=embed)
                logger.info(
                    f"Listings requested by {interaction.user} for {category} "
                    f"on server {server}, page {page}"
                )
                
        except InvalidAPIKeyError:
            embed = create_error_embed(
                "Неверный API ключ",
                "Ваш API ключ недействителен. Используйте `/setkey` для обновления."
            )
            await interaction.followup.send(embed=embed)
            
        except RateLimitError:
            embed = create_error_embed(
                "Лимит запросов",
                "Превышен лимит запросов к API. Попробуйте позже.",
                error_type="warning"
            )
            await interaction.followup.send(embed=embed)
            
        except MajesticAPIError as e:
            embed = create_error_embed(
                "Ошибка API",
                str(e)
            )
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Unexpected error in listings command: {e}", exc_info=True)
            embed = create_error_embed(
                "Неожиданная ошибка",
                "Произошла ошибка при получении объявлений. Попробуйте позже."
            )
            await interaction.followup.send(embed=embed)
    
    # ========================================================================
    # INFO COMMANDS
    # ========================================================================
    
    @app_commands.command(name="categories", description="Показать все доступные категории")
    async def categories(self, interaction: discord.Interaction):
        """Show all available categories"""
        embed = create_categories_embed()
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="servers", description="Показать поддерживаемые серверы")
    async def servers(self, interaction: discord.Interaction):
        """Show supported servers"""
        embed = create_servers_embed()
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="help", description="Показать справку по командам")
    async def help(self, interaction: discord.Interaction):
        """Show help message"""
        embed = create_help_embed()
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ============================================================================
# COG SETUP
# ============================================================================

async def setup(bot: commands.Bot):
    """
    Setup function for loading the cog
    
    Args:
        bot: Discord bot instance
    """
    await bot.add_cog(MarketCog(bot))
    logger.info("MarketCog loaded successfully")