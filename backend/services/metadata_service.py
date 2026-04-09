"""Servicio de búsqueda de metadatos en APIs externas (TMDB, Open Library).

Consulta TMDB para películas y series, y Open Library para libros,
devolviendo candidatos estructurados con título, año, creador,
descripción e imagen. Sigue el mismo patrón async que ImageService.
"""

from __future__ import annotations

import logging

import httpx

from backend.config import TMDB_API_KEY
from backend.schemas.media import MetadataCandidate

logger = logging.getLogger(__name__)

_MAX_CANDIDATES = 5


class MetadataService:
    """Busca metadatos en TMDB y Open Library.

    Servicio async puro sin dependencia de base de datos. Devuelve
    listas de MetadataCandidate que el router o MediaService consume.
    """

    async def search(self, title: str, media_type: str) -> list[MetadataCandidate]:
        """Busca candidatos de metadatos para un título y tipo.

        Enruta a TMDB para movies/series y a Open Library para books.

        Args:
            title: Título a buscar.
            media_type: Uno de "movie", "book", "series".

        Returns:
            Lista de hasta 5 MetadataCandidate. Lista vacía si no hay
            resultados o hay error.
        """
        try:
            if media_type == "book":
                return await self._search_open_library_metadata(title)

            tmdb_type = "tv" if media_type == "series" else "movie"
            return await self._search_tmdb_metadata(title, tmdb_type)
        except Exception:
            logger.exception(
                "Error searching metadata for '%s' (%s)", title, media_type
            )
            return []

    async def _search_tmdb_metadata(
        self, title: str, tmdb_type: str
    ) -> list[MetadataCandidate]:
        """Busca en TMDB y extrae título, año, creador, descripción e imagen.

        Para movies usa /search/movie y obtiene el director vía /movie/{id}/credits.
        Para series usa /search/tv y extrae created_by del resultado.

        Args:
            title: Título a buscar.
            tmdb_type: Tipo TMDB — "movie" o "tv".

        Returns:
            Lista de hasta 5 MetadataCandidate. Lista vacía si la API key
            no está configurada o hay error.
        """
        if not TMDB_API_KEY:
            logger.debug("TMDB API key not configured, skipping TMDB metadata search")
            return []

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"https://api.themoviedb.org/3/search/{tmdb_type}",
                    params={"api_key": TMDB_API_KEY, "query": title},
                )
                resp.raise_for_status()
                data = resp.json()

            results = data.get("results", [])[:_MAX_CANDIDATES]
            if not results:
                return []

            candidates: list[MetadataCandidate] = []
            for item in results:
                candidate = await self._parse_tmdb_result(item, tmdb_type)
                candidates.append(candidate)

            return candidates
        except Exception:
            logger.exception("TMDB metadata search failed for '%s'", title)
            return []

    async def _parse_tmdb_result(
        self, item: dict, tmdb_type: str
    ) -> MetadataCandidate:
        """Parsea un resultado individual de TMDB a MetadataCandidate.

        Args:
            item: Dict con datos de un resultado de TMDB.
            tmdb_type: "movie" o "tv".

        Returns:
            MetadataCandidate con los campos extraídos.
        """
        if tmdb_type == "movie":
            candidate_title = item.get("title") or ""
            date_str = item.get("release_date") or ""
        else:
            candidate_title = item.get("name") or ""
            date_str = item.get("first_air_date") or ""

        year = int(date_str[:4]) if len(date_str) >= 4 else None

        overview = item.get("overview") or None
        description = overview if overview else None

        # Imagen de poster
        poster_path = item.get("poster_path")
        image_url = (
            f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
        )

        # Creador: director para movies (vía credits), created_by para series
        creator = await self._get_tmdb_creator(item, tmdb_type)

        return MetadataCandidate(
            title=candidate_title,
            year=year,
            creator=creator,
            description=description,
            image_url=image_url,
        )

    async def _get_tmdb_creator(self, item: dict, tmdb_type: str) -> str | None:
        """Obtiene el creador de un resultado TMDB.

        Para movies, hace una llamada adicional a /movie/{id}/credits
        y busca el director en el crew. Para series, extrae created_by
        directamente del resultado de búsqueda.

        Args:
            item: Dict con datos de un resultado de TMDB.
            tmdb_type: "movie" o "tv".

        Returns:
            Nombre del creador/director, o None si no se encuentra.
        """
        if tmdb_type == "tv":
            created_by = item.get("created_by") or []
            if created_by and isinstance(created_by, list):
                return created_by[0].get("name") or None
            return None

        # Para movies, buscar director en credits
        movie_id = item.get("id")
        if not movie_id:
            return None

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"https://api.themoviedb.org/3/movie/{movie_id}/credits",
                    params={"api_key": TMDB_API_KEY},
                )
                resp.raise_for_status()
                credits_data = resp.json()

            crew = credits_data.get("crew") or []
            for member in crew:
                if member.get("job") == "Director":
                    return member.get("name") or None
            return None
        except Exception:
            logger.exception("Failed to fetch credits for movie %s", movie_id)
            return None

    async def _search_open_library_metadata(
        self, title: str
    ) -> list[MetadataCandidate]:
        """Busca en Open Library y extrae título, año, autor, descripción e imagen.

        Args:
            title: Título del libro a buscar.

        Returns:
            Lista de hasta 5 MetadataCandidate. Lista vacía si no hay
            resultados o hay error.
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://openlibrary.org/search.json",
                    params={"title": title, "limit": _MAX_CANDIDATES},
                )
                resp.raise_for_status()
                data = resp.json()

            docs = data.get("docs", [])[:_MAX_CANDIDATES]
            if not docs:
                return []

            candidates: list[MetadataCandidate] = []
            for doc in docs:
                candidate_title = doc.get("title") or ""

                year = doc.get("first_publish_year")
                if year is not None:
                    year = int(year)

                # Autor: primer elemento de author_name
                author_names = doc.get("author_name") or []
                creator = author_names[0] if author_names else None

                # Descripción: primer elemento de subject
                subjects = doc.get("subject") or []
                description = subjects[0] if subjects else None

                # Imagen de portada
                cover_id = doc.get("cover_i")
                image_url = (
                    f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
                    if cover_id
                    else None
                )

                candidates.append(
                    MetadataCandidate(
                        title=candidate_title,
                        year=year,
                        creator=creator,
                        description=description,
                        image_url=image_url,
                    )
                )

            return candidates
        except Exception:
            logger.exception("Open Library metadata search failed for '%s'", title)
            return []
