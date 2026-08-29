# Game-development role classifier.
# Determines whether an internship belongs on the dedicated "Game Dev" tab.
#
# A role is game-dev if it comes from a known game studio/publisher, OR was
# scraped from a game-industry board (GameJobs), OR its title/description
# explicitly mentions game development (gameplay, engine, graphics, etc.).

import re

# Known game studios / publishers / companies (company matches, case-insensitive).
GAME_COMPANIES = {
    # AAA / publishers
    "riot games", "riot", "epic games", "epic", "bungie", "naughty dog",
    "naughtydog", "bandai namco", "nintendo", "ubisoft", "blizzard",
    "activision", "activision blizzard", "electronic arts", "ea", "2k",
    "2k games", "take-two", "insomniac games", "square enix", "capcom",
    "sega", "playstation", "sony interactive", "xbox", "microsoft gaming",
    "valve", "rockstar", "rockstar games", "bethesda", "cd projekt red",
    "supercell", "roblox", "zynga", "gameloft", "king", "mojang",
    "netease", "tencent games", "garena", "scopely", "mobile gaming",
    "unity", "unreal", "unity technologies",
    # indies / studios
    "supergiant", "frogwares", "supermassive", "remedy", "fromsoftware",
    "from software", "rare", "turn 10", "playground games", "obsidian",
    "naughty", "treyarch", "infinity ward", "sledgehammer",
    "naughty dog", "housemarque", "hazelight", "annapurna", "thatgamecompany",
    # game-specific hardware / engines seen in listings
    "applovin", "supercell",
}

# Keywords in the title/skills that indicate a game-dev role.
# These are matched with word boundaries so "mmo" doesn't match "commodities".
GAME_KEYWORDS = [
    r"gameplay", r"game\s*dev", r"game\s*programmer", r"gamedev",
    r"game\s*engineer", r"game\s*server", r"game\s*ai", r"game\s*design",
    r"game\s*development", r"\bunreal\b", r"\bunity\b", r"\bconsole\b",
    r"mmo gaming", r"mmorpg", r"\bgames\b", r"video game",
    r"game studio", r"mobile game", r"game engine",
]

# Sometimes source==GameJobs means everything there is game industry.
GAMEDEV_SOURCES = {"GameJobs"}


def company_only(company: str) -> bool:
    return (company or "").strip().lower() in GAME_COMPANIES


def is_game_dev(item) -> bool:
    """Return True if the internship should go on the 'Game Dev' tab."""
    if not item:
        return False
    source = (getattr(item, "source", "") or "").lower()
    if source in {s.lower() for s in GAMEDEV_SOURCES}:
        return True

    company = (getattr(item, "company", "") or "").lower()
    if company and company in GAME_COMPANIES:
        return True

    title = (getattr(item, "title", "") or "").lower()
    for kw in GAME_KEYWORDS:
        if re.search(kw, title):
            # "Summer Games"/"Winter Games" usually refer to a sporting event
            # (e.g. Olympic-style support work), not game development.
            if re.search(r"summer games|winter games|para games|olympic", title):
                return False
            return True
    return False
