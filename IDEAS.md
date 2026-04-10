# Ideas

Backlog de ideas para Personal Shelf. Cuando quieras que convierta una idea en spec, dime cuál.

Cada idea sigue este formato:

```
## [IDEA-XX] Título corto

- Tipo: feature | bugfix | mejora | infra
- Prioridad: alta | media | baja
- Descripción: Qué quieres lograr, en 2-3 frases.
- Contexto: (opcional) Archivos relevantes, APIs externas, inspiración, etc.
- Notas: (opcional) Restricciones, dudas, o cosas que ya tienes claras.
```

---

<!-- Pega tus ideas debajo de esta línea -->

## [IDEA-1] Allowed Users ✅ COMPLETADA → `.kiro/specs/allowed-users/`

- Tipo: feature
- Prioridad: alta
- Descripción: antes de publicarla para todo el mundo, me gustaría ir poco a poco y tener como una especie de Lista de usuarios permitidos.
- Contexto: auth system
- Notas: He pensado que lo mejor sería tener un fichero llamado allowed_users en el que guardar una lista de usuarios permitidos, y antes de permitir crear un usuario, hay que validar si existe en esta lista de usuarios permitidos. También me gustaría que si un usuario no está en esta lista y quiere añadirse, cree una issue en Github (o un PR, lo que prefieras) para que yo cuando lo vea y lo mergee se añada para el futuro.
- Estado: Implementada el 2026-04-09. Spec completa + código desplegable.

---

## [IDEA-2] Buzón de sugerencias

- Tipo: feature
- Prioridad: media
- Descripción: me gustaría permitir que los primeros usuarios, pudiesen tener un sitio donde añadir sugerencias o peticiones de features nuevas
- Contexto: esto serían nuevos endpoints y nuevas vistas
- Notas: (opcional) Esas peticiones nuevas que escribiesen los usuarios de nuevas features o bugs que reporten, automáticamente tendrían que crear issues en Github para que de nuevo, yo pudiese priorizartelos y los fueses resolviendo uno a uno

---

## [IDEA-3] Recomendaciones entre amigos

- Tipo: feature
- Prioridad: alta
- Descripción: me gustaría que existiese la opción de recomendarle a tus amigos alguna película o item que tu hayas visto o estés viendo
- Contexto: en la ventana de catalogo, dentro de cada item tuvieses un botón para recomendar a amigos
- Notas: (opcional) Estaría bien que tuvieses un sistema de mensajes desde la pantalla de catálogo, con una "bolita" en la que aparezca el número de recomendaciones que tienes etc

---

## [IDEA-4] Pantalla de login dedicada

- Tipo: feature
- Prioridad: media
- Descripción: Crear una pantalla de login única y dedicada. Si el usuario no tiene token de acceso válido, debería ser redirigido automáticamente a esta pantalla. Centralizar todo el flujo de autenticación en un solo punto de entrada.
- Contexto: Actualmente el login se gestiona con el social login de Google. La idea es tener una vista `/login` que sea el punto de entrada obligatorio para usuarios no autenticados.
- Notas: Incluir redirección automática desde cualquier ruta protegida. Después del login exitoso, redirigir al usuario a la ruta que intentaba acceder originalmente.

---
