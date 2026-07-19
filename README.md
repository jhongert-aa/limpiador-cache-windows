# Limpiador de Caché y Temporales (Windows)

App de escritorio para liberar espacio borrando cachés y temporales de forma segura,
con vista previa de tamaños y confirmación antes de borrar nada.

## Qué limpia

- **VS Code**: carpetas de caché (`Cache`, `CachedData`, `GPUCache`, `CachedExtensionVSIXs`, `logs`, etc.)
- **Claude Code (extensión de VS Code)**: carpeta de `globalStorage` de la extensión (⚠ puede cerrar tu sesión de la extensión)
- **Claude Code (CLI)**: `~/.claude/statsig`, `~/.claude/shell-snapshots`, `~/.claude/logs` — **no** toca `projects`, `todos` ni tu configuración
- **pip**: ejecuta `pip cache purge` (el método oficial de pip)
- **Temporales de usuario**: contenido de `%TEMP%` / `%TMP%`
- **Temporales de sistema**: contenido de `C:\Windows\Temp` (requiere Administrador)
- **Prefetch**: `C:\Windows\Prefetch` (requiere Administrador; Windows lo regenera solo)
- **Google Chrome**: solo carpetas de caché (`Cache`, `Code Cache`, `GPUCache`, `Service Worker\CacheStorage`, etc.) de **todos los perfiles**. Nunca toca `Login Data`, `Cookies`, `History` ni `Bookmarks` — tus contraseñas e historial quedan intactos.
- **Microsoft Edge**: igual que Chrome, solo caché de todos los perfiles.
- **Mozilla Firefox**: carpeta `cache2` de todos los perfiles.
- **Firestorm** (viewer de Second Life): carpeta `cache`.
- **Fortnite**: caché de manifiestos/instalación de descargas.
- **Epic Games Launcher**: caché web (`webcache*`).
- **Zotero**: carpeta `cache2` de todos los perfiles.
- **CapCut**: caché y caché de CEF.

Para Chrome, Edge y Firefox hay una casilla "Cerrar antes de limpiar" que cierra el navegador (sin guardar) justo antes de borrar, para poder liberar los archivos que estén en uso.

Los archivos que estén en uso/bloqueados se omiten automáticamente (se listan en el registro) en vez de fallar.

## Ejecutar en modo desarrollo

Requiere Python 3.9+ (no se necesitan librerías externas):

```
python main.py
```

## Compilar a .exe

```
.\build.ps1
```

Genera `dist\LimpiadorCache.exe`, un ejecutable independiente que **pide permisos de Administrador al abrirse** (necesario para limpiar Prefetch y el Temp de sistema).

## Uso

1. Abre la app (como Administrador si quieres limpiar Prefetch / Temp de sistema).
2. Pulsa **Analizar** para ver cuánto espacio ocupa cada categoría.
3. Marca las categorías que quieras limpiar. Si vas a limpiar Chrome, activa "Cerrar Google Chrome antes de limpiar" para poder borrar los archivos que estén abiertos.
4. Pulsa **Eliminar seleccionado**, revisa el resumen y las advertencias, y confirma.
5. Vuelve a pulsar **Analizar** para verificar el espacio liberado.
