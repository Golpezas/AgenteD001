"""
Repositorio de Company — operaciones CRUD específicas.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.repositories.base import BaseRepository


class CompanyRepository(BaseRepository[Company]):
    """Repositorio para el modelo Company."""

    def __init__(self, session: AsyncSession):
        super().__init__(Company, session)
