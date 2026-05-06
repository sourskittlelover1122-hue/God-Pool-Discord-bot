import discord
import os
import random
import json
from pathlib import Path
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =========================
# 💾 USER HERO STORAGE
# =========================

HEROES_FILE = Path("user_heroes.json")

def load_user_heroes():
    """Load all user heroes from file"""
    if HEROES_FILE.exists():
        with open(HEROES_FILE, "r") as f:
            return json.load(f)
    return {}

def save_user_heroes(heroes_data):
    """Save all user heroes to file"""
    with open(HEROES_FILE, "w") as f:
        json.dump(heroes_data, f, indent=2)

def add_hero_to_user(user_id, hero_data):
    """Add a hero to a user's collection"""
    heroes = load_user_heroes()
    user_id_str = str(user_id)
    
    if user_id_str not in heroes:
        heroes[user_id_str] = []
    
    heroes[user_id_str].append(hero_data)
    save_user_heroes(heroes)

def get_user_heroes(user_id):
    """Get all heroes for a specific user"""
    heroes = load_user_heroes()
    return heroes.get(str(user_id), [])

# =========================
# 🔥 PASTE NAME LISTS HERE
# =========================

FIRST_NAMES = [
   "Aldren", "Vaelor", "Myrin", "Kael", "Thorne", "Eryndor", "Sylas", "Darian", "Vael", "Orin",
"Luthar", "Zephyr", "Kaelith", "Riven", "Talon", "Draven", "Eldric", "Sorren", "Nyx", "Calder",
"Varian", "Lucian", "Aric", "Brennor", "Theron", "Kairo", "Mordain", "Auron", "Elowen", "Iskander",
"Fenric", "Veylor", "Astra", "Solren", "Kaedric", "Myrren", "Zarek", "Dorian", "Vaelis", "Orion",
"Sable", "Korvin", "Alaric", "Rhevan", "Cyrus", "Eldrin", "Tiber", "Nymer", "Valen", "Skorn",
"Aether", "Laziel", "Bran", "Korran", "Virel", "Elyon", "Dax", "Malrik", "Vorn", "Selric",
"Aldor", "Nyxen", "Caelum", "Torin", "Rask", "Velkan", "Eiric", "Joren", "Mavros", "Zephar",
"Lyric", "Orvyn", "Kaelis", "Druven", "Sorin", "Ardyn", "Velor", "Kalen", "Rhydor", "Eron",
"Valken", "Solan", "Myrrik", "Thalor", "Kieran", "Zorren", "Alven", "Drakar", "Elyric", "Vaeron",
"Morlen", "Skye", "Calen", "Varek", "Oryn", "Eldan", "Rivenor", "Taren", "Nyro", "Kaldor",
"Aeris", "Veyran", "Lorian", "Braken", "Zyric", "Arkan", "Velryn", "Kaelor", "Drystan", "Elandor",
"Sorvik", "Tyren", "Vaelric", "Oberon", "Korrin", "Sylvar", "Auronis", "Ravik", "Elric", "Daren",
"Myrkos", "Zayden", "Kaelorin", "Thyric", "Valdrin", "Eryx", "Nerion", "Virek", "Solvik", "Khalor",
"Aldric", "Rhylen", "Vaelorin", "Torvak", "Zephiros", "Malven", "Ordan", "Kaeloris", "Druin", "Varn",
"Eldros", "Sorenik", "Cyrion", "Nyros", "Alther", "Veyros", "Kaedon", "Rivenael", "Tharic", "Elyndor",
"Zarekhan", "Vaelion", "Morvyn", "Skarn", "Caldrik", "Aeron", "Valkor", "Orric", "Eldarion", "Raskor",
"Tyran", "Nyxel", "Kalenor", "Arion", "Velmorn", "Dravenor", "Solvyr", "Kaeth", "Myrrion", "Thalen",
"Zorik", "Aldrenor", "Vireth", "Eronis", "Branik", "Lazir", "Kaelron", "Rivenis", "Torren", "Elyx",
"Vaelith", "Morvok", "Skelran", "Calix", "Varyn", "Orynth", "Eldrikor", "Rhyzor", "Tarenis", "Nyther",
"Kaelorix", "Arvel", "Velkanis", "Drayven", "Solrenik", "Thornak", "Zyreth", "Aldros", "Veyl", "Eldwyn",
"Ravon", "Kaelithor", "Myrran", "Thyros", "Valek", "Orvax", "Kaedryn", "Drakos", "Elyros", "Vaelorax",
"Morion", "Skarnyx", "Calderon", "Virethos", "Orynax", "Eldran", "Rivenox", "Tyrikos", "Nyxar", "Kaeloran",
"Ardynis", "Velkor", "Draxen", "Solvar", "Thalrik", "Zorvan", "Aldorix", "Veylan", "Eldrosan", "Rasken",
"Kaelvyn", "Myrrik", "Thorenix", "Valdros", "Orinax", "Kaedrix", "Dravon", "Elyndris", "Vaelkor", "Morvex",
"Skornis", "Caldran", "Vyrion", "Oryxen", "Eldrax", "Rivenar", "Tarenox", "Nyvar", "Kaelthas", "Arkon",
"Veldran", "Drazir", "Solkan", "Thyren", "Zorvyn", "Aldrex", "Veykor", "Eldrav", "Raskorix", "Kaelvorn",
"Myrrakor", "Thyvar", "Valdrak", "Orinox", "Kaedral", "Draykor", "Elyzor", "Vaelthar", "Morzan", "Skelvar",
"Caldrion", "Vyrak", "Oryzor", "Eldrikar", "Rivenzor", "Tarenix", "Nytheron", "Kaelthir", "Arvex", "Velzor",
"Draznor", "Solvex", "Thykar", "Zorvex", "Aldorin", "Veyrax", "Eldthar", "Ravikor", "Kaelorath", "Myrrenix",
"Thalzor", "Valex", "Orveth", "Kaedrion", "Drakorin", "Elythar", "Vaelmir", "Morvath", "Skarnex", "Calzor",
"Virethar", "Oryndal", "Eldvex", "Rivenkar", "Tyranox", "Nyxarion", "Kaelvar", "Arzeth", "Velkran", "Draxenor",
"Solzeth", "Thornar", "Zorvath", "Aldrax", "Veythar", "Eldkor", "Raskvyn", "Kaelzeth", "Myrrvex", "Thyron",
"Valzor", "Orvex"
]

LAST_NAMES = [
    "Stormborn", "Nightwhisper", "Ironvale", "Duskbreaker", "Ashenford", "Grimshaw", "Voidwalker", "Sunfall",
"Mooncrest", "Bloodthorne", "Starforge", "Emberlight", "Frosthelm", "Dreadmoor", "Windrider", "Stoneveil",
"Darkwater", "Flameward", "Skylance", "Ironfrost", "Shadowmere", "Goldbranch", "Ravencrest", "Thornfield",
"Brightsoul", "Dustborn", "Skullrend", "Stormveil", "Blackthorn", "Silverveil", "Oathbinder", "Firebrand",
"Nightfall", "Mistwalker", "Bloodraven", "Stonebreaker", "Skyforge", "Emberstone", "Frostwind", "Daggerfall",
"Voidborn", "Ashwalker", "Lightbringer", "Graveborn", "Soulrender", "Ironshade", "Moonfall", "Starveil",
"Darkbane", "Stormclaw", "Flameheart", "Wraithwood", "Duskforge", "Sunblade", "Nightforge", "Bloodveil",
"Stoneheart", "Windshade", "Shadowthorn", "Frostfang", "Emberbane", "Skyrend", "Ironthorn", "Voidflare",
"Grimveil", "Ashenblade", "Moonshade", "Starborn", "Dreadfang", "Fireveil", "Blackwater", "Silverthorn",
"Stormborned", "Nightbloom", "Ironwraith", "Dustveil", "Bloodshade", "Skyshadow", "Emberforge", "Frostveil",
"Shadowblade", "Stoneveil", "Voidcrest", "Flameveil", "Sunshadow", "Graveveil", "Windthorn", "Ashenveil",
"Moonblade", "Darkflare", "Stormrend", "Ironblade", "Nightthorn", "Bloodforge", "Skyveil", "Emberthorn",
"Frostborne", "Shadowfall", "Stoneforge", "Voidthorn", "Flamefall", "Sunforge", "Grimthorn", "Ashenfall",
"Moonforge", "Darkthorn", "Stormshadow", "Ironfall", "Nightveil", "Bloodthorned", "Skyborne", "Emberfall",
"Frostshadow", "Shadowforge", "Stonefall", "Voidfall", "Flameborn", "Sunveil", "Graveforge", "Windfall",
"Ashenborn", "Moonthorn", "Darkveil", "Stormblade", "Ironveil", "Nightshade", "Bloodfall", "Skyforge",
"Emberveil", "Frostfall", "Shadowborn", "Stoneblade", "Voidshade", "Flameblade", "Sunborn", "Grimfall",
"Ashenforge", "Moonfallen", "Darkborn", "Stormveilborn", "Ironshadow", "Nightforgeborn", "Bloodveilborn",
"Skyfall", "Embershade", "Frostforge", "Shadowveil", "Stoneborn", "Voidborned", "Flameveilborn",
"Sunfallen", "Graveborn", "Windveil", "Ashenshadow", "Moonveil", "Darkforge", "Stormborned", "Ironcrest",
"Nightfallen", "Bloodcrest", "Skyshade", "Embercrest", "Frostcrest", "Shadowcrest", "Stonecrest",
"Voidcrested", "Flamecrest", "Suncrest", "Grimcrest", "Ashencrest", "Mooncrested", "Darkcrest", "Stormcrest"
]


# =========================
# 🧠 PASTE FEATS BY RARITY HERE
# =========================

FEATS_BY_RARITY = {
    "Common": [
        "Defeated 5 enemies without dying",
        "Collected 100 resources",
        "Crafted a basic weapon",
        "Survived a dungeon encounter",
        "Completed first quest",
        "Tamed a basic creature",
        "Reached level 5",
        "Discovered a new location",
        "Helped an NPC",
        "Won a training duel",
        "Harvested rare-for-you material",
        "Escaped combat with low HP",
        "Blocked 10 attacks",
        "Landed 20 hits in a row",
        "Used first ability successfully",
        "Revived an ally once",
        "Cooked a meal",
        "Built a structure",
        "Traveled 1,000 blocks",
        "Looted a chest",
        "Survived a night cycle",
        "Learned a skill",
        "Equipped full gear set",
        "Sold an item",
        "First boss assist"
    ],
    "Trained": [
        "Defeated mini-boss",
        "Cleared a dungeon room flawlessly",
        "Blocked a lethal attack",
        "Mastered a basic weapon type",
        "Survived poison or burn effect",
        "Executed combo chain (10+)",
        "Tamed an aggressive creature",
        "Completed timed challenge",
        "Won PvP match",
        "Crafted rare-tier item",
        "Survived ambush",
        "Perfect dodge streak (5+)",
        "Killed elite enemy",
        "Used ability without cooldown loss",
        "Rescued NPC from danger",
        "Built fortified base section",
        "Gathered 1,000 resources",
        "Defeated 10 enemies without damage",
        "Completed quest chain",
        "Survived boss phase",
        "Landed critical hit streak",
        "Explored dangerous zone",
        "Baited enemy into trap",
        "Survived environmental hazard",
        "Upgraded gear twice"
    ],
    "Uncommon": [
        "Defeated dungeon boss",
        "Soloed elite enemy",
        "Survived lethal fall",
        "Perfect boss phase",
        "Crafted rare weapon",
        "Tamed rare creature",
        "Completed no-damage fight",
        "Cleared dungeon alone",
        "Survived 3v1 encounter",
        "Executed 50-hit combo",
        "Deflected projectile attack",
        "Survived elemental storm",
        "Found hidden area",
        "Completed high-risk quest",
        "Blocked ultimate ability",
        "Killed 100 enemies total",
        "Survived cursed zone",
        "Mastered combat stance",
        "Built advanced structure",
        "Won arena match",
        "Gathered rare resource",
        "Survived boss enraged phase",
        "Revived multiple allies",
        "Completed stealth mission",
        "Triggered secret event"
    ],
    "Handy": [
        "Defeated world mini-boss",
        "Solo cleared dungeon",
        "Crafted epic-tier item",
        "Survived lethal status effects",
        "Tamed rare elite beast",
        "Won ranked PvP match",
        "Completed flawless dungeon run",
        "Killed 500 enemies",
        "Survived ambush squad",
        "Mastered 2 weapon types",
        "Parried boss ultimate",
        "Completed raid phase",
        "Built stronghold",
        "Found legendary clue",
        "Survived world event",
        "Completed elite questline",
        "Hit 100 combo chain",
        "Survived under 1 HP",
        "Destroyed enemy base",
        "Escaped death trap",
        "Crafted enchanted gear",
        "Completed dungeon under time limit",
        "Revived entire team",
        "Defeated corrupted elite",
        "Triggered rare encounter"
    ],
    "Rare": [
        "Defeated raid boss",
        "Soloed dungeon boss",
        "Cleared nightmare dungeon",
        "Survived execution-level attack",
        "Killed 1,000 enemies",
        "Mastered combat system",
        "Crafted legendary component",
        "Tamed mythical creature",
        "Survived apocalypse event",
        "Won tournament",
        "Blocked ultimate attack",
        "Cleared dungeon blindfolded/disabled",
        "Survived dimensional rift",
        "Defeated corrupted hero",
        "Completed world quest",
        "Built massive fortress",
        "Survived 10 elite enemies",
        "Executed perfect raid run",
        "Found ancient relic",
        "Revived after death state",
        "Killed boss in under 1 minute",
        "Survived cursed transformation",
        "Controlled battlefield",
        "Completed no-hit boss",
        "Triggered legendary spawn"
    ],
    "Pseudo": [
        "Defeated pseudo-boss entity",
        "Survived reality distortion",
        "Killed unkillable enemy",
        "Bypassed system limitation",
        "Glitched through barrier",
        "Survived timeline collapse",
        "Held corrupted form",
        "Defeated multiple raid bosses solo",
        "Survived void exposure",
        "Killed entity beyond level cap",
        "Controlled enemy AI behavior",
        "Survived infinite dungeon wave",
        "Destroyed sealed artifact",
        "Survived memory erasure effect",
        "Broke game mechanic rule",
        "Defeated boss in invincible phase",
        "Survived null damage zone",
        "Absorbed forbidden power",
        "Cleared corrupted world layer",
        "Survived paradox event",
        "Rewrote skill effect",
        "Killed shadow duplicate self",
        "Survived system shutdown",
        "Triggered hidden developer event",
        "Entered forbidden zone"
    ],
    "Genisis": [
        "Defeated world-origin entity",
        "Created lifeform from essence",
        "Survived creation collapse",
        "Destroyed realm core",
        "Rebuilt destroyed zone",
        "Manipulated elemental laws",
        "Killed primordial beast",
        "Survived god fragment attack",
        "Reshaped terrain permanently",
        "Birthed elemental storm",
        "Absorbed world energy source",
        "Survived divine judgment",
        "Split continent-scale enemy",
        "Controlled reality shard",
        "Defeated world guardian",
        "Rewrote local physics",
        "Survived world reset",
        "Created pocket dimension",
        "Destroyed ancient seal",
        "Held corrupted genesis power",
        "Defeated time-anchored entity",
        "Survived planetary destruction event",
        "Became source of element",
        "Killed first creature archetype",
        "Triggered world evolution"
    ],
    "Legendary": [
        "Slayed legendary dragon",
        "Defeated ancient titan",
        "Survived god's strike",
        "Won world championship war",
        "Cleared mythic dungeon",
        "Killed immortal being",
        "Wielded legendary weapon",
        "Survived apocalypse alone",
        "Defeated army solo",
        "Mastered all weapon types",
        "Survived death curse",
        "Revived entire kingdom",
        "Controlled battlefield storm",
        "Found lost civilization",
        "Killed divine avatar",
        "Survived realm collapse",
        "Destroyed cursed artifact",
        "Won inter-realm duel",
        "Became faction leader",
        "Survived infinite trial",
        "Defeated corrupted godling",
        "Survived time loop",
        "Killed world serpent",
        "Achieved perfect combat record",
        "Triggered legendary ascension"
    ],
    "Mythical": [
        "Defeated mythic dragon king",
        "Survived divine apocalypse",
        "Killed spirit of world",
        "Controlled mythical beast army",
        "Entered spirit realm",
        "Defeated immortal myth",
        "Survived fate alteration",
        "Rewrote destiny thread",
        "Destroyed mythic relic",
        "Summoned celestial storm",
        "Killed dream entity",
        "Survived memory void",
        "Became legend across realms",
        "Defeated cosmic beast",
        "Held multiple divine blessings",
        "Survived soul separation",
        "Created mythic artifact",
        "Defeated god-tier hero",
        "Survived reality rewrite",
        "Killed eternal guardian",
        "Controlled mythic energy",
        "Survived infinite reincarnation loop",
        "Defeated void dragon",
        "Bypassed death itself",
        "Achieved mythic transcendence"
    ],
    "Ethereal": [
        "Became non-corporeal",
        "Survived astral plane",
        "Killed spirit entity",
        "Manipulated soul energy",
        "Phase through reality",
        "Absorbed divine essence",
        "Survived soul deletion attempt",
        "Entered dream realm",
        "Defeated ethereal guardian",
        "Communicated with dead worlds",
        "Became energy form",
        "Survived void drift",
        "Manipulated emotions of reality",
        "Destroyed spirit core",
        "Bound soul to weapon",
        "Survived astral collapse",
        "Controlled ghost legion",
        "Rewrote soul imprint",
        "Defeated incorporeal god",
        "Survived memory erasure",
        "Entered higher dimension",
        "Manipulated probability flow",
        "Absorbed spirit king",
        "Became eternal observer",
        "Survived existence reset"
    ],
    "Ascendant": [
        "Defeated divine avatar",
        "Surpassed mortal limits",
        "Achieved god-tier power spike",
        "Survived divine tribunal",
        "Ascended to higher realm",
        "Controlled multiple elements",
        "Defeated celestial army",
        "Survived fate rewrite",
        "Killed ascended being",
        "Created divine weapon",
        "Survived universe collapse",
        "Manipulated time flow",
        "Defeated star-born entity",
        "Became realm protector",
        "Survived omniscient attack",
        "Controlled fate threads",
        "Destroyed divine seal",
        "Rewrote personal destiny",
        "Survived cosmic judgment",
        "Defeated angelic host",
        "Absorbed celestial core",
        "Became walking catastrophe",
        "Survived god hierarchy war",
        "Killed ascended titan",
        "Reached near-omnipotence"
    ],
    "Primordial": [
        "Defeated origin force",
        "Survived pre-reality state",
        "Killed first-born entity",
        "Controlled elemental origins",
        "Witnessed universe birth",
        "Survived nothingness zone",
        "Absorbed chaos seed",
        "Defeated creation titan",
        "Manipulated existence laws",
        "Rewrote beginning of time",
        "Survived cosmic void",
        "Destroyed primordial seal",
        "Became origin of element",
        "Controlled entropy flow",
        "Defeated void creator",
        "Survived universal reset",
        "Split existence fabric",
        "Created primordial storm",
        "Consumed ancient force",
        "Defeated time origin entity",
        "Survived absolute nothing",
        "Manipulated genesis code",
        "Became living origin point",
        "Killed world-forger",
        "Exists before existence"
    ],
    "Omni": [
        "Defeated multiverse entity",
        "Survived infinite realities",
        "Killed omniversal god fragment",
        "Controlled probability itself",
        "Existed in all timelines",
        "Survived narrative deletion",
        "Rewrote multiverse rule",
        "Destroyed infinite worlds",
        "Absorbed reality layers",
        "Became all elements",
        "Survived concept erasure",
        "Defeated absolute being",
        "Controlled story flow",
        "Rebuilt multiverse",
        "Survived paradox collapse",
        "Exists outside logic",
        "Killed meta-creator entity",
        "Controlled all outcomes",
        "Survived author interference",
        "Became infinite self",
        "Defeated totality force",
        "Exists beyond existence",
        "Rewrote omniversal law",
        "Survived absolute nothingness",
        "Became everything"
    ],
    "God-Challenger": [
        "Challenged a god directly",
        "Survived divine wrath",
        "Injured a god entity",
        "Stole divine power",
        "Defeated god avatar",
        "Withstood divine punishment",
        "Broke divine seal",
        "Survived heaven strike",
        "Destroyed divine relic",
        "Entered god realm",
        "Stole fate from deity",
        "Survived god execution",
        "Killed minor god",
        "Resisted divine possession",
        "Challenged creation god",
        "Survived celestial judgment",
        "Shattered divine armor",
        "Defied prophecy",
        "Survived god war",
        "Broke immortal law",
        "Stole celestial throne fragment",
        "Defeated god's champion",
        "Survived divine erasure attempt",
        "Injured primordial deity",
        "Stood equal to gods"
    ]
}


# =========================
# 🌟 SYSTEM DATA
# =========================

ALIGNMENT_MODS = {
    "Valiant": (0.1, 0.6),
    "Good": (0.05, 0.5),
    "Neutral": (-0.1, 0.4),
    "Mischievous": (-0.3, 0.7),
    "Evil": (-0.4, 0.8),
}

DIVINITY_MODS = {
    "Divine": (-0.1, 0.8),
    "Neutral": (-0.2, 0.5),
}

ELEMENT_MODS = (-0.25, 0.25)
CLASS_MODS = (-0.25, 0.25)


RARITY_TIERS = [
    (0.0, "Common"),
    (0.5, "Trained"),
    (1.0, "Uncommon"),
    (1.5, "Handy"),
    (2.0, "Rare"),
    (2.6, "Pseudo"),
    (3.2, "Genisis"),
    (4.0, "Legendary"),
    (5.0, "Mythical"),
    (6.0, "Ethereal"),
    (7.0, "Ascendant"),
    (8.5, "Primordial"),
    (10.0, "Omni"),
    (12.0, "God-Challenger"),
]


# =========================
# ⚔️ CLASS TITLES
# =========================

CLASS_TIERS = [
    (-999, "Horrible"),
    (-0.2, "Okay"),
    (0.0, "Apprentice"),
    (0.3, "Journeyer"),
    (0.7, "Masterclass"),
    (1.2, "Chief"),
    (1.8, "Masterclass"),
    (2.5, "Transcendent"),
]


# =========================
# 🌊 ELEMENT DATA (YOUR TABLE)
# =========================

ELEMENTS = {
    "Fire": ("Flameborn", "Ash-Cursed"),
    "Water": ("Tidecaller", "Drowned Soul"),
    "Earth": ("Stonewarden", "Dustbroken"),
    "Air": ("Stormwing", "Hollow Breath"),
    "Steel": ("Iron Vanguard", "Rustbound"),
    "Glass": ("Prismseer", "Shattermarked"),
    "Light": ("Dawnblessed", "Faded One"),
    "Dark": ("Night Sovereign", "Void-Touched"),
    "Equinox": ("Balancekeeper", "Riftfallen"),
    "Celestial": ("Starforged", "Eclipsebound"),
    "Beast": ("Wildheart", "Rabid Fang"),
    "Lightning": ("Thunderlord", "Static Scarred"),
    "Magma": ("Inferno Core", "Cracked Ember"),
    "Spore": ("Bloomcaller", "Rotspawn"),
    "Crystal": ("Gemkeeper", "Fractured Soul"),
    "Color": ("Spectrum Weaver", "Colorless"),
    "Plants": ("Verdant Guardian", "Witherbloom"),
    "Poison": ("Venom Saint", "Toxin-Ridden"),
    "Corruption": ("Abyss Herald", "Broken Vessel"),
    "Mist": ("Fogwalker", "Lost Wanderer"),
    "Death": ("Grave Monarch", "Soulblighted"),
    "Life": ("Lifebringer", "Wilted Spirit"),
    "Rain": ("Stormbearer", "Endless Drizzle"),
    "Lava": ("Volcano King", "Burnscarred"),
}


# =========================
# 🧮 HELPERS
# =========================

def roll(mod_range):
    return random.uniform(mod_range[0], mod_range[1])


def get_rarity(score):
    rarity = "Common"
    for threshold, name in RARITY_TIERS:
        if score >= threshold:
            rarity = name
    return rarity


def get_class_title(score):
    title = "Okay"
    for threshold, name in CLASS_TIERS:
        if score >= threshold:
            title = name
    return title


def random_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def roll_feat(rarity):
    feats = FEATS_BY_RARITY.get(rarity, [])
    if feats:
        return random.choice(feats)
    return "No recorded feat."


# =========================
# 📌 BOT COMMANDS
# =========================

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.command(name="CH")
async def create_hero(ctx):
    msg = """
**Hero Creation Format**
Send your hero like this:

`CH_Alignment_Divinity_Race_Element_Class`

---

**Options:**

Alignment:
Valiant / Good / Neutral / Mischievous / Evil

Divinity:
Divine / Neutral

Race:
Human / Construct / Elven / Goblin / Beast / Ogre / Deep-Crawler / Celestial / Angel / Demon / Dwarf / Elemental / Undead / Magma-Crawler

Elements:
Fire, Water, Earth, Air, Steel, Glass, Light, Dark, Equinox, Celestial, Beast, Lightning, Magma, Spore, Crystal, Color, Plants, Poison, Corruption, Mist, Death, Life, Rain, Lava

Classes:
Warrior, Archer, Assassin, Mage, Paladin, Rogue, Admiral, Sniper, Outlaw, Bard, Scavenger, Ritualist, Commander

To view your hero collection, use the command `!HerosGodPool`
"""
    await ctx.send(msg)

@bot.command(name="HerosGodPool")
async def heros_god_pool(ctx):
    """Display all heroes in a user's collection"""
    user_heroes = get_user_heroes(ctx.author.id)
    
    if not user_heroes:
        await ctx.send(f"**⚔️ HERO COLLECTION — {ctx.author.name} ⚔️**\n\nYou currently have **0 heroes** in your collection. Create one with `CH_Alignment_Divinity_Race_Element_Class`!")
        return
    
    # Build the message
    message = f"**⚔️ HERO COLLECTION — {ctx.author.name} ⚔️**\n\nYou currently have **{len(user_heroes)}** heroes in your collection:\n\n---\n\n"
    
    for hero in user_heroes:
        message += f"🏷️ Hero Name: {hero['full_name']}\n"
        message += f"⭐ Rarity: {hero['rarity']}\n"
        message += f"⚔️ Class: {hero['class']}\n"
        message += f"🌟 Divinity: {hero['divinity']}\n"
        message += f"⚖️ Alignment: {hero['alignment']}\n"
        message += f"🧬 Race: {hero['race']}\n"
        message += f"🌊 Element: {hero['element']}\n"
        message += f"🔥 Feat: {hero['feat']}\n\n"
    
    # Discord has a 2000 character limit per message, so split if needed
    if len(message) > 2000:
        # Split into multiple messages
        chunks = []
        current = f"**⚔️ HERO COLLECTION — {ctx.author.name} ⚔️**\n\nYou currently have **{len(user_heroes)}** heroes in your collection:\n\n---\n\n"
        
        for hero in user_heroes:
            hero_text = f"🏷️ Hero Name: {hero['full_name']}\n⭐ Rarity: {hero['rarity']}\n⚔️ Class: {hero['class']}\n🌟 Divinity: {hero['divinity']}\n⚖️ Alignment: {hero['alignment']}\n🧬 Race: {hero['race']}\n🌊 Element: {hero['element']}\n🔥 Feat: {hero['feat']}\n\n"
            
            if len(current) + len(hero_text) > 2000:
                chunks.append(current)
                current = hero_text
            else:
                current += hero_text
        
        if current:
            chunks.append(current)
        
        for chunk in chunks:
            await ctx.send(chunk)
    else:
        await ctx.send(message)


@bot.event
async def on_message(message):
    await bot.process_commands(message)

    if message.author.bot:
        return

    if message.content.startswith("CH_"):
        try:
            parts = message.content.split("_")

            alignment = parts[1]
            divinity = parts[2]
            race = parts[3]
            element = parts[4]
            clazz = parts[5]

            # Rolls
            align_roll = roll(ALIGNMENT_MODS[alignment])
            div_roll = roll(DIVINITY_MODS[divinity])
            elem_roll = roll(ELEMENT_MODS)
            class_roll = roll(CLASS_MODS)

            total_score = align_roll + div_roll + elem_roll + class_roll

            rarity = get_rarity(total_score)

            class_title = get_class_title(class_roll)

            element_good, element_bad = ELEMENTS[element]

            if elem_roll > 0.1:
                element_title = element_good
            elif elem_roll < -0.1:
                element_title = element_bad
            else:
                element_title = element

            name = random_name()
            feat = roll_feat(rarity)

            final_name = f"{class_title} {clazz} {name} the {element_title} - ({rarity})"

            # Store hero data
            hero_data = {
                "full_name": final_name,
                "class": clazz,
                "rarity": rarity,
                "divinity": divinity,
                "alignment": alignment,
                "race": race,
                "element": element_title,
                "feat": feat
            }
            
            add_hero_to_user(message.author.id, hero_data)

            embed = discord.Embed(title="⚔️ Hero Created ⚔️", color=0x00ffcc)
            embed.add_field(name="Hero", value=final_name, inline=False)
            embed.add_field(name="Feat", value=feat, inline=False)
            embed.add_field(name="Divinity", value=f"{divinity} ({div_roll:.2f})", inline=True)
            embed.add_field(name="Alignment", value=f"{alignment} ({align_roll:.2f})", inline=True)
            embed.add_field(name="Race", value=race, inline=True)
            embed.add_field(name="Class Roll", value=f"{class_roll:.2f}", inline=True)
            embed.add_field(name="Element Roll", value=f"{elem_roll:.2f}", inline=True)
            embed.set_footer(text="✅ Hero added to your collection!")

            await message.channel.send(embed=embed)

        except Exception as e:
            await message.channel.send(f"Error creating hero: {e}")


bot.run(TOKEN)