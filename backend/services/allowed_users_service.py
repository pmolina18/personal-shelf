"""Servicio para leer y validar emails contra el fichero allowed_users.

Lee, parsea y serializa el fichero de texto plano que controla qué
emails pueden registrarse en la aplicación.
"""

from __future__ import annotations

import logging
from pathlib import Path

from backend.config import ALLOWED_USERS_PATH

logger = logging.getLogger(__name__)


class AllowedUsersService:
    """Lee y valida emails contra el fichero allowed_users."""

    def __init__(self, filepath: Path | None = None) -> None:
        """Inicializa con la ruta al fichero de usuarios permitidos.

        Args:
            filepath: Ruta al fichero. Si es None, usa ALLOWED_USERS_PATH de config.
        """
        self.filepath = filepath if filepath is not None else ALLOWED_USERS_PATH

    def is_allowed(self, email: str) -> bool:
        """Comprueba si el email está en la lista de permitidos (case-insensitive).

        Lee el fichero del disco en cada llamada para reflejar cambios
        inmediatamente tras un merge + redeploy.

        Args:
            email: Dirección de email a verificar.

        Returns:
            True si el email está en la lista, False en caso contrario.
        """
        try:
            content = self.filepath.read_text(encoding="utf-8")
        except FileNotFoundError:
            logger.error("Fichero allowed_users no encontrado: %s", self.filepath)
            return False

        allowed = self.parse(content)
        return email.strip().lower() in allowed

    def parse(self, content: str) -> list[str]:
        """Parsea el contenido del fichero a una lista de emails.

        Ignora líneas vacías y comentarios (líneas que empiezan con #).
        Elimina espacios en blanco y normaliza a lowercase.

        Args:
            content: Contenido del fichero como string.

        Returns:
            Lista de emails normalizados (lowercase, stripped).
        """
        result: list[str] = []
        for line in content.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            result.append(stripped.lower())
        return result

    def serialize(self, lines: list[str]) -> str:
        """Serializa una lista de líneas a texto plano.

        Cada línea se separa con \\n y el resultado termina con \\n final.

        Args:
            lines: Lista de líneas del fichero (emails, comentarios, vacías).

        Returns:
            Contenido del fichero como string.
        """
        return "\n".join(lines) + "\n"

    def parse_preserving(self, content: str) -> list[str]:
        """Parsea el contenido preservando comentarios y líneas vacías.

        Cada línea se limpia de espacios al inicio y final, pero se
        mantienen comentarios y líneas vacías en el resultado.

        Args:
            content: Contenido del fichero como string.

        Returns:
            Lista de todas las líneas (stripped), incluyendo comentarios y vacías.
        """
        return [line.strip() for line in content.splitlines()]

    def add_email(self, content: str, email: str) -> str:
        """Añade un email al final del contenido existente, preservando estructura.

        Mantiene comentarios y líneas vacías intactos. Asegura que el
        resultado termine con un salto de línea.

        Args:
            content: Contenido actual del fichero.
            email: Email a añadir.

        Returns:
            Nuevo contenido del fichero con el email añadido.
        """
        lines = self.parse_preserving(content)
        lines.append(email.strip().lower())
        return self.serialize(lines)
