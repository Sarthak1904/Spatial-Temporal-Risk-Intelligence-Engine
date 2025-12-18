"""H3 polygon registry model."""

from geoalchemy2 import Geometry
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class H3Cell(Base):
    """Stores H3 index geometry for tile rendering and joins."""

    __tablename__ = "h3_cells"

    h3_index: Mapped[str] = mapped_column(String(32), primary_key=True)
    resolution: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    geom: Mapped[str] = mapped_column(Geometry("POLYGON", srid=4326, spatial_index=True), nullable=False)
