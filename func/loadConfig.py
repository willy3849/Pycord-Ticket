import os
import dotenv

dotenv.load_dotenv()

DISCORD_TOKEN=os.getenv("DISCORD_TOKEN")
COMMAND_PREFIX=os.getenv("COMMAND_PREFIX")