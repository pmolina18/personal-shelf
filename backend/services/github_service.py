"""Servicio async para interactuar con la API REST de GitHub.

Crea Pull Requests de solicitud de acceso para añadir emails
al fichero allowed_users del repositorio.
"""

from __future__ import annotations

import base64
import logging
import re

import httpx
from fastapi import HTTPException

from backend.config import GITHUB_DEFAULT_BRANCH, GITHUB_REPO, GITHUB_TOKEN
from backend.services.allowed_users_service import AllowedUsersService

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"


class GitHubService:
    """Crea Pull Requests en GitHub para solicitudes de acceso."""

    def __init__(self) -> None:
        """Lee configuración de variables de entorno.

        Lee GITHUB_TOKEN, GITHUB_REPO y GITHUB_DEFAULT_BRANCH de config.
        Registra un warning si TOKEN o REPO están vacíos.
        """
        self.token = GITHUB_TOKEN
        self.repo = GITHUB_REPO
        self.default_branch = GITHUB_DEFAULT_BRANCH

        if not self.token:
            logger.warning("GITHUB_TOKEN no está configurado")
        if not self.repo:
            logger.warning("GITHUB_REPO no está configurado")

    @property
    def is_configured(self) -> bool:
        """True si GITHUB_TOKEN y GITHUB_REPO están configurados.

        Returns:
            True si ambos valores son non-empty.
        """
        return bool(self.token) and bool(self.repo)

    def _headers(self) -> dict[str, str]:
        """Construye las cabeceras de autenticación para la API de GitHub.

        Returns:
            Dict con cabeceras Authorization y Accept.
        """
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
        }

    def _sanitize_branch_name(self, email: str) -> str:
        """Convierte un email a un nombre de rama Git válido.

        Reemplaza @ y . con guiones, convierte a lowercase y elimina
        caracteres inválidos para nombres de rama.

        Args:
            email: Dirección de email a sanitizar.

        Returns:
            Nombre de rama sanitizado.
        """
        sanitized = email.lower()
        sanitized = sanitized.replace("@", "-").replace(".", "-")
        sanitized = re.sub(r"[^a-z0-9\-]", "", sanitized)
        return sanitized

    async def create_access_request_pr(self, email: str) -> dict:
        """Crea un PR que añade el email al fichero allowed_users.

        Pasos:
        1. Verificar que no existe un PR abierto para este email.
        2. Obtener el contenido actual de allowed_users desde la rama principal.
        3. Añadir el email al contenido usando AllowedUsersService.
        4. Crear una rama nueva (access-request/<email-sanitizado>).
        5. Actualizar el fichero en la rama nueva con el email añadido.
        6. Crear el PR contra la rama principal.

        Args:
            email: Email del solicitante.

        Returns:
            Dict con 'number' y 'html_url' del PR creado.

        Raises:
            HTTPException: 409 si ya existe un PR abierto para este email.
            HTTPException: 502 si la API de GitHub falla.
        """
        try:
            # 1. Verificar PR existente
            if await self._check_existing_pr(email):
                raise HTTPException(
                    status_code=409,
                    detail="Ya tienes una solicitud de acceso pendiente.",
                )

            # 2. Obtener contenido actual del fichero
            file_path = "allowed_users"
            content, sha = await self._get_file_content(
                file_path, self.default_branch
            )

            # 3. Añadir email al contenido
            allowed_svc = AllowedUsersService()
            new_content = allowed_svc.add_email(content, email)

            # 4. Crear rama nueva
            sanitized = self._sanitize_branch_name(email)
            branch_name = f"access-request/{sanitized}"
            await self._create_branch(branch_name, self.default_branch)

            # 5. Actualizar fichero en la rama nueva
            commit_message = f"Añadir {email} a allowed_users"
            await self._create_or_update_file(
                file_path, new_content, sha, branch_name, commit_message
            )

            # 6. Crear PR
            title = f"Solicitud de acceso: {email}"
            body = (
                f"Solicitud automática de acceso para {email}.\n\n"
                "Mergea este PR para añadir el email a la lista de "
                "usuarios permitidos."
            )
            pr_data = await self._create_pull_request(
                title, body, branch_name, self.default_branch
            )

            return {
                "number": pr_data["number"],
                "html_url": pr_data["html_url"],
            }

        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Error al crear PR de solicitud de acceso: %s", exc)
            raise HTTPException(
                status_code=502,
                detail="No se pudo procesar la solicitud. Inténtalo más tarde.",
            ) from exc

    async def _check_existing_pr(self, email: str) -> bool:
        """Verifica si ya existe un PR abierto para este email.

        Args:
            email: Email a buscar en los títulos de PRs abiertos.

        Returns:
            True si existe un PR abierto cuyo título contiene el email.
        """
        url = f"{GITHUB_API_BASE}/repos/{self.repo}/pulls"
        params = {"state": "open"}
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                url, headers=self._headers(), params=params
            )
            resp.raise_for_status()
        for pr in resp.json():
            if email.lower() in pr.get("title", "").lower():
                return True
        return False

    async def _get_file_content(self, path: str, ref: str) -> tuple[str, str]:
        """Obtiene el contenido y SHA de un fichero del repositorio.

        Args:
            path: Ruta del fichero dentro del repositorio.
            ref: Rama o referencia desde la que leer.

        Returns:
            Tupla (contenido decodificado, sha del fichero).
        """
        url = f"{GITHUB_API_BASE}/repos/{self.repo}/contents/{path}"
        params = {"ref": ref}
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                url, headers=self._headers(), params=params
            )
            resp.raise_for_status()
        data = resp.json()
        content_b64 = data["content"]
        decoded = base64.b64decode(content_b64).decode("utf-8")
        return decoded, data["sha"]

    async def _create_branch(self, branch_name: str, from_ref: str) -> None:
        """Crea una rama nueva a partir de una referencia.

        Obtiene el SHA de la referencia origen y crea la nueva rama
        apuntando al mismo commit.

        Args:
            branch_name: Nombre de la nueva rama.
            from_ref: Rama origen de la que obtener el SHA.
        """
        # Obtener SHA de la rama origen
        ref_url = (
            f"{GITHUB_API_BASE}/repos/{self.repo}/git/ref/heads/{from_ref}"
        )
        async with httpx.AsyncClient() as client:
            ref_resp = await client.get(ref_url, headers=self._headers())
            ref_resp.raise_for_status()
        sha = ref_resp.json()["object"]["sha"]

        # Crear la nueva rama
        create_url = f"{GITHUB_API_BASE}/repos/{self.repo}/git/refs"
        payload = {
            "ref": f"refs/heads/{branch_name}",
            "sha": sha,
        }
        async with httpx.AsyncClient() as client:
            create_resp = await client.post(
                create_url, headers=self._headers(), json=payload
            )
            create_resp.raise_for_status()

    async def _create_or_update_file(
        self,
        path: str,
        content: str,
        sha: str,
        branch: str,
        message: str,
    ) -> None:
        """Crea o actualiza un fichero en una rama específica.

        El contenido se codifica en base64 antes de enviarlo a la API.

        Args:
            path: Ruta del fichero dentro del repositorio.
            content: Contenido del fichero como texto plano.
            sha: SHA actual del fichero (para actualización).
            branch: Rama donde crear/actualizar el fichero.
            message: Mensaje del commit.
        """
        url = f"{GITHUB_API_BASE}/repos/{self.repo}/contents/{path}"
        encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
        payload = {
            "message": message,
            "content": encoded,
            "sha": sha,
            "branch": branch,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.put(
                url, headers=self._headers(), json=payload
            )
            resp.raise_for_status()

    async def _create_pull_request(
        self, title: str, body: str, head: str, base: str
    ) -> dict:
        """Crea un Pull Request en el repositorio.

        Args:
            title: Título del PR.
            body: Descripción del PR.
            head: Rama origen (la que contiene los cambios).
            base: Rama destino (contra la que se crea el PR).

        Returns:
            Dict con la respuesta JSON de la API de GitHub.
        """
        url = f"{GITHUB_API_BASE}/repos/{self.repo}/pulls"
        payload = {
            "title": title,
            "body": body,
            "head": head,
            "base": base,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url, headers=self._headers(), json=payload
            )
            resp.raise_for_status()
        return resp.json()