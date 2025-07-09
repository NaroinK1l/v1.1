from disnake.ext import commands
from services.config import GUILD_ID

class BaseCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def sync_commands(self):
        guild_id = GUILD_ID
        all_commands = self.bot.application_commands
        
        commands = [cmd for cmd in all_commands if cmd.guild_ids == [guild_id]]
        
        if commands:
            await self.bot.bulk_overwrite_guild_commands(guild_id, commands)
            command_names = [cmd.name for cmd in commands]
            print(f"[DEBUG] Команды синхронизированы для сервера {guild_id}: {', '.join(command_names)}")
        else:
            print(f"[DEBUG] Нет команд для синхронизации для сервера {guild_id}")

def setup(bot):
    bot.add_cog(BaseCog(bot))
