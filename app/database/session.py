from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from config import DB_URL, ECHOCF

engine = create_async_engine(DB_URL, echo=ECHOCF, future=True)
async_session = async_sessionmaker(bind=engine, expire_on_commit=False)
