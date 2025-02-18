import datetime as dt
import uuid
from uuid import UUID
from enum import Enum, auto

from sqlalchemy import bindparam
from sqlalchemy import CheckConstraint
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Table
from sqlalchemy import text
from sqlalchemy import UniqueConstraint
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Mapped as M
from sqlalchemy.orm import mapped_column as column
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.sql.expression import false
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.associationproxy import AssociationProxy

from sqlalchemy_service import Base

sql_utcnow = text('(now() at time zone \'utc\')')


class BaseMixin:
    @declared_attr.directive
    def __tablename__(cls):
        letters = ['_' + i.lower() if i.isupper() else i for i in cls.__name__]
        return ''.join(letters).lstrip('_') + 's'

    id: M[UUID] = column(server_default=text("gen_random_uuid()"), primary_key=True, index=True)
    created_at: M[dt.datetime] = column(server_default=sql_utcnow)
    updated_at: M[dt.datetime | None] = column(nullable=True, onupdate=sql_utcnow)


class TaskItem(Base):
    __tablename__ = "task_items"

    id: M[int] = column(primary_key=True, index=True, autoincrement=True)
    task_id: M[UUID] = column(ForeignKey('tasks.id', ondelete="CASCADE"))

    left_eye_close: M[float]
    right_eye_close: M[float]
    is_eyes_closed: M[bool]
    face_left: M[int]
    face_top: M[int]
    face_bottom: M[int]
    face_right: M[int]
    is_face_small: M[bool]
    image_width: M[int]
    image_height: M[int]

    task: M['Task'] = relationship(back_populates='items')


class Task(BaseMixin, Base):
    error: M[str | None] = column(nullable=True)

    items: M[list['TaskItem']] = relationship(back_populates='task')

