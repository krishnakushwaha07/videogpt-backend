from sqlalchemy.orm import mapped_column, DeclarativeBase, Mapped, relationship
from sqlalchemy import INTEGER, String, ForeignKey


class Base(DeclarativeBase):
    pass



# user model
class User(Base):
    __tablename__ = "users"

    id : Mapped[int] = mapped_column(INTEGER,primary_key=True, autoincrement=True)
    google_sub : Mapped[str] = mapped_column(String(255), unique=True)
    name : Mapped[str] = mapped_column(String(100), nullable=False)
    email : Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password_hash : Mapped[str | None] = mapped_column(String(255))
    profile_link : Mapped[str | None] = mapped_column(String(255))
    videos = relationship("Video", back_populates="user")


class Video(Base):
    __tablename__ = "videos"
    
    id : Mapped[int] = mapped_column(INTEGER,primary_key=True, autoincrement=True)
    video_link : Mapped[str | None] = mapped_column(String(255))
    user_id: Mapped[int] = mapped_column(
        INTEGER,
        ForeignKey("users.id"),
        nullable=False
    )

    user = relationship("User", back_populates="videos")