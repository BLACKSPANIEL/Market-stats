"""
Embed creation module for Discord messages
Creates beautiful, formatted embeds for all bot responses
"""

import discord
from typing import Dict, Any, List, Optional
from config import CATEGORIES, COLORS, LISTINGS_PER_PAGE


# ============================================================================
# STATS EMBED
# ============================================================================

def create_stats_embed(
    category: str,
    server: int,
    data: Dict[str, Any],
    author: Optional[discord.Member] = None
) -> discord.Embed:
    """
    Create embed with marketplace statistics
    
    Args:
        category: Category name
        server: Server number
        data: Statistics data from API
        author: Discord member who requested stats
        
    Returns:
        Formatted Discord embed
    """
    category_name = CATEGORIES.get(category, category)
    color = COLORS.get(category, COLORS["info"])
    
    embed = discord.Embed(
        title=f"📊 Статистика: {category_name}",
        description=f"**Сервер #{server}**",
        color=color,
        timestamp=discord.utils.utcnow()
    )
    
    # Add author if provided
    if author:
        embed.set_footer(
            text=f"Запрошено: {author.display_name}",
            icon_url=author.display_avatar.url if author.display_avatar else None
        )
    
    # Add statistics fields with emojis
    if "total_listings" in data:
        embed.add_field(
            name="📦 Всего объявлений",
            value=f"**{data['total_listings']:,}**",
            inline=True
        )
    
    if "average_price" in data:
        embed.add_field(
            name="💰 Средняя цена",
            value=f"**${data['average_price']:,}**",
            inline=True
        )
    
    if "min_price" in data and "max_price" in data:
        embed.add_field(
            name="📈 Диапазон цен",
            value=f"**${data['min_price']:,}** - **${data['max_price']:,}**",
            inline=True
        )
    
    if "total_value" in data:
        embed.add_field(
            name="💵 Общая стоимость",
            value=f"**${data['total_value']:,}**",
            inline=True
        )
    
    if "price_change_24h" in data:
        change = data["price_change_24h"]
        emoji = "📈" if change >= 0 else "📉"
        arrow = "↑" if change >= 0 else "↓"
        embed.add_field(
            name=f"{emoji} Изменение за 24ч",
            value=f"{arrow} **{abs(change):.2f}%**",
            inline=True
        )
    
    if "price_change_7d" in data:
        change = data["price_change_7d"]
        emoji = "📈" if change >= 0 else "📉"
        arrow = "↑" if change >= 0 else "↓"
        embed.add_field(
            name=f"{emoji} Изменение за 7д",
            value=f"{arrow} **{abs(change):.2f}%**",
            inline=True
        )
    
    if "most_popular" in data:
        embed.add_field(
            name="⭐ Самый популярный",
            value=data["most_popular"],
            inline=False
        )
    
    if "least_popular" in data:
        embed.add_field(
            name="💤 Самый редкий",
            value=data["least_popular"],
            inline=False
        )
    
    if "last_updated" in data:
        embed.add_field(
            name="🕐 Обновлено",
            value=data["last_updated"],
            inline=False
        )
    
    return embed


# ============================================================================
# LISTINGS EMBED
# ============================================================================

def create_listings_embed(
    category: str,
    server: int,
    listings: List[Dict[str, Any]],
    page: int = 1,
    total_pages: int = 1,
    author: Optional[discord.Member] = None
) -> discord.Embed:
    """
    Create embed with marketplace listings
    
    Args:
        category: Category name
        server: Server number
        listings: List of listings
        page: Current page number
        total_pages: Total number of pages
        author: Discord member who requested
        
    Returns:
        Formatted Discord embed
    """
    category_name = CATEGORIES.get(category, category)
    color = COLORS.get(category, COLORS["info"])
    
    embed = discord.Embed(
        title=f"📋 Объявления: {category_name}",
        description=f"**Сервер #{server}** | Страница {page}/{total_pages}",
        color=color,
        timestamp=discord.utils.utcnow()
    )
    
    if author:
        embed.set_footer(
            text=f"Запрошено: {author.display_name}",
            icon_url=author.display_avatar.url if author.display_avatar else None
        )
    
    if not listings:
        embed.add_field(
            name="ℹ️ Информация",
            value="Нет объявлений для отображения",
            inline=False
        )
        return embed
    
    # Add listings (max 10 per page)
    for i, listing in enumerate(listings[:LISTINGS_PER_PAGE], 1):
        name = listing.get("name", "Неизвестно")
        price = listing.get("price", 0)
        seller = listing.get("seller", "Неизвестно")
        item_id = listing.get("id", "")
        
        # Format price with commas
        price_formatted = f"${price:,}"
        
        embed.add_field(
            name=f"{i}. {name}",
            value=f"💰 **{price_formatted}**\n👤 {seller}",
            inline=True
        )
    
    return embed


# ============================================================================
# ERROR EMBEDS
# ============================================================================

def create_error_embed(
    title: str,
    description: str,
    error_type: str = "error"
) -> discord.Embed:
    """
    Create error embed
    
    Args:
        title: Error title
        description: Error description
        error_type: Type of error (error, warning, info)
        
    Returns:
        Formatted error embed
    """
    color = COLORS.get(error_type, COLORS["error"])
    
    embed = discord.Embed(
        title=f"❌ {title}",
        description=description,
        color=color,
        timestamp=discord.utils.utcnow()
    )
    
    return embed


def create_success_embed(
    title: str,
    description: str
) -> discord.Embed:
    """Create success embed"""
    embed = discord.Embed(
        title=f"✅ {title}",
        description=description,
        color=COLORS["success"],
        timestamp=discord.utils.utcnow()
    )
    
    return embed


def create_info_embed(
    title: str,
    description: str
) -> discord.Embed:
    """Create info embed"""
    embed = discord.Embed(
        title=f"ℹ️ {title}",
        description=description,
        color=COLORS["info"],
        timestamp=discord.utils.utcnow()
    )
    
    return embed


def create_warning_embed(
    title: str,
    description: str
) -> discord.Embed:
    """Create warning embed"""
    embed = discord.Embed(
        title=f"⚠️ {title}",
        description=description,
        color=COLORS["warning"],
        timestamp=discord.utils.utcnow()
    )
    
    return embed


# ============================================================================
# HELP & INFO EMBEDS
# ============================================================================

def create_help_embed() -> discord.Embed:
    """Create help embed with all available commands"""
    embed = discord.Embed(
        title="📖 Справка по командам",
        description="Доступные slash-команды бота:",
        color=COLORS["info"],
        timestamp=discord.utils.utcnow()
    )
    
    embed.add_field(
        name="🔑 `/setkey`",
        value="Установить API ключ Majestic RP\n"
              "Использование: `/setkey <api_key> [personal]`\n"
              "⚠️ Ключ показывается только один раз!",
        inline=False
    )
    
    embed.add_field(
        name="🔍 `/mykey`",
        value="Проверить, установлен ли API ключ",
        inline=False
    )
    
    embed.add_field(
        name="🗑️ `/removekey`",
        value="Удалить сохраненный API ключ\n"
              "Использование: `/removekey [personal]`",
        inline=False
    )
    
    embed.add_field(
        name="📊 `/market`",
        value="Статистика маркетплейса с интерактивными кнопками\n"
              "Использование: `/market [category] [server]`",
        inline=False
    )
    
    embed.add_field(
        name="📈 `/stats`",
        value="Статистика с выбором категории\n"
              "Использование: `/stats [server]`",
        inline=False
    )
    
    embed.add_field(
        name="📋 `/listings`",
        value="Показать объявления категории\n"
              "Использование: `/listings <category> <server> [page]`",
        inline=False
    )
    
    embed.add_field(
        name="📂 `/categories`",
        value="Показать все доступные категории",
        inline=False
    )
    
    embed.add_field(
        name="🌐 `/servers`",
        value="Показать поддерживаемые серверы",
        inline=False
    )
    
    embed.add_field(
        name="❓ `/help`",
        value="Показать эту справку",
        inline=False
    )
    
    embed.set_footer(text="Majestic RP Marketplace Bot | v1.1.0")
    
    return embed


def create_categories_embed() -> discord.Embed:
    """Create embed with all available categories"""
    embed = discord.Embed(
        title="📂 Доступные категории",
        description="Выберите категорию для просмотра статистики:",
        color=COLORS["info"],
        timestamp=discord.utils.utcnow()
    )
    
    # Group categories in pairs for better layout
    categories_list = list(CATEGORIES.items())
    for i in range(0, len(categories_list), 2):
        pair = categories_list[i:i+2]
        value = "\n".join([f"{emoji} `{key}`" for key, emoji in pair])
        embed.add_field(
            name="\u200b",  # Zero-width space
            value=value,
            inline=True
        )
    
    return embed


def create_servers_embed() -> discord.Embed:
    """Create embed with supported servers"""
    from config import SUPPORTED_SERVERS, DEFAULT_SERVER
    
    embed = discord.Embed(
        title="🌐 Поддерживаемые серверы",
        description="Выберите номер сервера для просмотра статистики:",
        color=COLORS["info"],
        timestamp=discord.utils.utcnow()
    )
    
    servers_text = "\n".join([
        f"**Сервер {s}** {'⭐ (по умолчанию)' if s == DEFAULT_SERVER else ''}"
        for s in SUPPORTED_SERVERS
    ])
    
    embed.add_field(
        name="Доступные серверы",
        value=servers_text,
        inline=False
    )
    
    return embed


def create_key_set_embed(api_key: str, scope: str) -> discord.Embed:
    """
    Create embed for successful key setup (shows key ONCE)
    
    Args:
        api_key: The API key to show
        scope: Key scope (guild or user)
        
    Returns:
        Formatted embed with API key
    """
    embed = discord.Embed(
        title="✅ API ключ сохранен",
        description=f"Ключ успешно сохранен ({scope})!\n\n"
                   f"**Ваш API ключ:** `{api_key}`\n\n"
                   f"⚠️ **Сохраните этот ключ! Он больше не будет показан.**\n"
                   f"Используйте `/mykey` для проверки статуса ключа.",
        color=COLORS["success"],
        timestamp=discord.utils.utcnow()
    )
    
    return embed


def create_key_status_embed(has_personal: bool, has_guild: bool) -> discord.Embed:
    """
    Create embed showing key status
    
    Args:
        has_personal: Whether personal key exists
        has_guild: Whether guild key exists
        
    Returns:
        Formatted embed with key status
    """
    if has_personal:
        description = "✅ У вас установлен **личный** API ключ."
    elif has_guild:
        description = "✅ На сервере установлен **серверный** API ключ."
    else:
        description = "❌ API ключ не установлен.\nИспользуйте `/setkey` для установки."
    
    embed = discord.Embed(
        title="🔑 Статус API ключа",
        description=description,
        color=COLORS["info"] if (has_personal or has_guild) else COLORS["warning"],
        timestamp=discord.utils.utcnow()
    )
    
    return embed


# ============================================================================
# SELECT MENU EMBEDS
# ============================================================================

def create_category_select_embed(server: int) -> discord.Embed:
    """
    Create embed for category selection
    
    Args:
        server: Server number
        
    Returns:
        Formatted embed for category selection
    """
    embed = discord.Embed(
        title="📊 Выберите категорию",
        description=f"**Сервер #{server}**\nНажмите на кнопку ниже для просмотра статистики",
        color=COLORS["primary"],
        timestamp=discord.utils.utcnow()
    )
    
    return embed