# -*- coding: utf-8 -*-
"""MC Studio path discovery utilities (Windows only)."""

import os
import sys


def get_mcs_download_path():
    if sys.platform != 'win32':
        return None
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Netease\MCStudio") as key:
            path, _ = winreg.QueryValueEx(key, "DownloadPath")
            return path
    except Exception:
        return None


def get_mcs_install_path():
    if sys.platform != 'win32':
        return None
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Netease\MCStudio") as key:
            path, _ = winreg.QueryValueEx(key, "InstallPath")
            return path
    except Exception:
        pass
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Netease\MCStudio") as key:
            path, _ = winreg.QueryValueEx(key, "InstallPath")
            return path
    except Exception:
        return None


def get_latest_engine_dir():
    download_path = get_mcs_download_path()
    if not download_path:
        return None
    engine_root = os.path.join(download_path, "game", "MinecraftPE_Netease")
    if not os.path.isdir(engine_root):
        return None
    dirs = [d for d in os.listdir(engine_root)
            if os.path.isdir(os.path.join(engine_root, d)) and not d.startswith("PCLauncher")]
    if not dirs:
        return None
    try:
        from packaging import version
        dirs.sort(key=lambda x: version.parse(x), reverse=True)
    except ImportError:
        dirs.sort(reverse=True)
    return os.path.join(engine_root, dirs[0])


def get_minecraft_exe():
    engine_dir = get_latest_engine_dir()
    if not engine_dir:
        return None
    exe = os.path.join(engine_dir, "Minecraft.Windows.exe")
    return exe if os.path.isfile(exe) else None


def get_editor_exe():
    download_path = get_mcs_download_path()
    if not download_path:
        return None
    exe = os.path.join(download_path, "MCX64Editor", "MC_Editor.exe")
    return exe if os.path.isfile(exe) else None


def get_safaia_exe():
    install_path = get_mcs_install_path()
    if not install_path:
        return None
    exe = os.path.join(install_path, "safaia", "safaia_server.exe")
    return exe if os.path.isfile(exe) else None


def setup_runtime(project_root):
    """Generate a .cppconfig under <project_root>/.runtime and return its path.

    Replicates mcpywrap's gen_runtime_config logic without requiring mcpywrap.
    """
    import json
    import uuid

    # --- Read studio.json ---
    studio_json = os.path.join(project_root, "studio.json")
    if not os.path.isfile(studio_json):
        raise RuntimeError("studio.json not found in %s" % project_root)
    with open(studio_json, "r", encoding="utf-8") as f:
        studio = json.load(f)

    pkg_name = studio.get("NameSpace", "")
    world_name = studio.get("EditName", "World")
    game_type = studio.get("GameType", 1)
    world_type = studio.get("WorldType", 1)
    seed = studio.get("Seed", "")

    # --- Discover packs ---
    beh_dir = res_dir = None
    for item in os.listdir(project_root):
        lower = item.lower()
        if lower.startswith("behavior_pack") or lower.startswith("behaviorpack"):
            beh_dir = item
        elif lower.startswith("resource_pack") or lower.startswith("resourcepack"):
            res_dir = item
    beh_dir = beh_dir or "behavior_pack"
    res_dir = res_dir or "resource_pack"

    # --- Ensure symlinks in AppData ---
    appdata = os.environ.get("APPDATA", "")
    netease_root = os.path.join(appdata, "MinecraftPE_Netease", "games", "com.netease")

    def _ensure_junction(link_parent, link_name, target):
        link_path = os.path.join(link_parent, link_name)
        if not os.path.exists(link_path):
            import subprocess
            subprocess.check_call(
                ["cmd", "/c", "mklink", "/J", link_path, target],
                stdout=open(os.devnull, "w"), stderr=open(os.devnull, "w")
            )

    beh_link_name = beh_dir  # e.g. "behavior_pack_WiETU4v9"
    res_link_name = res_dir
    _ensure_junction(
        os.path.join(netease_root, "behavior_packs"), beh_link_name,
        os.path.join(project_root, beh_dir)
    )
    _ensure_junction(
        os.path.join(netease_root, "resource_packs"), res_link_name,
        os.path.join(project_root, res_dir)
    )

    # --- Engine version + paths ---
    download_path = get_mcs_download_path() or ""
    engine_dir = get_latest_engine_dir()
    engine_version = os.path.basename(engine_dir) if engine_dir else "0.0.0"
    skin_path = os.path.join(download_path, "componentcache", "support", "steve", "steve.png")

    # --- Build config ---
    level_id = str(uuid.uuid4())
    data = {
        "version": engine_version,
        "MainComponentId": pkg_name,
        "LocalComponentPathsDict": {},
        "LocalComponentPaths": None,
        "world_info": {
            "level_id": level_id,
            "game_type": game_type,
            "difficulty": 2,
            "permission_level": 1,
            "cheat": True,
            "cheat_info": {
                "pvp": True,
                "show_coordinates": True,
                "always_day": False,
                "daylight_cycle": True,
                "fire_spreads": True,
                "tnt_explodes": True,
                "keep_inventory": False,
                "mob_spawn": True,
                "natural_regeneration": True,
                "mob_loot": True,
                "mob_griefing": True,
                "tile_drops": True,
                "entities_drop_loot": True,
                "weather_cycle": True,
                "command_blocks_enabled": True,
                "random_tick_speed": 1,
                "experimental_holiday": False,
                "experimental_biomes": False,
                "fancy_bubbles": False
            },
            "resource_packs": [res_link_name],
            "behavior_packs": [beh_link_name],
            "name": world_name,
            "world_type": world_type,
            "start_with_map": False,
            "bonus_items": False,
            "seed": seed
        },
        "room_info": {
            "ip": "", "port": 0, "muiltClient": False, "room_name": "",
            "token": "", "room_id": 0, "host_id": 0, "allow_pe": True,
            "max_player": 0, "visibility_mode": 0, "is_pe": False,
            "tag_ids": None, "item_ids": []
        },
        "skin_info": {"skin": skin_path, "slim": False}
    }

    runtime_dir = os.path.join(project_root, ".runtime")
    if not os.path.isdir(runtime_dir):
        os.makedirs(runtime_dir)

    config_path = os.path.join(runtime_dir, str(uuid.uuid4()) + ".cppconfig")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return config_path


def find_latest_cppconfig(project_root):
    """Return path to the newest .cppconfig under <project_root>/.runtime, or None."""
    import json
    runtime_dir = os.path.join(project_root, ".runtime")
    if not os.path.isdir(runtime_dir):
        return None
    instances = []
    for f in os.listdir(runtime_dir):
        if not f.endswith(".cppconfig"):
            continue
        fpath = os.path.join(runtime_dir, f)
        try:
            with open(fpath, "r", encoding="utf-8") as fp:
                cfg = json.load(fp)
            if cfg.get("world_info", {}).get("level_id"):
                instances.append((os.path.getctime(fpath), fpath))
        except Exception:
            continue
    if not instances:
        return None
    instances.sort(reverse=True)
    return instances[0][1]
