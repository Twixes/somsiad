# Copyright 2019 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from sqlalchemy import create_engine, Column, BigInteger, String, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from configuration import configuration

engine = create_engine(configuration['database_url'])
Base = declarative_base()
Session = sessionmaker(bind=engine)


class Server(Base):
    __tablename__ = 'servers'

    COMMAND_PREFIX_MAX_LENGTH = 12

    id = Column(BigInteger, primary_key=True)
    command_prefix = Column(String(COMMAND_PREFIX_MAX_LENGTH))
    joined_at = Column(DateTime, nullable=False)


Base.metadata.create_all(engine)
