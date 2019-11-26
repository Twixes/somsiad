# Copyright 2019 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from typing import Any, Union, Sequence, Dict
from sqlalchemy import create_engine, Column, BigInteger, String, DateTime, ForeignKey
from sqlalchemy.orm import Session as _Session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects import postgresql
import discord
from configuration import configuration

engine = create_engine(configuration['database_url'])
Base = declarative_base()
Session = sessionmaker(bind=engine)


def create_table(model):
    Base.metadata.create_all(engine, tables=[model.__table__])


def insert_or_ignore(model: Base, values: Union[Sequence[Dict[str, Any]], Dict[str, Any]], *, session: _Session = None):
    use_own_session = session is None
    if use_own_session:
        session = Session()
    dialect_name = str(session.bind.dialect.name)
    if dialect_name == 'postgresql':
        inserter = postgresql.insert(model.__table__).values(values).on_conflict_do_nothing()
    elif dialect_name == 'mysql':
        inserter = model.__table__.insert().prefix_with('IGNORE').values(values)
    elif dialect_name == 'sqlite':
        inserter = model.__table__.insert().prefix_with('OR IGNORE').values(values)
    else:
        raise Exception(
            f'database dialect {dialect_name} is not supported, only postgresql, mysql and sqlite'
        )
    session.execute(inserter)
    session.commit()
    if use_own_session:
        session.close()


class Server(Base):
    __tablename__ = 'servers'

    COMMAND_PREFIX_MAX_LENGTH = 12

    id = Column(BigInteger, primary_key=True)
    command_prefix = Column(String(COMMAND_PREFIX_MAX_LENGTH))
    joined_at = Column(DateTime, nullable=False)

    @classmethod
    def register(cls, server: Sequence[discord.Guild]):
        values = {'id': server.id, 'joined_at': server.me.joined_at}
        insert_or_ignore(cls, values)

    @classmethod
    def register_all(cls, servers: Sequence[discord.Guild]):
        values = [{'id': server.id, 'joined_at': server.me.joined_at} for server in servers]
        insert_or_ignore(cls, values)


create_table(Server)
