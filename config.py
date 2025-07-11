from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DB")

DB_URL = f"mysql+aiomysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}"

ECHOCF = os.getenv("ECHO", "False").lower() in ("true", "1", "yes")

ADMINS_RAW = os.getenv("ADMINS", "")
ADMINS = [int(x.strip().strip("()")) for x in ADMINS_RAW.split(",") if x.strip()]
if not ADMINS:
    raise ValueError("No admins found in the environment variable 'ADMINS'. Please set it correctly.")