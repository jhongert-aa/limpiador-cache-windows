"""Lógica de escaneo y borrado de cachés/temporales en Windows."""
import os
import sys
import ctypes
import subprocess


def expand(path):
    return os.path.expandvars(path)


def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_as_admin():
    params = " ".join(f'"{a}"' for a in sys.argv)
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
    sys.exit(0)


def human_size(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def dir_size(path):
    total = 0
    if not os.path.isdir(path):
        return total
    for root, _dirs, files in os.walk(path, onerror=lambda e: None):
        for f in files:
            fp = os.path.join(root, f)
            try:
                total += os.path.getsize(fp)
            except OSError:
                pass
    return total


def delete_dir_contents(path):
    """Borra archivos y subcarpetas dentro de `path`, dejando `path` vacío pero existente.
    Ignora archivos bloqueados/en uso. Devuelve (bytes_borrados, lista_de_errores)."""
    deleted = 0
    errors = []
    if not os.path.isdir(path):
        return deleted, errors
    for root, dirs, files in os.walk(path, topdown=False):
        for f in files:
            fp = os.path.join(root, f)
            try:
                size = os.path.getsize(fp)
                os.remove(fp)
                deleted += size
            except OSError as e:
                errors.append(f"{fp}: {e}")
        for d in dirs:
            dp = os.path.join(root, d)
            try:
                os.rmdir(dp)
            except OSError:
                pass
    return deleted, errors


def discover_chrome_profiles():
    base = expand(r"%LOCALAPPDATA%\Google\Chrome\User Data")
    subpaths = [
        "Cache",
        "Code Cache",
        "GPUCache",
        "Media Cache",
        os.path.join("Service Worker", "CacheStorage"),
        "DawnCache",
        "DawnGraphiteCache",
        "DawnWebGPUCache",
        "GrShaderCache",
        "ShaderCache",
    ]
    targets = []
    if os.path.isdir(base):
        for entry in os.listdir(base):
            full = os.path.join(base, entry)
            if not os.path.isdir(full):
                continue
            if entry == "Default" or entry.startswith("Profile ") or entry == "Guest Profile":
                for sp in subpaths:
                    tp = os.path.join(full, sp)
                    if os.path.isdir(tp):
                        targets.append(tp)
    return targets


def discover_edge_profiles():
    base = expand(r"%LOCALAPPDATA%\Microsoft\Edge\User Data")
    subpaths = [
        "Cache",
        "Code Cache",
        "GPUCache",
        "Media Cache",
        os.path.join("Service Worker", "CacheStorage"),
        "DawnCache",
        "DawnGraphiteCache",
        "DawnWebGPUCache",
        "GrShaderCache",
        "ShaderCache",
    ]
    targets = []
    if os.path.isdir(base):
        for entry in os.listdir(base):
            full = os.path.join(base, entry)
            if not os.path.isdir(full):
                continue
            if entry == "Default" or entry.startswith("Profile ") or entry == "Guest Profile":
                for sp in subpaths:
                    tp = os.path.join(full, sp)
                    if os.path.isdir(tp):
                        targets.append(tp)
    return targets


def discover_firefox_profiles():
    base = expand(r"%LOCALAPPDATA%\Mozilla\Firefox\Profiles")
    targets = []
    if os.path.isdir(base):
        for entry in os.listdir(base):
            tp = os.path.join(base, entry, "cache2")
            if os.path.isdir(tp):
                targets.append(tp)
    return targets


def discover_zotero_profiles():
    base = expand(r"%LOCALAPPDATA%\Zotero\Zotero\Profiles")
    targets = []
    if os.path.isdir(base):
        for entry in os.listdir(base):
            tp = os.path.join(base, entry, "cache2")
            if os.path.isdir(tp):
                targets.append(tp)
    return targets


def discover_epic_launcher_webcache():
    base = expand(r"%LOCALAPPDATA%\EpicGamesLauncher\Saved")
    targets = []
    if os.path.isdir(base):
        for entry in os.listdir(base):
            if entry.lower().startswith("webcache"):
                full = os.path.join(base, entry)
                if os.path.isdir(full):
                    targets.append(full)
    return targets


def discover_claude_ext():
    base = expand(r"%APPDATA%\Code\User\globalStorage")
    targets = []
    if os.path.isdir(base):
        for entry in os.listdir(base):
            low = entry.lower()
            if "claude" in low or "anthropic" in low:
                full = os.path.join(base, entry)
                if os.path.isdir(full):
                    targets.append(full)
    return targets


def pip_cache_dir():
    for cmd in (["pip", "cache", "dir"], ["py", "-m", "pip", "cache", "dir"]):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            p = r.stdout.strip()
            if p and os.path.isdir(p):
                return p
        except (FileNotFoundError, OSError):
            continue
    return None


def pip_cache_purge():
    log = []
    for cmd in (["pip", "cache", "purge"], ["py", "-m", "pip", "cache", "purge"]):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            out = (r.stdout.strip() or r.stderr.strip())
            log.append(f"{' '.join(cmd)} -> {out}")
        except FileNotFoundError:
            continue
        except OSError as e:
            log.append(f"{' '.join(cmd)} -> error: {e}")
    if not log:
        log.append("No se encontró pip en el sistema.")
    return log


def kill_process(image_name):
    try:
        subprocess.run(
            ["taskkill", "/IM", image_name, "/F"],
            capture_output=True, text=True, timeout=15,
        )
    except OSError:
        pass


def kill_chrome():
    kill_process("chrome.exe")


def kill_edge():
    kill_process("msedge.exe")


def kill_firefox():
    kill_process("firefox.exe")


CLOSE_BEFORE_CLEAN = {
    "chrome": (kill_chrome, "Cerrar Google Chrome antes de limpiar (recomendado)"),
    "edge": (kill_edge, "Cerrar Microsoft Edge antes de limpiar (recomendado)"),
    "firefox": (kill_firefox, "Cerrar Mozilla Firefox antes de limpiar (recomendado)"),
}


CATEGORIES = [
    {
        "key": "vscode",
        "label": "VS Code - Caché",
        "requires_admin": False,
        "static": [
            r"%APPDATA%\Code\Cache",
            r"%APPDATA%\Code\CachedData",
            r"%APPDATA%\Code\Code Cache",
            r"%APPDATA%\Code\CachedExtensionVSIXs",
            r"%APPDATA%\Code\GPUCache",
            r"%APPDATA%\Code\Service Worker\CacheStorage",
            r"%APPDATA%\Code\logs",
        ],
    },
    {
        "key": "claude_ext",
        "label": "Claude Code (extensión de VS Code)",
        "requires_admin": False,
        "discover": discover_claude_ext,
        "warning": "Puede borrar configuración/sesión guardada de la extensión; "
                   "quizás debas volver a iniciar sesión en Claude Code dentro de VS Code.",
    },
    {
        "key": "claude_cli",
        "label": "Claude Code (CLI de terminal)",
        "requires_admin": False,
        "static": [
            r"%USERPROFILE%\.claude\statsig",
            r"%USERPROFILE%\.claude\shell-snapshots",
            r"%USERPROFILE%\.claude\logs",
        ],
    },
    {
        "key": "pip",
        "label": "pip - Caché de paquetes",
        "requires_admin": False,
        "kind": "pip",
    },
    {
        "key": "temp_user",
        "label": "Temporales de usuario (%TEMP% / %TMP%)",
        "requires_admin": False,
        "static": [r"%TEMP%"],
    },
    {
        "key": "temp_system",
        "label": "Temporales de sistema (C:\\Windows\\Temp)",
        "requires_admin": True,
        "static": [r"%WINDIR%\Temp"],
    },
    {
        "key": "prefetch",
        "label": "Prefetch (C:\\Windows\\Prefetch)",
        "requires_admin": True,
        "static": [r"%WINDIR%\Prefetch"],
        "warning": "Windows lo regenera automáticamente; solo puede causar una breve "
                   "lentitud al abrir programas justo después.",
    },
    {
        "key": "chrome",
        "label": "Google Chrome - Caché (todos los perfiles)",
        "requires_admin": False,
        "discover": discover_chrome_profiles,
        "warning": "No borra contraseñas, cookies, historial ni marcadores. Cierra Chrome "
                   "antes de limpiar para poder borrar los archivos que estén en uso.",
    },
    {
        "key": "edge",
        "label": "Microsoft Edge - Caché (todos los perfiles)",
        "requires_admin": False,
        "discover": discover_edge_profiles,
        "warning": "No borra contraseñas, cookies, historial ni marcadores. Cierra Edge "
                   "antes de limpiar para poder borrar los archivos que estén en uso.",
    },
    {
        "key": "firefox",
        "label": "Mozilla Firefox - Caché (todos los perfiles)",
        "requires_admin": False,
        "discover": discover_firefox_profiles,
        "warning": "No borra contraseñas, cookies, historial ni marcadores. Cierra Firefox "
                   "antes de limpiar para poder borrar los archivos que estén en uso.",
    },
    {
        "key": "firestorm",
        "label": "Firestorm (viewer de Second Life)",
        "requires_admin": False,
        "static": [
            r"%LOCALAPPDATA%\Firestorm_x64\cache",
            r"%LOCALAPPDATA%\Firestorm_x86\cache",
        ],
    },
    {
        "key": "fortnite",
        "label": "Fortnite - Caché de descargas",
        "requires_admin": False,
        "static": [
            r"%LOCALAPPDATA%\FortniteGame\Saved\PersistentDownloadDir\ManifestCache",
            r"%LOCALAPPDATA%\FortniteGame\Saved\PersistentDownloadDir\IoStore\InstallCache",
        ],
    },
    {
        "key": "epic_launcher",
        "label": "Epic Games Launcher - Caché web",
        "requires_admin": False,
        "discover": discover_epic_launcher_webcache,
    },
    {
        "key": "zotero",
        "label": "Zotero - Caché (todos los perfiles)",
        "requires_admin": False,
        "discover": discover_zotero_profiles,
    },
    {
        "key": "capcut",
        "label": "CapCut - Caché",
        "requires_admin": False,
        "static": [
            r"%LOCALAPPDATA%\CapCut\User Data\Cache",
            r"%LOCALAPPDATA%\CapCut\User Data\CEF",
        ],
    },
]


def scan():
    """Devuelve dict key -> {label, warning, requires_admin, targets:[(path,size)], total}"""
    result = {}
    for cat in CATEGORIES:
        entry = {
            "label": cat["label"],
            "warning": cat.get("warning"),
            "requires_admin": cat.get("requires_admin", False),
            "targets": [],
            "total": 0,
        }
        if cat.get("kind") == "pip":
            p = pip_cache_dir()
            if p:
                size = dir_size(p)
                entry["targets"].append((p, size))
                entry["total"] = size
        else:
            paths = list(cat.get("static", []))
            if "discover" in cat:
                paths += cat["discover"]()
            for raw in paths:
                p = expand(raw)
                if os.path.isdir(p):
                    size = dir_size(p)
                    entry["targets"].append((p, size))
                    entry["total"] += size
        result[cat["key"]] = entry
    return result


def delete_category(key, scanned_entry, log_fn):
    if key == "pip":
        for line in pip_cache_purge():
            log_fn(line)
        return
    for path, _size in scanned_entry["targets"]:
        deleted, errors = delete_dir_contents(path)
        log_fn(f"{path} -> liberado {human_size(deleted)}")
        for e in errors[:5]:
            log_fn(f"  omitido (en uso): {e}")
        if len(errors) > 5:
            log_fn(f"  ...y {len(errors) - 5} archivo(s) más en uso, omitidos.")
