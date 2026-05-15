import discord
import os
import random
import json
import datetime
from pathlib import Path
from dotenv import load_dotenv
from discord.ext import commands, tasks
import requests

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GIST_ID = os.getenv("GIST_ID")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

GIST_URL = f"https://api.github.com/gists/{GIST_ID}"
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}

# Fallback to local files if Gist not configured
USE_GIST = GIST_ID and GITHUB_TOKEN

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

EVENT_STATE_FILE = Path("event_state.json")
EVENT_MESSAGE_INTERVAL_SECONDS = 12 * 60 * 60
EVENT_DURATION_SECONDS = 7 * 60 * 60
ACTIVE_EVENT_STATE = None

EVENTS = [
    {
        "name": "Blood Moon Rising",
        "boost": "Death, Corruption, and Evil alignment heroes gain greatly increased rarity chances.",
        "details": "Rarity surges for the darkest champions under the crimson moon.",
    },
    {
        "name": "Celestial Convergence",
        "boost": "Divine and Celestial element rolls receive massive positive modifier boosts.",
        "details": "Stars align and sacred power bathes those touched by the heavens.",
    },
    {
        "name": "Infernal Surge",
        "boost": "Hellish-style outcomes, Lava, Magma, and Fire elements roll higher but more volatile.",
        "details": "The forge of the abyss spits unpredictable infernal power.",
    },
    {
        "name": "The Hollow Fog",
        "boost": "Mist and Dark elements gain increased shiny chances.",
        "details": "A chilling haze whispers with glimmering secrets in the gloom.",
    },
    {
        "name": "Verdant Bloom",
        "boost": "Plants and Life heroes gain boosted rarity and reduced negative rolls.",
        "details": "Nature's vitality blooms, guarding against rotten fate.",
    },
    {
        "name": "Thunder Dominion",
        "boost": "Lightning and Air elements gain increased chances for high-tier titles.",
        "details": "Stormlords rise, and wind-carved titles thunder through the skies.",
    },
    {
        "name": "The Drowned Tide",
        "boost": "Water and Rain heroes gain boosted rarity and shiny odds.",
        "details": "The ocean's blessing flows to those born of the tides.",
    },
    {
        "name": "Gravecall Night",
        "boost": "Undead and Death heroes are far more likely to roll Mythical+ rarities.",
        "details": "The dead answer the call, and forbidden power awakens in the night.",
    },
    {
        "name": "Prismatic Awakening",
        "boost": "Glass, Crystal, and Color elements gain doubled chances for special titles.",
        "details": "A spectrum of brilliance shatters the ordinary and crowns new champions.",
    },
    {
        "name": "The Beast Hunt",
        "boost": "Beast race and Beast element heroes gain stronger class modifiers.",
        "details": "Predators prowl with sharpened instincts and primal rank.",
        "race": ["Beast"],
    },
    {
        "name": "Eclipse of Judgment",
        "boost": "Alignment rolls become far more extreme, both positively and negatively.",
        "details": "Balance shatters and fate swings wildly under the black sun.",
    },
    {
        "name": "Forgeheart Festival",
        "boost": "Steel and Earth heroes gain powerful stable rarity increases.",
        "details": "The heart of the forge beats strong, grounding champions in strength.",
    },
    {
        "name": "The Rotting Bloom",
        "boost": "Spore and Poison heroes gain huge rarity spikes and increased shiny rates.",
        "details": "Rotting beauty festers, attracting rare and dangerous glory.",
    },
    {
        "name": "Starfall Cataclysm",
        "boost": "Celestial and Equinox elements gain increased Omni and God-Challenger chances.",
        "details": "Falling stars tear open the heavens for the chosen and the damned.",
    },
    {
        "name": "The Ashen Era",
        "boost": "Fire, Lava, and Magma heroes gain increased title quality rolls.",
        "details": "The ash-filled skies crown the fiercest flame-born warriors.",
    },
    {
        "name": "Sanctuary of Dawn",
        "boost": "Light element and Good/Valiant alignments gain heavily reduced negative modifiers.",
        "details": "Dawn's sanctuary shields the righteous from the darkest setbacks.",
    },
    {
        "name": "The Rift Collapse",
        "boost": "Random element modifiers are doubled, creating chaotic high-roll opportunities.",
        "details": "Reality warps and elemental fortunes twist wildly.",
    },
    {
        "name": "The Wandering Tempest",
        "boost": "Air, Rain, and Lightning heroes gain boosted rarity.",
        "details": "Stormwinds carry luck and reward to those who ride the tempest.",
    },
    {
        "name": "Kingdoms at War",
        "boost": "Commander, Paladin, Admiral, and Warrior classes gain greatly increased class rolls.",
        "details": "Battlefields ignite and commanding champions gain fearsome valor.",
        "classes": ["Commander", "Paladin", "Admiral", "Warrior"],
    },
    {
        "name": "The Abyss Stares Back",
        "boost": "Corruption, Dark, and Mischievous/Evil alignment heroes gain extremely high-risk, high-reward modifiers.",
        "details": "The abyss reaches out with torment and temptation for the bold.",
    },
]

# =========================
# 💾 USER HERO STORAGE
# =========================

HEROES_FILE = Path("user_heroes.json")
ROLL_COUNTER_FILE = Path("user_roll_counts.json")
EMPORIUM_STATE_FILE = Path("emporium_state.json")
USER_ITEMS_FILE = Path("user_items.json")
USER_BOOSTS_FILE = Path("user_boosts.json")
NEMESIS_STATE_FILE = Path("nemesis_state.json")
MAX_HEROES_PER_USER = 150
NEMESIS_REQUIRED_VICTORIES = 3
NEMESIS_HUNT_INTERVAL_HOURS = 3
NEMESIS_HUNT_CHANCE = 0.30
NEMESIS_ACTIVE_ENCOUNTER_CHANCE = 0.30
NEMESIS_POTENTIAL_ENCOUNTER_CHANCE = 0.10
NEMESIS_MINION_REQUIREMENTS = ["Legendary", "Mythical", "Ethereal", "Ascendant"]
NEMESIS_GUESS_OPTIONS = ["Strike", "Shield"]
FORCED_ENCOUNTER_TYPE = None
EVOLUTION_TITLES = {
    "Fire": {
        "Warrior": "Flame Vanguard", "Archer": "Ember Ranger", "Assassin": "Cinder Shade", "Mage": "Inferno Sage",
        "Paladin": "Sunfire Templar", "Rogue": "Ashstep Raider", "Admiral": "Blazewave Captain", "Sniper": "Scorchshot",
        "Outlaw": "Wildfire Bandit", "Bard": "Balladeer of Embers", "Scavenger": "Coalpicker", "Ritualist": "Pyre Caller",
        "Commander": "Infernal General", "Defender": "Molten Bulwark", "Barbarian": "Volcano Reaver"
    },
    "Water": {
        "Warrior": "Tidebreaker", "Archer": "Deepcurrent Archer", "Assassin": "Undertow Stalker", "Mage": "Abyssal Channeler",
        "Paladin": "Tidal Guardian", "Rogue": "Wave Skulker", "Admiral": "Leviathan Admiral", "Sniper": "Harbor Piercer",
        "Outlaw": "Blackwater Marauder", "Bard": "Siren Minstrel", "Scavenger": "Drift Seeker", "Ritualist": "Ocean Whisperer",
        "Commander": "Sea Marshal", "Defender": "Coral Bastion", "Barbarian": "Riptide Berserker"
    },
    "Earth": {
        "Warrior": "Stonecrusher", "Archer": "Rootshot Ranger", "Assassin": "Gravellurker", "Mage": "Terra Shaper",
        "Paladin": "Mountain Sentinel", "Rogue": "Dustwalker", "Admiral": "Canyon Fleetmaster", "Sniper": "Cliffshot",
        "Outlaw": "Badlands Raider", "Bard": "Echo Drummer", "Scavenger": "Quarry Rat", "Ritualist": "Earthbinder",
        "Commander": "Ironpeak Warden", "Defender": "Granite Wall", "Barbarian": "Boulderfury"
    },
    "Air": {
        "Warrior": "Gale Knight", "Archer": "Skyfeather Archer", "Assassin": "Wind Veil", "Mage": "Tempest Caller",
        "Paladin": "Storm Herald", "Rogue": "Breeze Phantom", "Admiral": "Cloudfleet Admiral", "Sniper": "Cyclone Eye",
        "Outlaw": "Dust Devil", "Bard": "Whisper Singer", "Scavenger": "Drift Chaser", "Ritualist": "Zephyr Monk",
        "Commander": "Storm Marshal", "Defender": "Skyshield", "Barbarian": "Hurricane Ravager"
    },
    "Steel": {
        "Warrior": "Iron Vanguard", "Archer": "Steelstring Ranger", "Assassin": "Blade Phantom", "Mage": "Alloy Arcanist",
        "Paladin": "Argent Crusader", "Rogue": "Razorcloak", "Admiral": "Ironfleet Captain", "Sniper": "Railshot",
        "Outlaw": "Rust Marauder", "Bard": "Forgemelody", "Scavenger": "Scrap Hunter", "Ritualist": "Metal Binder",
        "Commander": "Warsteel Marshal", "Defender": "Fortress Sentinel", "Barbarian": "Chainbreaker"
    },
    "Glass": {
        "Warrior": "Shard Knight", "Archer": "Prismshot", "Assassin": "Mirror Veil", "Mage": "Crystal Lensmage",
        "Paladin": "Gleam Protector", "Rogue": "Glass Phantom", "Admiral": "Reflective Corsair", "Sniper": "Diamond Eye",
        "Outlaw": "Shatterhand", "Bard": "Chime Singer", "Scavenger": "Fragment Seeker", "Ritualist": "Prism Weaver",
        "Commander": "Crystal Marshal", "Defender": "Mirror Bastion", "Barbarian": "Shardbreaker"
    },
    "Light": {
        "Warrior": "Radiant Knight", "Archer": "Sunpiercer", "Assassin": "Dawnshade", "Mage": "Lumen Sage",
        "Paladin": "Holy Crusader", "Rogue": "Gleamstep", "Admiral": "Solar Admiral", "Sniper": "Beacon Eye",
        "Outlaw": "Goldflare Rogue", "Bard": "Choir of Dawn", "Scavenger": "Halo Hunter", "Ritualist": "Lightbearer",
        "Commander": "Dawn Marshal", "Defender": "Aegis of Light", "Barbarian": "Sunfury"
    },
    "Dark": {
        "Warrior": "Dread Knight", "Archer": "Nightpiercer", "Assassin": "Void Fang", "Mage": "Umbra Weaver",
        "Paladin": "Eclipse Templar", "Rogue": "Shade Runner", "Admiral": "Blackwake Admiral", "Sniper": "Moonshot Stalker",
        "Outlaw": "Grave Bandit", "Bard": "Dirge Singer", "Scavenger": "Hollow Picker", "Ritualist": "Shadowbinder",
        "Commander": "Abyss Marshal", "Defender": "Nightwall", "Barbarian": "Doomreaver"
    },
    "Equinox": {
        "Warrior": "Balance Knight", "Archer": "Horizon Archer", "Assassin": "Twilight Veil", "Mage": "Equilibrium Sage",
        "Paladin": "Zenith Guardian", "Rogue": "Duskstep", "Admiral": "Meridian Captain", "Sniper": "Eclipse Eye",
        "Outlaw": "Halfmoon Raider", "Bard": "Twilight Harpist", "Scavenger": "Balance Seeker", "Ritualist": "Equinox Caller",
        "Commander": "Duality Marshal", "Defender": "Axis Bastion", "Barbarian": "Twilight Ravager"
    },
    "Celestial": {
        "Warrior": "Starforged Knight", "Archer": "Comet Ranger", "Assassin": "Nebula Phantom", "Mage": "Astral Oracle",
        "Paladin": "Cosmic Crusader", "Rogue": "Meteor Stepper", "Admiral": "Galaxy Admiral", "Sniper": "Starshot",
        "Outlaw": "Void Corsair", "Bard": "Constellation Singer", "Scavenger": "Stardust Hunter", "Ritualist": "Celestial Seer",
        "Commander": "Astral Marshal", "Defender": "Nebula Bastion", "Barbarian": "Supernova Reaver"
    },
    "Beast": {
        "Warrior": "Fang Warrior", "Archer": "Huntcaller", "Assassin": "Predator Shade", "Mage": "Wildspeaker",
        "Paladin": "Alpha Guardian", "Rogue": "Clawstepper", "Admiral": "Leviabeast Captain", "Sniper": "Talon Eye",
        "Outlaw": "Savage Raider", "Bard": "Howl Singer", "Scavenger": "Carrion Hunter", "Ritualist": "Beastbinder",
        "Commander": "Pack Leader", "Defender": "Ironhide Sentinel", "Barbarian": "Apex Berserker"
    },
    "Lightning": {
        "Warrior": "Thunderblade", "Archer": "Stormshot", "Assassin": "Flash Fang", "Mage": "Volt Caller",
        "Paladin": "Tempest Templar", "Rogue": "Static Runner", "Admiral": "Thunderfleet Admiral", "Sniper": "Railstorm Eye",
        "Outlaw": "Shock Raider", "Bard": "Pulse Drummer", "Scavenger": "Sparkpicker", "Ritualist": "Storm Conduit",
        "Commander": "Thunder Marshal", "Defender": "Volt Bastion", "Barbarian": "Skybreaker"
    },
    "Magma": {
        "Warrior": "Magma Crusher", "Archer": "Emberbolt Ranger", "Assassin": "Lava Shade", "Mage": "Volcano Caller",
        "Paladin": "Infernal Warden", "Rogue": "Ash Runner", "Admiral": "Molten Admiral", "Sniper": "Furnace Eye",
        "Outlaw": "Crater Marauder", "Bard": "Lava Chanter", "Scavenger": "Cinderscraper", "Ritualist": "Molten Binder",
        "Commander": "Eruption Marshal", "Defender": "Basalt Fortress", "Barbarian": "Lavafury"
    },
    "Spore": {
        "Warrior": "Rotblade", "Archer": "Fungus Ranger", "Assassin": "Mold Stalker", "Mage": "Bloomcaller",
        "Paladin": "Verdant Saint", "Rogue": "Sporeveil", "Admiral": "Rotwater Captain", "Sniper": "Toxin Eye",
        "Outlaw": "Plague Drifter", "Bard": "Bloom Singer", "Scavenger": "Decay Gatherer", "Ritualist": "Mushroom Shaman",
        "Commander": "Rot Marshal", "Defender": "Fungus Bastion", "Barbarian": "Blight Berserker"
    },
    "Crystal": {
        "Warrior": "Crystal Knight", "Archer": "Gemshot", "Assassin": "Prism Fang", "Mage": "Crystal Sage",
        "Paladin": "Diamond Guardian", "Rogue": "Facet Runner", "Admiral": "Sapphire Admiral", "Sniper": "Quartz Eye",
        "Outlaw": "Gem Raider", "Bard": "Resonance Singer", "Scavenger": "Geode Hunter", "Ritualist": "Crystal Seer",
        "Commander": "Prism Marshal", "Defender": "Diamond Bastion", "Barbarian": "Shattermaul"
    },
    "Color": {
        "Warrior": "Spectrum Knight", "Archer": "Rainbow Piercer", "Assassin": "Hue Phantom", "Mage": "Chromatic Weaver",
        "Paladin": "Prism Guardian", "Rogue": "Paintshadow", "Admiral": "Aurora Captain", "Sniper": "Vivid Eye",
        "Outlaw": "Graffiti Raider", "Bard": "Color Chorus", "Scavenger": "Pigment Seeker", "Ritualist": "Spectrum Caller",
        "Commander": "Rainbow Marshal", "Defender": "Chromatic Wall", "Barbarian": "Neon Fury"
    },
    "Plants": {
        "Warrior": "Thorn Knight", "Archer": "Vine Ranger", "Assassin": "Rootlurker", "Mage": "Verdant Druid",
        "Paladin": "Grove Sentinel", "Rogue": "Leafstepper", "Admiral": "Greenwater Captain", "Sniper": "Thornshot",
        "Outlaw": "Briar Bandit", "Bard": "Forest Minstrel", "Scavenger": "Seed Gatherer", "Ritualist": "Bloom Ritualist",
        "Commander": "Wildwood Marshal", "Defender": "Barkshield", "Barbarian": "Vine Berserker"
    },
    "Poison": {
        "Warrior": "Venom Knight", "Archer": "Toxic Ranger", "Assassin": "Fangshade", "Mage": "Plague Weaver",
        "Paladin": "Toxic Templar", "Rogue": "Venomstep", "Admiral": "Blackwater Venomlord", "Sniper": "Serpent Eye",
        "Outlaw": "Toxin Marauder", "Bard": "Venom Balladeer", "Scavenger": "Rotpicker", "Ritualist": "Poison Hexer",
        "Commander": "Blight Marshal", "Defender": "Toxic Bastion", "Barbarian": "Acid Reaver"
    },
    "Corruption": {
        "Warrior": "Corrupt Vanguard", "Archer": "Voidbow Hunter", "Assassin": "Abyss Stalker", "Mage": "Ruin Weaver",
        "Paladin": "Fallen Crusader", "Rogue": "Riftstepper", "Admiral": "Black Rift Admiral", "Sniper": "Corrupt Eye",
        "Outlaw": "Rotblood Raider", "Bard": "Dirge Whisperer", "Scavenger": "Void Picker", "Ritualist": "Corruption Caller",
        "Commander": "Ruin Marshal", "Defender": "Hollow Bastion", "Barbarian": "Doom Berserker"
    },
    "Mist": {
        "Warrior": "Fogblade", "Archer": "Mist Ranger", "Assassin": "Vapor Phantom", "Mage": "Haze Weaver",
        "Paladin": "Veil Guardian", "Rogue": "Fogstepper", "Admiral": "Mistwake Admiral", "Sniper": "Silent Eye",
        "Outlaw": "Gray Wanderer", "Bard": "Whisper Bard", "Scavenger": "Drift Picker", "Ritualist": "Mistcaller",
        "Commander": "Veil Marshal", "Defender": "Silent Bastion", "Barbarian": "Fog Reaver"
    },
    "Death": {
        "Warrior": "Grave Knight", "Archer": "Bonepiercer", "Assassin": "Soulreaper", "Mage": "Necro Sage",
        "Paladin": "Deathwarden", "Rogue": "Gravewalker", "Admiral": "Dreadfleet Admiral", "Sniper": "Skull Eye",
        "Outlaw": "Tomb Raider", "Bard": "Funeral Singer", "Scavenger": "Corpse Gatherer", "Ritualist": "Soul Binder",
        "Commander": "Death Marshal", "Defender": "Crypt Bastion", "Barbarian": "Bonecrusher"
    },
    "Life": {
        "Warrior": "Lifeblade", "Archer": "Bloom Ranger", "Assassin": "Spirit Walker", "Mage": "Vital Sage",
        "Paladin": "Guardian Saint", "Rogue": "Greenstepper", "Admiral": "Lifetide Captain", "Sniper": "Heartshot",
        "Outlaw": "Wild Healer", "Bard": "Harmony Singer", "Scavenger": "Herb Gatherer", "Ritualist": "Spirit Caller",
        "Commander": "Dawn Marshal", "Defender": "Living Bastion", "Barbarian": "Wildblood Berserker"
    },
    "Ice": {
        "Warrior": "Frost Knight", "Archer": "Glacier Archer", "Assassin": "Snowshade", "Mage": "Cryo Sage",
        "Paladin": "Winter Guardian", "Rogue": "Ice Veil", "Admiral": "Frostwave Admiral", "Sniper": "Icicle Eye",
        "Outlaw": "Tundra Raider", "Bard": "Frost Chanter", "Scavenger": "Icepicker", "Ritualist": "Blizzard Caller",
        "Commander": "Winter Marshal", "Defender": "Glacier Wall", "Barbarian": "Frostfang Berserker"
    },
    "Rain": {
        "Warrior": "Stormblade", "Archer": "Rainpiercer", "Assassin": "Downpour Phantom", "Mage": "Tempest Sage",
        "Paladin": "Rain Guardian", "Rogue": "Drizzle Runner", "Admiral": "Monsoon Admiral", "Sniper": "Storm Eye",
        "Outlaw": "Flood Raider", "Bard": "Thunder Minstrel", "Scavenger": "Rain Gatherer", "Ritualist": "Stormcaller",
        "Commander": "Tempest Marshal", "Defender": "Monsoon Bastion", "Barbarian": "Flood Berserker"
    },
    "Lava": {
        "Warrior": "Lava Knight", "Archer": "Magmashot", "Assassin": "Crater Shade", "Mage": "Lava Weaver",
        "Paladin": "Molten Guardian", "Rogue": "Emberstepper", "Admiral": "Volcano Admiral", "Sniper": "Ashen Eye",
        "Outlaw": "Inferno Raider", "Bard": "Ember Singer", "Scavenger": "Lava Scraper", "Ritualist": "Volcano Caller",
        "Commander": "Lava Marshal", "Defender": "Obsidian Wall", "Barbarian": "Inferno Berserker"
    },
    "Blood": {
        "Warrior": "Blood Knight", "Archer": "Crimson Archer", "Assassin": "Hemoshade", "Mage": "Bloodweaver",
        "Paladin": "Scarlet Guardian", "Rogue": "Veinrunner", "Admiral": "Crimson Admiral", "Sniper": "Blood Eye",
        "Outlaw": "Red Marauder", "Bard": "Heartbeat Singer", "Scavenger": "Flesh Gatherer", "Ritualist": "Blood Ritualist",
        "Commander": "Crimson Marshal", "Defender": "Scarlet Bastion", "Barbarian": "Gore Berserker"
    },
    "Desert": {
        "Warrior": "Dune Knight", "Archer": "Sandshot Ranger", "Assassin": "Mirage Phantom", "Mage": "Sand Weaver",
        "Paladin": "Sun Dervish", "Rogue": "Dustrunner", "Admiral": "Oasis Admiral", "Sniper": "Mirage Eye",
        "Outlaw": "Wasteland Raider", "Bard": "Desert Songcaller", "Scavenger": "Scrap Nomad", "Ritualist": "Sandcaller",
        "Commander": "Dune Marshal", "Defender": "Sand Bastion", "Barbarian": "Scorpion Berserker"
    },
    "Arcane": {
        "Warrior": "Arcblade Knight", "Archer": "Mystic Ranger", "Assassin": "Rune Phantom", "Mage": "Archsage",
        "Paladin": "Arcane Templar", "Rogue": "Spellstepper", "Admiral": "Ether Admiral", "Sniper": "Rune Eye",
        "Outlaw": "Hex Raider", "Bard": "Arcane Minstrel", "Scavenger": "Relic Hunter", "Ritualist": "Rune Binder",
        "Commander": "Mystic Marshal", "Defender": "Arcane Bastion", "Barbarian": "Spellfury Berserker"
    }
}


def load_json_data(file_path, filename):
    if USE_GIST:
        try:
            response = requests.get(GIST_URL, headers=HEADERS)
            if response.status_code == 200:
                gist_data = response.json()
                content = gist_data['files'].get(filename, {}).get('content', '{}')
                return json.loads(content)
            else:
                print(f"Failed to load {filename} from Gist: {response.status_code}")
                return {}
        except Exception as e:
            print(f"Error loading {filename} from Gist: {e}")
            return {}
    else:
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: {file_path} contains invalid JSON. Recreating storage for {filename}.")
                return {}
        return {}


def save_json_data(file_path, filename, data):
    if USE_GIST:
        try:
            response = requests.get(GIST_URL, headers=HEADERS)
            if response.status_code == 200:
                gist_data = response.json()
                files = gist_data.get('files', {})
                files[filename] = {"content": json.dumps(data, indent=2)}
                response = requests.patch(GIST_URL, headers=HEADERS, json={"files": files})
                if response.status_code not in [200, 201]:
                    raise IOError(f"Failed to save {filename} to Gist: {response.status_code}")
            else:
                raise IOError(f"Failed to fetch Gist for saving {filename}: {response.status_code}")
        except Exception as e:
            raise IOError(f"Error saving {filename} to Gist: {e}")
    else:
        temp_path = file_path.with_suffix(file_path.suffix + ".tmp")
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(temp_path, file_path)
        except Exception as e:
            if temp_path.exists():
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
            raise IOError(f"Failed to save {filename}: {e}")


def load_user_heroes():
    """Load all user heroes from Gist or file"""
    if USE_GIST:
        try:
            response = requests.get(GIST_URL, headers=HEADERS)
            if response.status_code == 200:
                gist_data = response.json()
                heroes_content = gist_data['files'].get('user_heroes.json', {}).get('content', '{}')
                return json.loads(heroes_content)
            else:
                print(f"Failed to load from Gist: {response.status_code}")
                return {}
        except Exception as e:
            print(f"Error loading from Gist: {e}")
            return {}
    else:
        if HEROES_FILE.exists():
            try:
                with open(HEROES_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: {HEROES_FILE} contains invalid JSON. Recreating hero storage.")
                return {}
        return {}

def save_user_heroes(heroes_data):
    """Save all user heroes to Gist or file"""
    if USE_GIST:
        try:
            # Get current Gist data
            response = requests.get(GIST_URL, headers=HEADERS)
            if response.status_code == 200:
                gist_data = response.json()
                files = gist_data.get('files', {})
                # Update heroes
                files['user_heroes.json'] = {
                    "content": json.dumps(heroes_data, indent=2)
                }
                data = {"files": files}
                response = requests.patch(GIST_URL, headers=HEADERS, json=data)
                if response.status_code not in [200, 201]:
                    raise IOError(f"Failed to save heroes to Gist: {response.status_code}")
            else:
                raise IOError(f"Failed to fetch Gist for saving: {response.status_code}")
        except Exception as e:
            raise IOError(f"Error saving heroes to Gist: {e}")
    else:
        temp_path = HEROES_FILE.with_suffix(HEROES_FILE.suffix + ".tmp")
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(heroes_data, f, indent=2)
            os.replace(temp_path, HEROES_FILE)
        except Exception as e:
            if temp_path.exists():
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
            raise IOError(f"Failed to save hero data: {e}")


def load_user_roll_counts():
    """Load persisted roll counts for users."""
    return load_json_data(ROLL_COUNTER_FILE, 'user_roll_counts.json')


def save_user_roll_counts(counts):
    """Save persisted roll counts for users."""
    save_json_data(ROLL_COUNTER_FILE, 'user_roll_counts.json', counts)


def increment_user_roll_count(user_id):
    """Increment the roll count for a user and return the new count."""
    counts = load_user_roll_counts()
    user_id_str = str(user_id)
    current_count = counts.get(user_id_str, 0)
    new_count = current_count + 1
    counts[user_id_str] = new_count
    save_user_roll_counts(counts)
    return new_count


def load_emporium_state():
    return load_json_data(EMPORIUM_STATE_FILE, 'emporium_state.json')


def save_emporium_state(state):
    save_json_data(EMPORIUM_STATE_FILE, 'emporium_state.json', state)


def load_user_items():
    return load_json_data(USER_ITEMS_FILE, 'user_items.json')


def save_user_items(items):
    save_json_data(USER_ITEMS_FILE, 'user_items.json', items)


def load_user_boosts():
    return load_json_data(USER_BOOSTS_FILE, 'user_boosts.json')


def save_user_boosts(boosts):
    save_json_data(USER_BOOSTS_FILE, 'user_boosts.json', boosts)


def load_nemesis_state():
    state = load_json_data(NEMESIS_STATE_FILE, 'nemesis_state.json')
    if not state:
        return {"active": {}}
    if "active" not in state:
        state["active"] = {}
    return state


def save_nemesis_state(state):
    save_json_data(NEMESIS_STATE_FILE, 'nemesis_state.json', state)


def get_user_nemesis(user_id):
    state = load_nemesis_state()
    return state.get("active", {}).get(str(user_id))


def set_user_nemesis(user_id, nemesis_data):
    state = load_nemesis_state()
    state.setdefault("active", {})[str(user_id)] = nemesis_data
    save_nemesis_state(state)


def remove_user_nemesis(user_id):
    state = load_nemesis_state()
    if str(user_id) in state.get("active", {}):
        del state["active"][str(user_id)]
        save_nemesis_state(state)


def has_active_nemesis(user_id):
    return get_user_nemesis(user_id) is not None


def add_nemesis_victory(user_id):
    nemesis = get_user_nemesis(user_id)
    if not nemesis:
        return None
    nemesis["victories"] = nemesis.get("victories", 0) + 1
    if nemesis["victories"] >= NEMESIS_REQUIRED_VICTORIES:
        nemesis["defeated"] = True
        nemesis["pending_finish"] = True
        nemesis["defeated_at"] = datetime.datetime.utcnow().isoformat()
    set_user_nemesis(user_id, nemesis)
    return nemesis


def get_nemesis_debuff(user_id):
    nemesis = get_user_nemesis(user_id)
    if not nemesis:
        return None
    debuff = nemesis.get("hide_debuff")
    if not debuff:
        return None
    try:
        expires_at = datetime.datetime.fromisoformat(debuff.get("expires_at"))
    except Exception:
        return None
    if datetime.datetime.utcnow() >= expires_at:
        nemesis.pop("hide_debuff", None)
        set_user_nemesis(user_id, nemesis)
        return None
    return debuff


def choose_nemesis_rarity():
    pool = [tier[1] for tier in RARITY_TIERS]
    weights = [40, 25, 15, 8, 5, 3, 2, 1, 1, 1, 0.7, 0.3, 0.2, 0.1]
    return random.choices(pool, weights=weights, k=1)[0]


def choose_nemesis_class_title():
    pool = [title for _, title in CLASS_TIERS]
    weights = [15, 25, 20, 15, 10, 8, 5, 2]
    return random.choices(pool, weights=weights, k=1)[0]


def increase_rarity_by_steps(rarity, steps):
    order = [name for _, name in RARITY_TIERS]
    if rarity not in order:
        return rarity
    idx = order.index(rarity)
    new_index = min(idx + steps, len(order) - 1)
    return order[new_index]


def generate_nemesis_hero():
    alignment = random.choice(list(ALIGNMENT_TITLE_MAP.keys()))
    divinity = random.choice(list(DIVINITY_TITLE_MAP.keys()))
    race = random.choice([
        "Human", "Construct", "Elven", "Goblin", "Beast", "Ogre", "Deep-Crawler",
        "Celestial", "Angel", "Demon", "Dwarf", "Elemental", "Undead", "Magma-Crawler"
    ])
    element = random.choice(list(ELEMENTS.keys()))
    clazz = random.choice(CLASSES)
    rarity = choose_nemesis_rarity()
    class_title = choose_nemesis_class_title()
    name = random_name()
    feat = roll_feat(rarity)
    element_good, element_bad = ELEMENTS[element]
    element_part = f" the {element_good}" if random.random() < 0.65 else ""
    element_title = element_good if element_part else element
    full_name = f"{class_title} {clazz} {name}{element_part} - ({rarity})"

    return {
        "full_name": full_name,
        "hero_name": name,
        "class": clazz,
        "class_title": class_title,
        "rarity": rarity,
        "divinity": divinity,
        "alignment": alignment,
        "race": race,
        "element": element_title,
        "element_raw": element,
        "element_part": element_part,
        "feat": feat,
        "shiny": False,
        "created_at": datetime.datetime.utcnow().isoformat(),
    }


# =========================
# 🎲 RANDOM ENCOUNTERS
# =========================

RA_ENCOUNTER_FILE = Path("ra_encounters.json")

EASY_ENCOUNTERS = [
    "Goblin", "Skeleton", "Zombie", "Bandit", "Wolf", "Cave Spider", "Slime", "Rat Swarm",
    "Wild Boar", "Scout Rogue", "Kobold", "Ghoul", "Bat Swarm", "Mud Crawler", "Thief",
    "Cultist", "Stray Hound", "Bone Hound", "Forest Imp", "Mimic Chest", "Rotling", "Cave Dweller",
    "Rogue Mercenary", "Bog Toad", "Burrower", "Feral Villager", "Stone Gremlin", "Wandering Duelist",
    "Crypt Rat", "Swamp Leech", "Prowler", "Ransacker", "Grave Robber", "Tunnel Lurker", "Corrupted Farmer"
]

NORMAL_ENCOUNTERS = [
    "Orc", "Ogre", "Troll", "Necromancer", "Dark Knight", "Wyvern", "Harpy", "Werewolf",
    "Executioner", "Battle Mage", "Warlock", "Shadow Stalker", "Bone Giant", "Drake", "Wraith",
    "Plague Doctor", "Dread Soldier", "Flesh Golem", "Bounty Hunter", "Minotaur", "Crypt Keeper",
    "Ghast", "Mutant Beast", "Raid Captain", "Blood Hunter", "Masked Assassin", "Cursed Monk",
    "Arena Champion", "Revenant", "Pit Beast", "Crawling Horror", "Ravager", "Ancient Guardian",
    "Fallen Paladin", "Cavern Beast"
]

CHALLENGING_ENCOUNTERS = [
    "Ancient Dragon", "Titan", "Lich King", "Void Reaper", "World Serpent", "Demon Lord", "Colossus",
    "Fallen Angel", "Behemoth", "Hydra", "Soul Tyrant", "Abyss Walker", "Death Knight", "Elder Vampire",
    "Chaos Beast", "Dread Titan", "Celestial Hunter", "Nightmare Monarch", "Ancient Warden", "Voidspawn",
    "Rift Stalker", "Bone Colossus", "Warbringer", "Immortal Gladiator", "Crownless King",
    "Shadow Leviathan", "Forgotten Godling", "Eternal Sentinel", "Doom Herald", "Plague Tyrant",
    "Ancient Chimera", "Execution Monarch", "Reality Eater", "Primeval Beast", "The Hollow One"
]

ALIGNMENT_TITLE_MAP = {
    "Valiant": "Tyrannical",
    "Good": "Wicked",
    "Neutral": "Unstable",
    "Mischievous": "Lawbound",
    "Evil": "Righteous",
}

DIVINITY_TITLE_MAP = {
    "Divine": "Demonic",
    "Neutral": "Twisted",
    "Hellish": "Sanctified",
}

CLASS_TITLE_MAP = {
    "Warrior": "Berserker",
    "Archer": "Marksman",
    "Assassin": "Watcher",
    "Mage": "Spellbound",
    "Paladin": "Oathbreaker",
    "Rogue": "Cutthroat",
    "Admiral": "Dread Captain",
    "Sniper": "Deadeye",
    "Outlaw": "Bandit King",
    "Bard": "Dirgesinger",
    "Scavenger": "Scrapfiend",
    "Ritualist": "Cultist",
    "Commander": "Warlord",
    "Defender": "Juggernaut",
    "Barbarian": "Ravager",
}

ELEMENT_TITLE_MAP = {
    "Fire": "Frostbitten",
    "Water": "Parched",
    "Earth": "Skybound",
    "Air": "Grounded",
    "Steel": "Corroded",
    "Glass": "Shatterbound",
    "Light": "Shadowed",
    "Dark": "Radiant",
    "Equinox": "Imbalanced",
    "Celestial": "Fallen",
    "Beast": "Tamed",
    "Lightning": "Discharged",
    "Magma": "Cooled",
    "Spore": "Purified",
    "Crystal": "Fractured",
    "Color": "Faded",
    "Plants": "Withered",
    "Poison": "Cleansed",
    "Corruption": "Redeemed",
    "Mist": "Revealed",
    "Death": "Living",
    "Life": "Hollow",
    "Ice": "Melted",
    "Rain": "Droughtborn",
    "Lava": "Hardened",
    "Blood": "Bloodless",
    "Desert": "Drowned",
    "Arcane": "Silenced",
}

DIFFICULTY_POOLS = {
    "Easy": EASY_ENCOUNTERS,
    "Normal": NORMAL_ENCOUNTERS,
    "Challenging": CHALLENGING_ENCOUNTERS,
}

RARITY_POOLS = {
    "Easy": ["Common", "Trained", "Uncommon", "Handy"],
    "Normal": ["Rare", "Pseudo", "Genesis"],
    "Challenging": ["Legendary", "Mythical", "Ethereal", "Ascendant", "Primordial", "Omni", "God-Challenger"],
}

RARITY_WEIGHTS = {
    "Easy": [45, 30, 20, 5],
    "Normal": [60, 30, 10],
    "Challenging": [55, 25, 12, 4, 2, 1, 1],
}

ENCOUNTER_UPGRADE_BASE = {
    "Easy": 0.07,
    "Normal": 0.11,
    "Challenging": 0.15,
}

REQUIREMENT_CATEGORIES = ["alignment", "divinity", "class", "element"]
REQUIREMENT_LABELS = {
    "alignment": "Alignment",
    "divinity": "Divinity",
    "class": "Class",
    "element": "Element",
}

REQUIREMENT_VALUE_OPTIONS = {
    "alignment": list(ALIGNMENT_TITLE_MAP.keys()),
    "divinity": list(DIVINITY_TITLE_MAP.keys()),
    "class": list(CLASS_TITLE_MAP.keys()),
    "element": list(ELEMENT_TITLE_MAP.keys()),
}

REQUIREMENT_TITLE_MAPS = {
    "alignment": ALIGNMENT_TITLE_MAP,
    "divinity": DIVINITY_TITLE_MAP,
    "class": CLASS_TITLE_MAP,
    "element": ELEMENT_TITLE_MAP,
}


def load_ra_encounter_state():
    state = load_json_data(RA_ENCOUNTER_FILE, 'ra_encounters.json')
    if not state:
        return {"next_id": 1, "active": {}}
    if "next_id" not in state:
        state["next_id"] = 1
    if "active" not in state:
        state["active"] = {}
    return state


def save_ra_encounter_state(state):
    save_json_data(RA_ENCOUNTER_FILE, 'ra_encounters.json', state)


def get_next_ra_encounter_id(state):
    next_id = state.get("next_id", 1)
    state["next_id"] = next_id + 1
    return next_id


def build_hero_full_name(hero):
    hero_name = hero.get("hero_name")
    if not hero_name:
        full_name = hero.get("full_name", "Unknown")
        if " - (" in full_name:
            prefix = full_name.rsplit(" - (", 1)[0]
            parts = prefix.split(" ", 2)
            if len(parts) >= 3:
                hero_name = parts[2]
            else:
                hero_name = prefix
        else:
            hero_name = full_name

    clazz = hero.get("class", "Unknown")
    class_title = hero.get("class_title", "Okay")
    rarity = hero.get("rarity", "Common")
    element_part = hero.get("element_part", "")
    if element_part and element_part not in hero_name:
        hero_name = f"{hero_name}{element_part}"
    return f"{class_title} {clazz} {hero_name} - ({rarity})"


def choose_ra_requirements():
    count = random.choices([1, 2, 3], weights=[55, 30, 15], k=1)[0]
    categories = random.sample(REQUIREMENT_CATEGORIES, count)
    requirements = []
    for category in categories:
        value = random.choice(REQUIREMENT_VALUE_OPTIONS[category])
        title = REQUIREMENT_TITLE_MAPS[category].get(value, value)
        requirements.append({"category": category, "value": value, "title": title})
    return requirements


def choose_ra_required_rarity(difficulty):
    pool = RARITY_POOLS.get(difficulty, RARITY_POOLS["Easy"])
    weights = RARITY_WEIGHTS.get(difficulty, [1] * len(pool))
    return random.choices(pool, weights=weights, k=1)[0]


def choose_ra_enemy(difficulty):
    return random.choice(DIFFICULTY_POOLS.get(difficulty, EASY_ENCOUNTERS))


def get_ra_requirement_title(requirements, enemy_name):
    if not requirements:
        return enemy_name
    main = random.choice(requirements)
    title = main.get("title", enemy_name)
    return f"{title} {enemy_name}"


def format_ra_requirements(requirements, encounter=None):
    if encounter and encounter.get("sought_out"):
        target_name = encounter.get("target_hero_name", "the sought-out hero")
        return f"- Only **{target_name}** may attempt this encounter."
    if not requirements:
        return "- No special requirements."
    return "\n".join([f"- {REQUIREMENT_LABELS[r['category']]}: {r['value']}" for r in requirements])


def hero_matches_ra_requirements(hero, encounter):
    if encounter.get("sought_out"):
        if hero.get("id") != encounter.get("target_hero_id"):
            target_name = encounter.get("target_hero_name", "the sought-out hero")
            return False, f"This encounter was sought out for **{target_name}** and only that hero may attempt it."
        return True, None

    if not rarity_meets_requirement(hero.get("rarity", "Common"), encounter.get("required_rarity", "Common")):
        return False, f"That hero must be at least **{encounter.get('required_rarity', 'Common')}** rarity to attempt this encounter."

    for req in encounter.get("requirements", []):
        if req["category"] == "alignment" and hero.get("alignment") != req["value"]:
            return False, f"Requires {req['value']} alignment. Your hero has {hero.get('alignment', 'Unknown')}."
        if req["category"] == "divinity" and hero.get("divinity") != req["value"]:
            return False, f"Requires {req['value']} divinity. Your hero has {hero.get('divinity', 'Unknown')}."
        if req["category"] == "class" and hero.get("class") != req["value"]:
            return False, f"Requires {req['value']} class. Your hero is {hero.get('class', 'Unknown')}."
        if req["category"] == "element" and hero.get("element_raw", hero.get("element", "")) != req["value"]:
            return False, f"Requires {req['value']} element. Your hero has {hero.get('element_raw', hero.get('element', 'Unknown'))}."
    return True, None


def build_ra_encounter_embed(encounter):
    embed = discord.Embed(title="🧭 Random Encounter", color=0x00ffcc)
    embed.add_field(name="Encounter ID", value=str(encounter["id"]), inline=True)
    embed.add_field(name="Difficulty", value=encounter["difficulty"], inline=True)
    embed.add_field(name="Encounter", value=encounter["title"], inline=False)
    required_rarity_text = "No rarity requirement" if encounter.get("sought_out") else encounter.get("required_rarity", "Unknown")
    embed.add_field(name="Required Rarity", value=required_rarity_text, inline=True)
    embed.add_field(name="Requirements", value=format_ra_requirements(encounter.get("requirements", []), encounter), inline=False)
    if encounter.get("sought_out"):
        embed.add_field(name="Sought Out By", value=encounter.get("sought_out_person", "Unknown"), inline=True)
        embed.add_field(name="Sought Hero", value=f"#{encounter.get('target_hero_id')} — {encounter.get('target_hero_name', 'Unknown')}", inline=True)
    if encounter.get("special_type") == "potential_nemesis":
        nemesis_hero = encounter.get("nemesis_hero", {})
        embed.add_field(name="Potential Nemesis", value=nemesis_hero.get("full_name", "Unknown"), inline=False)
        embed.add_field(name="Choice", value="After facing the menace, use `!SpareGP` to spare it or `!KillGP` to slay it.", inline=False)
    if encounter.get("special_type") == "nemesis_challenge":
        embed.add_field(name="Nemesis Trial", value="A reflex test begins. Use `Strike` or `Shield` when prompted.", inline=False)
    if encounter.get("special_type") == "nemesis_minion":
        embed.add_field(name="Nemesis Minion", value="Only a high-ranked hero can defeat this servant of your Nemesis.", inline=False)
    embed.set_footer(text=f"Use !FaceRA {encounter['id']} <Hero ID> to attempt the encounter.")
    return embed


def get_rarity_order():
    return {name: index for index, (_, name) in enumerate(RARITY_TIERS)}


def get_class_title_order():
    return [name for _, name in CLASS_TIERS]


def increase_hero_rarity(hero):
    order = get_rarity_order()
    current_index = order.get(hero.get("rarity", "Common"), 0)
    if current_index + 1 >= len(RARITY_TIERS):
        return False
    new_rarity = RARITY_TIERS[current_index + 1][1]
    hero["rarity"] = new_rarity
    hero["full_name"] = build_hero_full_name(hero)
    return True


def increase_hero_class_title(hero):
    titles = get_class_title_order()
    try:
        current_index = titles.index(hero.get("class_title", "Okay"))
    except ValueError:
        current_index = 1
    if current_index + 1 >= len(titles):
        return False
    hero["class_title"] = titles[current_index + 1]
    hero["full_name"] = build_hero_full_name(hero)
    return True


def get_ra_upgrade_chance(hero_rarity, required_rarity, difficulty):
    order = get_rarity_order()
    hero_index = order.get(hero_rarity, 0)
    required_index = order.get(required_rarity, 0)
    base = ENCOUNTER_UPGRADE_BASE.get(difficulty, 0.07)
    if hero_index <= required_index:
        modifier = 1.0
    elif hero_index == required_index + 1:
        modifier = 0.75
    elif hero_index == required_index + 2:
        modifier = 0.55
    else:
        modifier = 0.40
    return base * modifier


def get_ra_encounter_message(encounter):
    return (
        f"**RANDOM ENCOUNTER READY!**\n"
        f"Encounter ID: **{encounter['id']}**\n"
        f"Difficulty: **{encounter['difficulty']}**\n"
        f"Encounter: **{encounter['title']}**\n"
        f"Required Rarity: **{encounter.get('required_rarity', 'Unknown')}**\n"
        f"Requirements:\n{format_ra_requirements(encounter.get('requirements', []), encounter)}\n\n"
        f"Use `!FaceRA {encounter['id']} <Hero ID>` to attempt this encounter. "
        f"Higher rarity heroes can still attempt, but they have a smaller chance to gain a bonus upgrade."
    )


def remove_user_ra_encounter(state, user_id):
    active = state.get("active", {})
    if str(user_id) in active:
        del active[str(user_id)]
        save_ra_encounter_state(state)


def add_item_to_user(user_id, item_data):
    items = load_user_items()
    user_id_str = str(user_id)
    if user_id_str not in items:
        items[user_id_str] = []
    item_data["id"] = get_next_item_id(user_id)
    items[user_id_str].append(item_data)
    save_user_items(items)


def remove_item_from_user(user_id, item_id):
    items = load_user_items()
    user_id_str = str(user_id)
    user_items = items.get(user_id_str, [])
    remaining_items = [item for item in user_items if item.get("id") != item_id]
    if len(remaining_items) == len(user_items):
        return None
    items[user_id_str] = remaining_items
    save_user_items(items)
    return next((item for item in user_items if item.get("id") == item_id), None)


def get_user_items(user_id):
    items = load_user_items()
    return items.get(str(user_id), [])


def set_user_boost(user_id, boost_data):
    boosts = load_user_boosts()
    boosts[str(user_id)] = boost_data
    save_user_boosts(boosts)


def pop_user_boost(user_id):
    boosts = load_user_boosts()
    boost = boosts.pop(str(user_id), None)
    save_user_boosts(boosts)
    return boost


def rarity_meets_requirement(hero_rarity, requirement_rarity):
    order = get_rarity_order()
    return order.get(hero_rarity, -1) >= order.get(requirement_rarity, -1)


def get_reward_items_for_rank(rank):
    if rank == "Legendary":
        return [
            {"name": "Enchanted Luck Stone", "type": "luck", "description": "Good overall rank luck boost on your next roll.", "multiplier": 1.30},
            {"name": "Elite Training Order", "type": "class", "description": "Good class rank luck boost on your next roll.", "multiplier": 1.30},
            {"name": "Evolution Stone", "type": "evolution", "description": "A mystical stone that can evolve a hero's title based on their element and class.", "multiplier": 1.0},
        ]
    if rank == "Rare":
        return [
            {"name": "Natural Luck Stone", "type": "luck", "description": "Mild overall rank luck boost on your next roll.", "multiplier": 1.20},
            {"name": "Normal Training Order", "type": "class", "description": "Mild class rank luck boost on your next roll.", "multiplier": 1.20},
        ]
    return [
        {"name": "Weak Luck Stone", "type": "luck", "description": "Teensy overall rank luck boost on your next roll.", "multiplier": 1.10},
        {"name": "Weak Training Order", "type": "class", "description": "Teensy class rank luck boost on your next roll.", "multiplier": 1.10},
    ]

RA_REWARD_POOLS = {
    "Easy": [
        {"name": "Weak Luck Stone", "type": "luck", "description": "Teensy overall luck boost from an easy victory.", "multiplier": 1.10},
        {"name": "Weak Training Order", "type": "class", "description": "Teensy class training boost from an easy victory.", "multiplier": 1.10},
        {"name": "Evolution Stone", "type": "evolution", "description": "A mystical stone that can evolve a hero's title based on their element and class.", "multiplier": 1.0},
    ],
    "Normal": [
        {"name": "Natural Luck Stone", "type": "luck", "description": "Balanced overall luck boost from a solid victory.", "multiplier": 1.20},
        {"name": "Normal Training Order", "type": "class", "description": "Balanced class training boost from a solid victory.", "multiplier": 1.20},
        {"name": "Evolution Stone", "type": "evolution", "description": "A mystical stone that can evolve a hero's title based on their element and class.", "multiplier": 1.0},
    ],
    "Challenging": [
        {"name": "Enchanted Luck Stone", "type": "luck", "description": "Strong overall luck boost from a hard-fought victory.", "multiplier": 1.30},
        {"name": "Elite Training Order", "type": "class", "description": "Strong class training boost from a hard-fought victory.", "multiplier": 1.30},
        {"name": "Evolution Stone", "type": "evolution", "description": "A mystical stone that can evolve a hero's title based on their element and class.", "multiplier": 1.0},
    ],
}


def get_ra_reward_for_difficulty(difficulty):
    return RA_REWARD_POOLS.get(difficulty, RA_REWARD_POOLS["Easy"])


def try_grant_ra_reward(user_id, difficulty):
    if random.random() >= 0.4:
        return None
    reward_item = random.choice(get_ra_reward_for_difficulty(difficulty))
    item_data = {
        "name": reward_item["name"],
        "type": reward_item["type"],
        "description": reward_item["description"],
        "multiplier": reward_item["multiplier"],
        "created_at": datetime.datetime.utcnow().isoformat(),
    }
    add_item_to_user(user_id, item_data)
    return item_data


def get_required_rarity_choices():
    return ["Uncommon", "Rare", "Legendary"]

def add_hero_to_user(user_id, hero_data):
    """Add a hero to a user's collection"""
    heroes = load_user_heroes()
    user_id_str = str(user_id)
    
    if user_id_str not in heroes:
        heroes[user_id_str] = []

    hero_data["id"] = get_next_hero_id(user_id)
    heroes[user_id_str].append(hero_data)
    save_user_heroes(heroes)

def get_user_heroes(user_id):
    """Get all heroes for a specific user"""
    heroes = load_user_heroes()
    return heroes.get(str(user_id), [])

def get_next_hero_id(user_id, user_heroes=None):
    """Get the next hero ID for a user's collection."""
    if user_heroes is None:
        user_heroes = get_user_heroes(user_id)

    max_id = 0
    for hero in user_heroes:
        try:
            hero_id = int(hero.get("id", 0))
            if hero_id > max_id:
                max_id = hero_id
        except (TypeError, ValueError):
            continue
    return max_id + 1


def choose_emporium_requirement():
    rank = random.choice(get_required_rarity_choices())
    category = random.choice(["class", "element"])
    if category == "class":
        item = random.choice(CLASSES)
    else:
        item = random.choice(list(ELEMENTS.keys()))
    return rank, category, item


def build_emporium_state():
    rank, category, item = choose_emporium_requirement()
    reward_item = random.choice(get_reward_items_for_rank(rank))
    requirement_text = f"{rank} {item}"
    flavor = random.choice(EMPORIUM_SCENARIOS).replace("[requirements]", requirement_text)

    return {
        "target_rarity": rank,
        "target_category": category,
        "target_item": item,
        "requirement_text": requirement_text,
        "reward_item": reward_item,
        "flavor_text": flavor,
        "trade_counts": {},
        "refreshed_at": datetime.datetime.utcnow().isoformat(),
        "trade_limit_per_user": 2,
    }


def refresh_emporium_state():
    state = build_emporium_state()
    save_emporium_state(state)
    return state


def get_emporium_state():
    state = load_emporium_state()
    if not state:
        state = refresh_emporium_state()
    return state


def load_event_state():
    """Load the persisted event state from disk."""
    if EVENT_STATE_FILE.exists():
        try:
            with open(EVENT_STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading event state: {e}")
    return None


def save_event_state(state):
    """Persist the current event state to disk."""
    try:
        with open(EVENT_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"Error saving event state: {e}")


def choose_random_event(exclude_name=None):
    """Choose a random event, optionally excluding the current one."""
    options = [event for event in EVENTS if event["name"] != exclude_name]
    if not options:
        options = EVENTS
    return random.choice(options)


def build_event_state(event):
    """Build a new persisted state for an event announcement."""
    now = datetime.datetime.utcnow()
    return {
        "name": event["name"],
        "boost": event["boost"],
        "details": event.get("details", ""),
        "classes": event.get("classes", []),
        "elements": event.get("elements", []),
        "race": event.get("race", []),
        "started_at": now.isoformat(),
        "expires_at": (now + datetime.timedelta(seconds=EVENT_DURATION_SECONDS)).isoformat(),
        "next_announcement_at": (now + datetime.timedelta(seconds=EVENT_MESSAGE_INTERVAL_SECONDS)).isoformat(),
        "announcement_messages": [],
    }


def format_event_announcement(state, forced_by=None):
    """Create the announcement text for the current event."""
    title = state["name"]
    boost = state["boost"]
    details = state.get("details", "")
    
    # Calculate remaining time
    expires_at = datetime.datetime.fromisoformat(state.get("expires_at"))
    now = datetime.datetime.utcnow()
    time_remaining = expires_at - now
    
    # Format time remaining as HH:MM:SS or MM:SS
    total_seconds = int(time_remaining.total_seconds())
    if total_seconds < 0:
        time_str = "0:00"
    else:
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        if hours > 0:
            time_str = f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            time_str = f"{minutes}:{seconds:02d}"
    
    footer = "A new event has begun! It lasts 7 hours."
    if forced_by:
        footer = f"Forced into motion by {forced_by}. New event lasts 7 hours."
    return (
        f"🌟 **{title}** is now active!\n{boost}\n\n{details}\n\n"
        f"The Adventures Exchange has been refreshed.\n\n"
        f"{time_str} remain\n\n{footer}"
    )


def format_event_ended_message(state):
    """Create the announcement text for an ended event."""
    return "This Event has ended, a new one has started!"


async def mark_previous_event_ended(state):
    """Edit previous event announcement messages to indicate the event has ended."""
    if not state:
        return
    ended_message = format_event_ended_message(state)
    for entry in state.get("announcement_messages", []):
        guild = bot.get_guild(entry["guild_id"])
        if not guild:
            continue
        channel = guild.get_channel(entry["channel_id"])
        if not channel:
            continue
        try:
            msg = await channel.fetch_message(entry["message_id"])
            await msg.edit(content=ended_message)
        except discord.NotFound:
            continue
        except discord.Forbidden:
            continue
        except Exception as e:
            print(f"Failed to mark previous event ended for guild {guild.name}: {e}")


def get_announcement_channel(guild):
    """Find a channel in the guild where the bot can send announcements."""
    # First, try to find a channel named "godpool-events"
    for channel in guild.text_channels:
        if channel.name == "godpool-events" and channel.permissions_for(guild.me).send_messages:
            return channel
    # Fallback to system channel
    if guild.system_channel and guild.system_channel.permissions_for(guild.me).send_messages:
        return guild.system_channel
    # Fallback to any text channel
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            return channel
    return None


async def send_global_announcement(message):
    """Send the same announcement message to every guild the bot is in."""
    sent_messages = []
    for guild in bot.guilds:
        channel = get_announcement_channel(guild)
        if channel is not None:
            try:
                msg = await channel.send(message)
                sent_messages.append({
                    "guild_id": guild.id,
                    "channel_id": channel.id,
                    "message_id": msg.id,
                })
            except Exception as e:
                print(f"Failed to send announcement to {guild.name}: {e}")
    return sent_messages


@tasks.loop(seconds=60)
async def event_countdown_updater():
    """Update the remaining time on active event announcement messages."""
    state = load_event_state()
    if not state or not is_event_active(state):
        return
    announcement_messages = state.get("announcement_messages", [])
    if not announcement_messages:
        return
    updated_message = format_event_announcement(state)
    for entry in announcement_messages:
        guild = bot.get_guild(entry["guild_id"])
        if not guild:
            continue
        channel = guild.get_channel(entry["channel_id"])
        if not channel:
            continue
        try:
            msg = await channel.fetch_message(entry["message_id"])
            await msg.edit(content=updated_message)
        except discord.NotFound:
            continue
        except discord.Forbidden:
            continue
        except Exception as e:
            print(f"Failed to update event countdown for guild {guild.name}: {e}")


@tasks.loop(minutes=10)
async def nemesis_hunt_scheduler():
    state = load_nemesis_state()
    now = datetime.datetime.utcnow()
    active_nemeses = state.get("active", {})
    any_changed = False
    for user_id_str, nemesis in active_nemeses.items():
        if nemesis.get("pending_finish"):
            continue
        if nemesis.get("pending_hunt"):
            continue
        next_hunt = nemesis.get("next_hunt_at")
        if next_hunt:
            try:
                next_hunt_time = datetime.datetime.fromisoformat(next_hunt)
            except Exception:
                next_hunt_time = now
        else:
            next_hunt_time = now

        if now < next_hunt_time:
            continue

        nemesis["next_hunt_at"] = (now + datetime.timedelta(hours=NEMESIS_HUNT_INTERVAL_HOURS)).isoformat()
        if random.random() < NEMESIS_HUNT_CHANCE:
            nemesis["pending_hunt"] = {
                "status": "waiting_choice",
                "created_at": now.isoformat(),
            }
            any_changed = True
            user = await bot.fetch_user(int(user_id_str))
            if user:
                hero_name = nemesis.get("spawned_by_hero_name", "your hero")
                try:
                    await user.send(
                        f"🖤 **{nemesis['hero'].get('full_name', 'The Nemesis')}** is hunting for **{hero_name}**.\n"
                        "Use `!HideGP` to hide or `!ConfrontGP` to confront the Nemesis hunt."
                    )
                except Exception:
                    pass

    if any_changed:
        save_nemesis_state(state)


def is_event_active(state):
    """Check whether the current event is still active."""
    if not state:
        return False
    try:
        expires_at = datetime.datetime.fromisoformat(state.get("expires_at"))
        return datetime.datetime.utcnow() < expires_at
    except Exception:
        return False


def get_current_event():
    """Return the event state loaded into memory or from disk."""
    global ACTIVE_EVENT_STATE
    if ACTIVE_EVENT_STATE is None:
        ACTIVE_EVENT_STATE = load_event_state()
    return ACTIVE_EVENT_STATE


def set_current_event(state):
    """Persist and store the active event state."""
    global ACTIVE_EVENT_STATE
    ACTIVE_EVENT_STATE = state
    save_event_state(state)


def choose_and_activate_event(exclude_name=None):
    """Choose a new event, persist it, and return the state."""
    event = choose_random_event(exclude_name=exclude_name)
    state = build_event_state(event)
    set_current_event(state)
    return state


def apply_event_boosts(alignment, divinity, element, clazz, race, align_roll, div_roll, elem_roll, class_roll, shiny_chance):
    """Modify roll values based on the active event (multiplicative system)."""
    state = get_current_event()
    if not is_event_active(state):
        return align_roll, div_roll, elem_roll, class_roll, shiny_chance

    event_name = state["name"]
    if event_name == "Blood Moon Rising":
        if alignment in ["Death", "Corruption", "Evil"]:
            align_roll *= random.uniform(1.05, 1.15)
    elif event_name == "Celestial Convergence":
        if divinity == "Divine":
            div_roll *= random.uniform(1.05, 1.15)
        if element == "Celestial":
            elem_roll *= random.uniform(1.05, 1.15)
    elif event_name == "Infernal Surge":
        if element in ["Lava", "Magma", "Fire"]:
            elem_roll *= random.uniform(1.08, 1.2)
            if random.random() < 0.2:
                elem_roll *= random.uniform(0.9, 1.1)
    elif event_name == "The Hollow Fog":
        if element in ["Mist", "Dark"]:
            shiny_chance += 0.04
    elif event_name == "Verdant Bloom":
        if element in ["Plants", "Life"]:
            elem_roll *= random.uniform(1.08, 1.2)
            if elem_roll < 1.0:
                elem_roll *= 0.95
    elif event_name == "Thunder Dominion":
        if element in ["Lightning", "Air"]:
            class_roll *= random.uniform(1.08, 1.18)
    elif event_name == "The Drowned Tide":
        if element in ["Water", "Rain"]:
            elem_roll *= random.uniform(1.08, 1.2)
            shiny_chance += 0.03
    elif event_name == "Gravecall Night":
        if race == "Undead" or element == "Death":
            align_roll *= random.uniform(1.1, 1.25)
    elif event_name == "Prismatic Awakening":
        if element in ["Glass", "Crystal", "Color"]:
            class_roll *= random.uniform(1.08, 1.2)
    elif event_name == "The Beast Hunt":
        if race == "Beast" or element == "Beast":
            class_roll *= random.uniform(1.08, 1.2)
    elif event_name == "Eclipse of Judgment":
        align_roll *= random.uniform(1.08, 1.2)
    elif event_name == "Forgeheart Festival":
        if element in ["Steel", "Earth"]:
            elem_roll *= random.uniform(1.08, 1.2)
    elif event_name == "The Rotting Bloom":
        if element in ["Spore", "Poison"]:
            elem_roll *= random.uniform(1.1, 1.3)
            shiny_chance += 0.05
    elif event_name == "Starfall Cataclysm":
        if element in ["Celestial", "Equinox"]:
            align_roll *= random.uniform(1.08, 1.2)
            class_roll *= random.uniform(1.08, 1.18)
    elif event_name == "The Ashen Era":
        if element in ["Fire", "Lava", "Magma"]:
            class_roll *= random.uniform(1.08, 1.2)
    elif event_name == "Sanctuary of Dawn":
        if element == "Light" or alignment in ["Good", "Valiant"]:
            if div_roll < 1.0:
                div_roll *= 1.08
            if align_roll < 1.0:
                align_roll *= 1.08
    elif event_name == "The Rift Collapse":
        elem_roll *= 1.3
    elif event_name == "The Wandering Tempest":
        if element in ["Air", "Rain", "Lightning"]:
            elem_roll *= random.uniform(1.08, 1.2)
    elif event_name == "Kingdoms at War":
        if clazz in ["Commander", "Paladin", "Admiral", "Warrior"]:
            class_roll *= random.uniform(1.15, 1.35)
    elif event_name == "The Abyss Stares Back":
        if element in ["Corruption", "Dark"] or alignment in ["Mischievous", "Evil"]:
            bonus = random.uniform(1.0, 1.15)
            align_roll *= bonus
            elem_roll *= random.uniform(0.98, 1.1)

    return align_roll, div_roll, elem_roll, class_roll, shiny_chance

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
    "Gravron", "Sykang", "Bralen", "Morvek", "Harkan", "Velorin", "Caldor", "Fenric",
"Druven", "Korrin", "Lareth", "Myrion", "Selran", "Tavric", "Vornak", "Zelmir",
"Arken", "Brennar", "Calyth", "Draven", "Eldrid", "Farron", "Gorlan", "Havren",
"Ithran", "Jorvik", "Kalren", "Lyrion", "Mavros", "Norwyn", "Orvyn", "Perrik",
"Quorin", "Ravell", "Sarvik", "Thalen", "Ulmar", "Varcor", "Wesryn", "Xandar",
"Yorlan", "Zaren", "Aldric", "Brinor", "Corven", "Dasker", "Elyon", "Fendrith",
"Garron", "Haldor", "Ivron", "Jasker", "Korlen", "Lythar", "Mordek", "Nereth",
"Odran", "Prythe", "Quaric", "Ralen", "Selron", "Tyrvan", "Uldor", "Velmar",
"Wyrik", "Xandor", "Ylven", "Zorin", "Arvex", "Branik", "Cerath", "Dornel",
"Eldran", "Faylen", "Gavric", "Halvor", "Iyren", "Jorath", "Krelan", "Lysen",
"Meral", "Nyrik", "Orren", "Parvik", "Qyros", "Revas", "Sarlen", "Tharic",
"Urven", "Veknor", "Weslor", "Xyran", "Yevon", "Zalrin", "Averon", "Brynd",
"Cavren", "Dornik", "Erasyn", "Fyran", "Grelth", "Havik", "Ithrel", "Jaryn",
"Kallor", "Lydar", "Marvik", "Neroth", "Orvin", "Pyran", "Ryxen", "Saren",
"Talric", "Ulrak", "Voren", "Wyler", "Xaric", "Yvran", "Zalvor", "Arven",
"Bralor", "Crethan", "Dalvek", "Elvyn", "Freth", "Gorvik", "Halen", "Jovren",
"Karven", "Leyron", "Marven", "Norlis", "Oscor", "Pervan", "Qyros", "Ralven",
"Serak", "Thorin", "Urel", "Valkan", "Wyrin", "Xerath", "Ylkor", "Zereth"
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
    "Genesis": [
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

# Multiplicative modifiers (1.0 = neutral, >1.0 = boost, <1.0 = penalty)
ALIGNMENT_MODS = {
    "Valiant": (0.9, 2.35),
    "Good": (1.10, 1.85),
    "Neutral": (0.95, 1.85),
    "Mischievous": (0.65, 2.65),
    "Evil": (0.58, 2.75),
}

DIVINITY_MODS = {
    "Divine": (0.82, 1.80),
    "Neutral": (0.83, 1.70),
    "Hellish": (0.70, 2.00),
}

ELEMENT_MODS = (0.85, 0.98)
CLASS_MODS = (0.85, 0.98)


RARITY_TIERS = [
    (0.0, "Common"),
    (0.65, "Trained"),
    (0.95, "Uncommon"),
    (1.4, "Handy"),
    (2.6, "Rare"),
    (4.0, "Pseudo"),
    (5.0, "Genesis"),
    (6.2, "Legendary"),
    (7.0, "Mythical"),
    (8.0, "Ethereal"),
    (9.2, "Ascendant"),
    (10.3, "Primordial"),
    (11.5, "Omni"),
    (12.8, "God-Challenger"),
]


# =========================
# ⚔️ CLASS TITLES
# =========================

CLASS_TIERS = [
    (0.7, "Horrible"),
    (0.85, "Okay"),
    (0.95, "Apprentice"),
    (1.02, "Journeyer"),
    (1.08, "Elite"),
    (1.13, "Chief"),
    (1.17, "Masterclass"),
    (1.2, "Transcendant"),
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
    "Ice": ("Frostwarden", "Icebound"),
    "Rain": ("Stormbearer", "Endless Drizzle"),
    "Lava": ("Volcano King", "Burnscarred"),
    "Blood": ("Bloodsworn", "Vein-Bound"),
    "Desert": ("Sandwarden", "Dustblighted"),
    "Arcane": ("Spellhallowed", "Rune-Cursed"),
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


CHECKIN_ACTIONS = [
    "Meditating in the ruins of a forgotten temple",
    "Training under a collapsing waterfall",
    "Hunting a corrupted beast in the wildlands",
    "Resting after a brutal expedition",
    "Crafting a weapon infused with elemental energy",
    "Exploring an uncharted cavern system",
    "Standing guard over a sacred relic",
    "Recovering from severe injuries",
    "Negotiating with a hostile faction",
    "Studying ancient runes carved into stone",
    "Tracking a legendary creature through the forest",
    "Clearing out a monster-infested village",
    "Charging power through storm energy",
    "Patrolling the borders of the kingdom",
    "Resting at a makeshift campfire",
    "Searching for a lost companion",
    "Conducting a ritual of purification",
    "Defending a village from raiders",
    "Mapping unknown territory",
    "Gathering rare alchemical ingredients",
    "Training combat techniques with a master",
    "Restoring a broken artifact",
    "Fighting off waves of enemies",
    "Investigating a mysterious anomaly",
    "Sealing a dimensional rift",
    "Guarding a caravan through dangerous lands",
    "Climbing a sacred mountain peak",
    "Fleeing from an overwhelming threat",
    "Preparing for an upcoming battle",
    "Recovering ancient knowledge",
    "Communing with a spirit entity",
    "Harvesting energy from a leyline",
    "Testing a newly forged weapon",
    "Breaking through enemy lines",
    "Surviving in a cursed zone",
    "Exploring a sunken ruin",
    "Clearing corruption from the land",
    "Building a fortified outpost",
    "Rescuing trapped civilians",
    "Chasing a fleeing bounty target",
    "Dueling an elite warrior",
    "Absorbing elemental essence",
    "Performing emergency healing rituals",
    "Hiding from a superior force",
    "Reinforcing magical barriers",
    "Studying celestial movements",
    "Recovering stolen artifacts",
    "Assassinating a high-value target",
    "Guarding a sacred shrine",
    "Escorting an important envoy",
    "Investigating a destroyed settlement",
    "Facing a trial of endurance",
    "Traversing a desert wasteland",
    "Crossing a frozen tundra",
    "Entering a forbidden zone",
    "Breaking a magical seal",
    "Defending against an ambush",
    "Recovering lost memories",
    "Enhancing combat abilities",
    "Taming a wild beast",
    "Repairing damaged armor",
    "Observing enemy movements",
    "Waiting for reinforcements",
    "Channeling divine energy",
    "Surviving a natural disaster",
    "Escaping a collapsing dungeon",
    "Uncovering hidden passages",
    "Defending a strategic chokepoint",
    "Collecting battlefield intelligence",
    "Purging undead from the area",
    "Searching for a mythical relic",
    "Recovering from exhaustion",
    "Studying forbidden magic",
    "Strengthening spiritual energy",
    "Training with elemental forces",
    "Investigating strange phenomena",
    "Guarding a prisoner convoy",
    "Negotiating peace between factions",
    "Surviving a monster siege",
    "Infiltrating enemy territory",
    "Sabotaging enemy supplies",
    "Escorting survivors to safety",
    "Exploring a floating ruin",
    "Crossing a shattered battlefield",
    "Rebuilding destroyed settlements",
    "Holding the frontline alone",
    "Resisting mind control influence",
    "Purifying corrupted water sources",
    "Activating ancient machinery",
    "Discovering hidden lore",
    "Chasing an escaping spirit",
    "Breaking through a magical barrier",
    "Defending against aerial threats",
    "Harvesting mana crystals",
    "Recovering from a divine trial",
    "Testing reality stability",
    "Exploring a void-touched zone",
    "Meditating to regain balance",
    "Strengthening soul resonance",
    "Fighting a shadow version of self",
    "Observing cosmic disturbances",
    "Tracking interdimensional signals",
    "Repairing dimensional fractures",
    "Protecting a sacred tree",
    "Clearing plague-infested lands",
    "Surviving an endless storm",
    "Escorting a royal procession",
    "Holding a defensive formation",
    "Conducting battlefield healing",
    "Searching for survivors",
    "Recovering stolen knowledge",
    "Challenging arena champions",
    "Entering a trial of gods",
    "Unlocking sealed powers",
    "Facing corrupted allies",
    "Escaping collapsing reality",
    "Defending against siege engines",
    "Clearing a monster nest",
    "Investigating ancient prophecy",
    "Channeling forbidden energy",
    "Resisting elemental overload",
    "Traversing volcanic terrain",
    "Crossing cursed swamplands",
    "Mapping shifting terrain",
    "Confronting a legendary beast",
    "Hunting spectral entities",
    "Guarding a dimensional anchor",
    "Studying arcane anomalies",
    "Reforging broken relics",
    "Recovering lost artifacts of power",
    "Escaping pursuit through ruins",
    "Defending a last stronghold",
    "Restoring balance to nature",
    "Absorbing ambient magic",
    "Tracking rogue magic storms",
    "Investigating void contamination",
    "Fighting through enemy stronghold",
    "Recovering from soul damage",
    "Observing time distortions",
    "Breaking enemy siege lines",
    "Strengthening defensive wards",
    "Searching for divine intervention",
    "Confronting ancient guardians",
    "Training in isolation",
    "Surviving without resources",
    "Escaping labyrinthine ruins",
    "Defending sacred grounds",
    "Chasing a world-ending threat",
    "Studying elemental convergence",
    "Repairing reality anchors",
    "Gathering storm energy",
    "Guarding a portal nexus",
    "Recovering from battle fatigue",
    "Investigating celestial ruins",
    "Destroying cursed relics",
    "Escorting wounded allies",
    "Preparing for apocalypse-level threat",
    "Traversing dimensional overlap",
    "Holding off enemy reinforcements",
    "Surviving cursed transformation",
    "Studying enemy weaknesses",
    "Rebuilding magical defenses",
    "Hunting elite commanders",
    "Breaking enemy morale",
    "Protecting a last hope artifact",
    "Crossing battle-scarred plains",
    "Recovering lost divine blessings",
    "Investigating cosmic signals",
    "Defending against shadow invasion",
    "Clearing corrupted battlefield zones",
    "Training with ancestral spirits",
    "Surviving trial of endurance",
    "Resisting void influence",
    "Observing collapsing stars",
    "Repairing broken leyline network",
    "Escaping enchanted traps",
    "Guarding sacred knowledge vault",
    "Facing judgment trial",
    "Hunting rogue entities",
    "Clearing cursed tombs",
    "Traversing unstable terrain",
    "Defending collapsing fortress",
    "Investigating ancient war sites",
    "Channeling storm essence",
    "Protecting elemental core",
    "Surviving multi-wave assault",
    "Recovering stolen essence fragments",
    "Escorting magical artifact convoy",
    "Studying forbidden ruins",
    "Holding position under siege",
    "Defeating invading force",
    "Reinforcing magical seals",
    "Surviving spiritual purge",
    "Exploring fractured world zones",
    "Tracking ancient war spirits",
    "Defending dimensional gate",
    "Investigating reality anomalies",
    "Restoring broken sanctuaries",
    "Surviving endless battlefield loop",
    "Guarding celestial beacon",
    "Searching for lost timeline fragments",
    "Battling corrupted heroes",
    "Escaping collapsing dungeon system",
    "Defending against reality collapse",
    "Preparing for god-level confrontation",
    "Holding final stand"
]

CLASSES = [
    "Warrior", "Archer", "Assassin", "Mage", "Paladin", "Rogue", "Admiral", "Sniper",
    "Outlaw", "Bard", "Scavenger", "Ritualist", "Commander", "Defender", "Barbarian"
]

EMPORIUM_SCENARIOS = [
    "The Adventures Exchange is looking for a [requirements] hero to slay the Mist Dragon lurking in the northern marshes.",
    "The Guild requests a [requirements] hero to escort a royal caravan through corrupted territory.",
    "A desperate village seeks a [requirements] hero to stop a plague spreading from the old crypts.",
    "The Crimson Market needs a [requirements] hero to retrieve a stolen relic from bandit lords.",
    "The Celestial Archive requires a [requirements] hero to recover ancient star charts from ruined observatories.",
    "The kingdom is searching for a [requirements] hero to defend the eastern wall from raiders.",
    "The Hollow Merchant seeks a [requirements] hero to explore a newly opened dimensional rift.",
    "The Spore Circle requests a [requirements] hero to purge a corrupted fungal hive.",
    "A noble family offers rewards for a [requirements] hero to hunt a rogue Beast Titan.",
    "The Iron Syndicate needs a [requirements] hero to recover lost steel shipments from lava caverns.",
    "The Moonlit Temple calls for a [requirements] hero to survive the Trial of Echoes.",
    "A wandering oracle seeks a [requirements] hero to escort her through the cursed wastelands.",
    "The Blackwater Docks require a [requirements] hero to eliminate sea horrors attacking trade ships.",
    "The Arcane Vault seeks a [requirements] hero to seal unstable magical fractures.",
    "The royal alchemists need a [requirements] hero to harvest venom from an ancient serpent.",
    "The people of Frost Hollow plead for a [requirements] hero to end an endless blizzard.",
    "A mysterious collector wants a [requirements] hero to retrieve crystal shards from the abyss.",
    "The Sunspire Order seeks a [requirements] hero to destroy a relic spreading corruption.",
    "The Adventures Exchange requests a [requirements] hero to escort sacred cargo through bandit territory.",
    "A celestial priesthood seeks a [requirements] hero to defend a fallen star from invaders.",
    "The Shadow Bazaar requires a [requirements] hero to infiltrate a forbidden fortress.",
    "The Golden Arena seeks a [requirements] hero to compete in the Trials of Champions.",
    "The villagers of Emberfall need a [requirements] hero to contain a magma eruption.",
    "A hidden resistance seeks a [requirements] hero to sabotage enemy war machines.",
    "The Stormcallers request a [requirements] hero to investigate unnatural lightning storms.",
    "The ancient druids seek a [requirements] hero to restore balance to dying forests.",
    "A grieving king requests a [requirements] hero to retrieve the soul of his fallen son.",
    "The Gravekeepers need a [requirements] hero to stop undead armies from rising.",
    "The Astral Guild seeks a [requirements] hero to recover a drifting celestial artifact.",
    "A forgotten spirit asks for a [requirements] hero to break its eternal curse.",
    "The merchants of Duskwatch require a [requirements] hero to clear monsters from trade routes.",
    "The Crystal Choir seeks a [requirements] hero to defend their sacred caverns.",
    "The Deepwater Council requests a [requirements] hero to slay a leviathan beneath the harbor.",
    "The kingdom seeks a [requirements] hero to challenge a rogue warlord in single combat.",
    "A hidden cult requires a [requirements] hero to retrieve forbidden tomes from ancient ruins.",
    "The Ember Forge seeks a [requirements] hero to reignite the Eternal Furnace.",
    "A terrified village pleads for a [requirements] hero to survive the Forest of Whispers.",
    "The Voidwatchers seek a [requirements] hero to close a breach leaking shadow creatures.",
    "The royal scouts need a [requirements] hero to map uncharted wastelands.",
    "The Temple of Dawn seeks a [requirements] hero to defeat a corrupted angel.",
    "The Spire Archivists request a [requirements] hero to uncover lost history beneath the capital.",
    "A desperate merchant seeks a [requirements] hero to retrieve cargo stolen by sky pirates.",
    "The ancient guardians seek a [requirements] hero to complete the Trial of Flame.",
    "The empire needs a [requirements] hero to hold the frontline against invading beasts.",
    "A wandering beastmaster seeks a [requirements] hero to tame a celestial wolf.",
    "The Oracle Circle requests a [requirements] hero to investigate visions of the apocalypse.",
    "The Corrupted Marsh calls for a [requirements] hero to destroy its heart core.",
    "A forgotten kingdom seeks a [requirements] hero to awaken an ancient protector.",
    "The Frostbound Clan requests a [requirements] hero to survive the Glacier Labyrinth.",
    "The citizens of Nightreach seek a [requirements] hero to hunt a shadow assassin.",
    "The Arcane Academy requires a [requirements] hero to recover unstable magical artifacts.",
    "The Eternal Library seeks a [requirements] hero to defend forbidden knowledge from thieves.",
    "The heavens request a [requirements] hero to investigate fallen celestial fragments.",
    "A hidden rebellion seeks a [requirements] hero to free prisoners from the Iron Fortress.",
    "The Bloomkeepers need a [requirements] hero to restore life to poisoned lands.",
    "The Titan Hunters request a [requirements] hero to track an ancient colossus.",
    "The Storm Monastery seeks a [requirements] hero to meditate atop the Thunder Peak.",
    "The royal family seeks a [requirements] hero to guard the prince during negotiations.",
    "The Whispering Depths call for a [requirements] hero to explore submerged ruins.",
    "A cursed knight seeks a [requirements] hero to finally grant him peace.",
    "The Void Market requests a [requirements] hero to collect essence from corrupted beasts.",
    "The Celestial Forge seeks a [requirements] hero to temper weapons with starfire.",
    "The Ashen Legion needs a [requirements] hero to reclaim lost battle standards.",
    "A mysterious traveler seeks a [requirements] hero to survive the Realm Between Worlds.",
    "The Temple of Equinox requires a [requirements] hero to restore balance between Light and Dark.",
    "The kingdom requests a [requirements] hero to investigate disappearances near the old mines.",
    "The Deep Spore Hive seeks a [requirements] hero to destroy parasitic queens.",
    "The Skywatchers require a [requirements] hero to defend floating cities from invaders.",
    "A rogue scientist seeks a [requirements] hero to test experimental artifacts.",
    "The Sapphire Court seeks a [requirements] hero to duel a traitorous noble champion.",
    "The Wraith Hunters request a [requirements] hero to survive the Valley of Souls.",
    "The Lavaforged seek a [requirements] hero to mine crystals beneath active volcanoes.",
    "The Astral Choir needs a [requirements] hero to investigate singing stars in the night sky.",
    "A forgotten dragon seeks a [requirements] hero worthy of inheriting its power.",
    "The empire calls for a [requirements] hero to stop a spreading corruption storm.",
    "The Chronokeepers seek a [requirements] hero to stabilize fractures in time itself.",
    "The Last Sanctuary requests a [requirements] hero to defend humanity’s final refuge."
]


# =========================
# 📌 BOT COMMANDS
# =========================

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    if not event_scheduler.is_running():
        event_scheduler.start()
    if not event_countdown_updater.is_running():
        event_countdown_updater.start()
    if not nemesis_hunt_scheduler.is_running():
        nemesis_hunt_scheduler.start()


@tasks.loop(minutes=1)
async def event_scheduler():
    """Send an event announcement every 12 hours and keep event state updated."""
    state = load_event_state()
    now = datetime.datetime.utcnow()
    if not state or now >= datetime.datetime.fromisoformat(state.get("next_announcement_at", now.isoformat())):
        if state:
            await mark_previous_event_ended(state)
        previous_name = state.get("name") if state else None
        new_state = choose_and_activate_event(exclude_name=previous_name)
        refresh_emporium_state()
        announcement = format_event_announcement(new_state)
        sent_messages = await send_global_announcement(announcement)
        new_state["announcement_messages"] = sent_messages
        set_current_event(new_state)


@bot.command(name="CH")
async def create_hero(ctx):
    class_rank_lines = "  ".join([f"{name}({threshold:+.2f})" for threshold, name in CLASS_TIERS])
    rarity_rank_lines = "  ".join([f"{name}({threshold:+.2f})" for threshold, name in RARITY_TIERS])
    msg = f"""
**Hero Creation Guide**
Use: `CH_Alignment_Divinity_Race_Element_Class`

*Choices*
Alignment: Valiant, Good, Neutral, Mischievous, Evil
Divinity: Divine, Neutral, Hellish

Race: Human / Construct / Elven / Goblin / Beast / Ogre / Deep-Crawler / Celestial / Angel / Demon / Dwarf / Elemental / Undead / Magma-Crawler
*Race is flavor only.*

Elements: Fire, Water, Earth, Air, Steel, Glass, Light, Dark, Equinox, Celestial, Beast, Lightning, Magma, Spore, Crystal, Color, Plants, Poison, Corruption, Mist, Death, Life, Ice, Rain, Lava, Blood, Desert, Arcane

Classes: Warrior, Archer, Assassin, Mage, Paladin, Rogue, Admiral, Sniper, Outlaw, Bard, Scavenger, Ritualist, Commander, Defender, Barbarian

Class ranks: {class_rank_lines}

Overall rarity ranks: {rarity_rank_lines}

Every 10th roll is Lucky. 5% chance for Shiny.

"""
    await ctx.send(msg)

@bot.command(name="ViewHeroesGodPool")
async def heroes_god_pool(ctx, page: int = 1):
    """Display paginated heroes in a user's collection (name, rarity, and ID only)"""
    user_heroes = get_user_heroes(ctx.author.id)
    
    if not user_heroes:
        await ctx.send(f"**HERO COLLECTION — {ctx.author.name}**\n\nYou currently have **0 heroes** in your collection. Create one with `CH_Alignment_Divinity_Race_Element_Class`!")
        return
    
    per_page = 8
    total_heroes = len(user_heroes)
    max_page = max(1, (total_heroes + per_page - 1) // per_page)
    if page < 1:
        page = 1
    if page > max_page:
        page = max_page

    start = (page - 1) * per_page
    end = start + per_page
    current_page_heroes = user_heroes[start:end]

    message = (
        f"**HERO COLLECTION — {ctx.author.name}**\n\n"
        f"You currently have **{total_heroes}** heroes in your collection.\n"
        f"Showing page **{page}/{max_page}** (8 heroes per page):\n\n---\n\n"
    )
    
    for hero in current_page_heroes:
        icons = ""
        if hero.get('shiny', False):
            icons += " ✨"
        if hero.get('favorite', False):
            icons += " ❤️"
        message += f"**#{hero['id']}** | {hero['full_name']}{icons} | ⭐ {hero['rarity']}\n"
    
    message += (
        f"\n---\n"
        f"Use `!ViewHero <number>` to see a hero's full details.\n"
        f"To change pages, use `!ViewHeroesGodPool <page #>`.\n"
        f"✨ Shiny   ❤️ Favorite"
    )

    await ctx.send(message)


@bot.command(name="GodPoolCmds")
async def godpool_cmds(ctx):
    """Display every GodPool command and what it does."""
    help_text = (
        "**GodPool Command List**\n\n"
        "`!CH` — Create a new hero using `CH_Alignment_Divinity_Race_Element_Class`.\n"
        "`!ViewHeroesGodPool <page #>` — List your heroes with ID, name, and rarity, 8 per page.\n"
        "`!ViewHero <id>` — Show full details for one hero.\n"
        "`!DeleteAllHeroesGodPool` — Delete all your heroes except those preserved.\n"
        "`!PreserveHero <id>` — Toggle preservation so a hero is not deleted by `!DeleteAllHeroesGodPool`.\n"
        "`!FavHero <id>` — Mark a hero as your favorite.\n"
        "`!NameHero <id> <nickname>` — Rename a hero while preserving its displayed rarity.\n"
        "`!HeroCheckIn <id>` — Check in on what a hero is currently doing.\n"
        "`!Dishero <id>` — Delete a specific hero from your collection.\n"
        "`!AE` — View the current Adventures Exchange requirement and reward.\n"
        "`!TradeHeroGodPool <id>` — Trade a hero to the Adventures Exchange for a reward.\n"
        "`!CheckInvGP` — View your current Adventures Exchange inventory items.\n"
        "`!ConsumeGP <itemid> [hero_id]` — Consume a reward item to boost your next hero roll, or evolve a hero's title with Evolution Stone.\n"
        "`!RAGodPool <Easy|Normal|Challenging>` — Start a random encounter and receive an encounter ID.\n"
        "`!FaceRA <Encounter ID> <Hero ID>` — Attempt the active random encounter with a hero.\n"
        "`!SearchHeroGP <Encounter ID>` — Find which of your heroes can face the active encounter.\n"
        "`!CancelRA <Encounter ID>` — Cancel your active random encounter.\n"
        "`!SpareGP` — Spare a potential Nemesis after a Nemesis encounter.\n"
        "`!KillGP` — Slay a potential Nemesis or finish a defeated Nemesis.\n"
        "`!NemisisGP` — View your current active Nemesis status.\n"
        "`!HideGP` — Hide from a Nemesis hunt and gain a temporary hero-making debuff.\n"
        "`!ConfrontGP` — Confront a Nemesis hunt with a longer Strike/Shield game.\n"
        "`!RecruitGP` — Recruit a defeated Nemesis into your hero collection.\n"
        "`!HeroSpeakGD <Hero ID> <message>` — Have a hero say a custom message.\n"
        "`!GodPoolCmds` — Show this command list.\n"
    )
    await ctx.send(help_text)


@bot.command(name="RAGodPool")
async def random_encounter(ctx, difficulty: str):
    global FORCED_ENCOUNTER_TYPE
    difficulty_clean = difficulty.capitalize()
    if difficulty_clean not in DIFFICULTY_POOLS:
        await ctx.send("Invalid difficulty. Choose one of: Easy, Normal, Challenging.")
        return

    state = load_ra_encounter_state()
    active = state.get("active", {})
    user_id_str = str(ctx.author.id)
    if user_id_str in active:
        encounter = active[user_id_str]
        await ctx.send(
            f"You already have an active random encounter. Finish it with `!FaceRA {encounter['id']} <Hero ID>` before starting a new one."
        )
        return

    enemy = choose_ra_enemy(difficulty_clean)
    requirements = choose_ra_requirements()
    required_rarity = choose_ra_required_rarity(difficulty_clean)
    nemesis = get_user_nemesis(ctx.author.id)
    encounter_id = get_next_ra_encounter_id(state)

    encounter = {
        "id": encounter_id,
        "difficulty": difficulty_clean,
        "enemy": enemy,
        "requirements": requirements,
        "required_rarity": required_rarity,
        "created_at": datetime.datetime.utcnow().isoformat(),
    }

    # Check for forced encounter type
    forced_type = FORCED_ENCOUNTER_TYPE
    FORCED_ENCOUNTER_TYPE = None  # Reset after use

    if forced_type == "N":
        # Force Nemesis encounter
        if nemesis:
            if random.random() < 0.5:
                encounter["special_type"] = "nemesis_challenge"
                encounter["title"] = f"A whisper in the dark: {nemesis['hero_name']} tests your instincts."
                encounter["requirements"] = []
                encounter["required_rarity"] = "Common"
                encounter["challenge"] = {
                    "prompt": "Strike or Shield?",
                    "remaining_guesses": 3,
                    "correct_needed": 1,
                    "correct_guesses": 0,
                    "attempts": 0,
                    "pending": True,
                    "last_feedback": None,
                }
            else:
                minion_rarity = random.choice(NEMESIS_MINION_REQUIREMENTS)
                encounter["special_type"] = "nemesis_minion"
                encounter["title"] = f"A dark minion of {nemesis['hero_name']} blocks your way."
                encounter["requirements"] = []
                encounter["required_rarity"] = minion_rarity
        else:
            encounter["special_type"] = "potential_nemesis"
            nemesis_hero = generate_nemesis_hero()
            encounter["nemesis_hero"] = nemesis_hero
            encounter["title"] = f"A Potential Nemesis emerges: {nemesis_hero['full_name']}"
            encounter["requirements"] = []
            encounter["required_rarity"] = "Common"
    elif forced_type == "SO":
        # Force Sought Out encounter
        user_heroes = load_user_heroes().get(user_id_str, [])
        if user_heroes:
            sought_hero = random.choice(user_heroes)
            sought_person = random.choice(FIRST_NAMES)
            encounter["sought_out"] = True
            encounter["sought_out_person"] = sought_person
            encounter["target_hero_id"] = sought_hero.get("id")
            encounter["target_hero_name"] = sought_hero.get("hero_name", sought_hero.get("full_name", "Unknown"))
            encounter["requirements"] = []
            encounter["required_rarity"] = "Common"
            encounter["title"] = f"{sought_person} sought out {encounter['target_hero_name']} to face {enemy}"
        else:
            encounter["title"] = get_ra_requirement_title(requirements, enemy)
    elif forced_type == "R":
        # Force Regular encounter
        encounter["title"] = get_ra_requirement_title(requirements, enemy)
    else:
        # Normal random logic
        if nemesis and random.random() < NEMESIS_ACTIVE_ENCOUNTER_CHANCE:
            if random.random() < 0.5:
                encounter["special_type"] = "nemesis_challenge"
                encounter["title"] = f"A whisper in the dark: {nemesis['hero_name']} tests your instincts."
                encounter["requirements"] = []
                encounter["required_rarity"] = "Common"
                encounter["challenge"] = {
                    "prompt": "Strike or Shield?",
                    "remaining_guesses": 3,
                    "correct_needed": 1,
                    "correct_guesses": 0,
                    "attempts": 0,
                    "pending": True,
                    "last_feedback": None,
                }
            else:
                minion_rarity = random.choice(NEMESIS_MINION_REQUIREMENTS)
                encounter["special_type"] = "nemesis_minion"
                encounter["title"] = f"A dark minion of {nemesis['hero_name']} blocks your way."
                encounter["requirements"] = []
                encounter["required_rarity"] = minion_rarity
        elif not nemesis and random.random() < NEMESIS_POTENTIAL_ENCOUNTER_CHANCE:
            encounter["special_type"] = "potential_nemesis"
            nemesis_hero = generate_nemesis_hero()
            encounter["nemesis_hero"] = nemesis_hero
            encounter["title"] = f"A Potential Nemesis emerges: {nemesis_hero['full_name']}"
            encounter["requirements"] = []
            encounter["required_rarity"] = "Common"
        elif random.random() < 0.10:
            user_heroes = load_user_heroes().get(user_id_str, [])
            if user_heroes:
                sought_hero = random.choice(user_heroes)
                sought_person = random.choice(FIRST_NAMES)
                encounter["sought_out"] = True
                encounter["sought_out_person"] = sought_person
                encounter["target_hero_id"] = sought_hero.get("id")
                encounter["target_hero_name"] = sought_hero.get("hero_name", sought_hero.get("full_name", "Unknown"))
                encounter["requirements"] = []
                encounter["required_rarity"] = "Common"
                encounter["title"] = f"{sought_person} sought out {encounter['target_hero_name']} to face {enemy}"
            else:
                encounter["title"] = get_ra_requirement_title(requirements, enemy)
        else:
            encounter["title"] = get_ra_requirement_title(requirements, enemy)

    active[user_id_str] = encounter
    state["active"] = active
    save_ra_encounter_state(state)

    await ctx.send(embed=build_ra_encounter_embed(encounter))


@bot.command(name="FaceRA")
async def face_ra(ctx, encounter_id: int, hero_id: int):
    state = load_ra_encounter_state()
    active = state.get("active", {})
    encounter = active.get(str(ctx.author.id))
    if not encounter or encounter.get("id") != encounter_id:
        await ctx.send(
            "No active random encounter with that ID was found for you. Start one with `!RAGodPool <Easy|Normal|Challenging>`."
        )
        return

    heroes = load_user_heroes()
    user_heroes = heroes.get(str(ctx.author.id), [])
    hero = next((h for h in user_heroes if h.get("id") == hero_id), None)
    if not hero:
        await ctx.send(f"No hero with ID **{hero_id}** found in your collection.")
        return

    match, reason = hero_matches_ra_requirements(hero, encounter)
    if not match:
        remove_user_ra_encounter(state, ctx.author.id)
        await ctx.send(
            f"Your hero **#{hero_id}** `{hero.get('full_name', 'Unknown')}` failed the encounter **{encounter['title']}**. {reason}"
        )
        return

    if encounter.get("special_type") == "potential_nemesis":
        if encounter.get("pending_choice"):
            await ctx.send("The Potential Nemesis is already waiting. Use `!SpareGP` to spare it or `!KillGP` to slay it.")
            return

        encounter["pending_choice"] = True
        encounter["facing_hero_id"] = hero_id
        active[str(ctx.author.id)] = encounter
        state["active"] = active
        save_ra_encounter_state(state)

        nemesis_hero = encounter.get("nemesis_hero", {})
        embed = discord.Embed(title="🔥 Potential Nemesis Encounter", color=0xff5500)
        embed.add_field(name="Your Hero", value=f"#{hero_id} {hero.get('full_name', 'Unknown')}", inline=False)
        embed.add_field(name="Potential Nemesis", value=nemesis_hero.get("full_name", "Unknown"), inline=False)
        embed.add_field(name="Choice", value="Spare the Nemesis with `!SpareGP` or kill it with `!KillGP`.", inline=False)
        await ctx.send(embed=embed)
        return

    if encounter.get("special_type") == "nemesis_challenge":
        challenge = encounter.get("challenge", {})
        if challenge.get("pending"):
            if challenge.get("attempts", 0) > 0:
                await ctx.send("The Nemesis challenge is already underway. Answer with `Strike` or `Shield`.")
                return

            challenge["hero_id"] = hero_id
            challenge["pending"] = True
            encounter["challenge"] = challenge
            active[str(ctx.author.id)] = encounter
            state["active"] = active
            save_ra_encounter_state(state)

            nemesis = get_user_nemesis(ctx.author.id)
            nemesis_name = nemesis.get("full_name", "The Nemesis") if nemesis else "The Nemesis"
            embed = discord.Embed(title="🔮 Nemesis Duel Begins", color=0x9933ff)
            embed.add_field(name="Your Hero", value=f"#{hero_id} {hero.get('full_name', 'Unknown')}", inline=False)
            embed.add_field(name="Nemesis", value=nemesis_name, inline=False)
            embed.add_field(name="Prompt", value=challenge.get("prompt", "Strike or Shield?"), inline=False)
            embed.add_field(name="Guesses Remaining", value=str(challenge.get("remaining_guesses", 3)), inline=False)
            embed.set_footer(text="Reply with Strike or Shield to resolve the challenge.")
            await ctx.send(embed=embed)
            return

    reward_item = try_grant_ra_reward(ctx.author.id, encounter["difficulty"])
    upgrade_amount = get_ra_upgrade_chance(hero.get("rarity", "Common"), encounter.get("required_rarity", "Common"), encounter["difficulty"])
    upgrade_type = random.choice(["class", "rarity"])
    upgraded = False
    bonus_text = "No bonus rank increase occurred this time. Better luck on the next encounter."

    if random.random() < upgrade_amount:
        if upgrade_type == "class":
            upgraded = increase_hero_class_title(hero)
            if upgraded:
                bonus_text = f"Your hero's class title has improved to **{hero['class_title']}**!"
        else:
            upgraded = increase_hero_rarity(hero)
            if upgraded:
                bonus_text = f"Your hero's rarity has improved to **{hero['rarity']}**!"

    if encounter.get("special_type") == "nemesis_minion":
        nemesis_data = add_nemesis_victory(ctx.author.id)
        if nemesis_data and nemesis_data.get("pending_finish"):
            bonus_text += "\nThe Nemesis is weakened. Use `!KillGP` or `!RecruitGP` to finish them."

    heroes[str(ctx.author.id)] = user_heroes
    save_user_heroes(heroes)

    if encounter.get("special_type") != "nemesis_challenge":
        remove_user_ra_encounter(state, ctx.author.id)

    embed = discord.Embed(title="✅ Random Encounter Victory", color=0x00ffcc)
    embed.add_field(name="Hero", value=f"#{hero_id} {hero.get('full_name', 'Unknown')}", inline=False)
    embed.add_field(name="Encounter", value=encounter["title"], inline=False)
    embed.add_field(name="Difficulty", value=encounter["difficulty"], inline=True)
    embed.add_field(name="Result", value="Defeated", inline=True)
    embed.add_field(name="Bonus", value=bonus_text, inline=False)
    if reward_item:
        embed.add_field(name="Reward", value=f"{reward_item['name']} — {reward_item['description']}", inline=False)
        embed.set_footer(text="The reward has been added to your inventory. Use !CheckInvGP to view it.")
    else:
        embed.set_footer(text="No item reward dropped this time. Try another encounter.")

    await ctx.send(embed=embed)


@bot.command(name="SearchHeroGP")
async def search_hero_gp(ctx, encounter_id: int):
    state = load_ra_encounter_state()
    active = state.get("active", {})
    encounter = active.get(str(ctx.author.id))
    if not encounter or encounter.get("id") != encounter_id:
        await ctx.send("No active random encounter with that ID was found for you.")
        return

    user_heroes = get_user_heroes(ctx.author.id)
    matching_heroes = []
    for hero in user_heroes:
        match, _ = hero_matches_ra_requirements(hero, encounter)
        if match:
            matching_heroes.append(hero)

    if not matching_heroes:
        await ctx.send(
            f"No heroes in your collection currently match the requirements for encounter **{encounter['title']}**."
        )
        return

    embed = discord.Embed(title="🔎 Encounter Search Results", color=0x00ffcc)
    embed.add_field(name="Encounter", value=encounter["title"], inline=False)
    embed.add_field(name="Difficulty", value=encounter["difficulty"], inline=True)
    embed.add_field(name="Requirements", value=format_ra_requirements(encounter.get("requirements", []), encounter), inline=False)

    hero_lines = [f"**#{hero['id']}** {hero.get('full_name', 'Unknown')}" for hero in matching_heroes[:10]]
    if len(matching_heroes) > 10:
        hero_lines.append(f"...and {len(matching_heroes) - 10} more heroes.")

    embed.add_field(name="Matching Heroes", value="\n".join(hero_lines), inline=False)
    await ctx.send(embed=embed)


@bot.command(name="CancelRA")
async def cancel_ra(ctx, encounter_id: int):
    state = load_ra_encounter_state()
    active = state.get("active", {})
    encounter = active.get(str(ctx.author.id))
    if not encounter or encounter.get("id") != encounter_id:
        await ctx.send("No active random encounter with that ID was found for you.")
        return

    del active[str(ctx.author.id)]
    state["active"] = active
    save_ra_encounter_state(state)

    embed = discord.Embed(title="❌ Random Encounter Cancelled", color=0xff6666)
    embed.add_field(name="Encounter ID", value=str(encounter_id), inline=True)
    embed.add_field(name="Title", value=encounter["title"], inline=False)
    embed.set_footer(text="You may start a new random encounter with !RAGodPool.")
    await ctx.send(embed=embed)


@bot.command(name="SpareGP")
async def spare_gp(ctx):
    state = load_ra_encounter_state()
    encounter = state.get("active", {}).get(str(ctx.author.id))
    if not encounter or encounter.get("special_type") != "potential_nemesis":
        await ctx.send("No potential Nemesis encounter is waiting for you to spare.")
        return
    if has_active_nemesis(ctx.author.id):
        await ctx.send("You already have an active Nemesis. Finish your current Nemesis before sparing another.")
        return

    nemesis_hero = encounter.get("nemesis_hero", {})
    faced_hero = None
    if encounter.get("facing_hero_id"):
        faced_hero = next((h for h in get_user_heroes(ctx.author.id) if h.get("id") == encounter.get("facing_hero_id")), None)
    started_at = datetime.datetime.utcnow().isoformat()
    nemesis_data = {
        "hero": nemesis_hero,
        "spawned_by_hero_id": encounter.get("facing_hero_id"),
        "spawned_by_hero_name": faced_hero.get("hero_name", faced_hero.get("full_name", "Your hero")) if faced_hero else "Your hero",
        "victories": 0,
        "defeated": False,
        "pending_finish": False,
        "started_at": started_at,
        "next_hunt_at": (datetime.datetime.utcnow() + datetime.timedelta(hours=NEMESIS_HUNT_INTERVAL_HOURS)).isoformat(),
        "hide_debuff": None,
        "pending_hunt": None,
    }
    set_user_nemesis(ctx.author.id, nemesis_data)
    remove_user_ra_encounter(state, ctx.author.id)

    embed = discord.Embed(title="🛡️ Nemesis Spared", color=0x8b0000)
    embed.add_field(name="Your Choice", value="You spared the foe and it now stalks your path.", inline=False)
    embed.add_field(name="Nemesis", value=nemesis_hero.get("full_name", "Unknown"), inline=False)
    embed.add_field(name="Fate", value="The Nemesis has been spared. New Nemesis encounters may appear in future adventures.", inline=False)
    await ctx.send(embed=embed)


@bot.command(name="KillGP")
async def kill_gp(ctx):
    state = load_ra_encounter_state()
    encounter = state.get("active", {}).get(str(ctx.author.id))
    if encounter and encounter.get("special_type") == "potential_nemesis" and encounter.get("pending_choice"):
        item = random.choice(get_reward_items_for_rank(encounter["nemesis_hero"].get("rarity", "Common")))
        add_item_to_user(ctx.author.id, {
            "name": item["name"],
            "type": item["type"],
            "description": item["description"],
            "multiplier": item.get("multiplier", 1.0),
            "created_at": datetime.datetime.utcnow().isoformat(),
        })
        remove_user_ra_encounter(state, ctx.author.id)
        await ctx.send(f"You struck down the potential Nemesis and claimed **{item['name']}** as your guaranteed reward.")
        return

    nemesis = get_user_nemesis(ctx.author.id)
    if not nemesis or not nemesis.get("pending_finish"):
        await ctx.send("You have no defeated Nemesis waiting to be finished.")
        return

    hero = nemesis.get("hero", {})
    hero["rarity"] = increase_rarity_by_steps(hero.get("rarity", "Common"), 1)
    hero["full_name"] = build_hero_full_name(hero)
    remove_user_nemesis(ctx.author.id)

    await ctx.send(
        f"You finished the Nemesis in a final strike. Its rarity has risen to **{hero['rarity']}** and the threat is gone forever."
    )


@bot.command(name="RecruitGP")
async def recruit_gp(ctx):
    nemesis = get_user_nemesis(ctx.author.id)
    if not nemesis or not nemesis.get("pending_finish"):
        await ctx.send("You have no defeated Nemesis available for recruitment.")
        return

    hero = nemesis.get("hero", {})
    hero["rarity"] = increase_rarity_by_steps(hero.get("rarity", "Common"), 3)
    hero["full_name"] = build_hero_full_name(hero)
    hero["is_nemesis"] = True
    hero["nemesis_recruited_at"] = datetime.datetime.utcnow().isoformat()
    hero["nemesis_note"] = "Recruited from a defeated Nemesis."
    add_hero_to_user(ctx.author.id, hero)
    remove_user_nemesis(ctx.author.id)

    await ctx.send(
        f"The Nemesis has been recruited into your collection as a hero of rarity **{hero['rarity']}**. It now carries the mark of its dark origin."
    )


@bot.command(name="NemisisGP")
async def nemesis_gp(ctx):
    nemesis = get_user_nemesis(ctx.author.id)
    if not nemesis:
        await ctx.send("You do not currently have an active Nemesis.")
        return

    embed = discord.Embed(title="🕯️ Nemesis Status", color=0x551a8b)
    hero = nemesis.get("hero", {})
    embed.add_field(name="Nemesis", value=hero.get("full_name", "Unknown"), inline=False)
    embed.add_field(name="Victories", value=f"{nemesis.get('victories', 0)} / {NEMESIS_REQUIRED_VICTORIES}", inline=True)
    embed.add_field(name="Started", value=nemesis.get("started_at", "Unknown"), inline=True)
    next_hunt = nemesis.get("next_hunt_at")
    if next_hunt:
        embed.add_field(name="Next Hunt", value=next_hunt, inline=False)
    if nemesis.get("reload_reason"):
        embed.add_field(name="Notes", value=nemesis.get("reload_reason"), inline=False)
    if nemesis.get("pending_hunt"):
        hunt = nemesis["pending_hunt"]
        if hunt.get("status") == "waiting_choice":
            embed.add_field(name="Hunt", value="A Nemesis hunt is active. Use `!HideGP` or `!ConfrontGP`.", inline=False)
        elif hunt.get("status") == "guessing":
            embed.add_field(name="Hunt", value=f"Hunt in progress — {hunt.get('successes', 0)} / {hunt.get('required_successes', 3)} successes.", inline=False)
    if nemesis.get("hide_debuff"):
        embed.add_field(name="Debuff", value="A Nemesis curse weakens your next hero roll.", inline=False)

    await ctx.send(embed=embed)


@bot.command(name="HideGP")
async def hide_gp(ctx):
    nemesis = get_user_nemesis(ctx.author.id)
    if not nemesis or not nemesis.get("pending_hunt") or nemesis["pending_hunt"].get("status") != "waiting_choice":
        await ctx.send("There is no active Nemesis hunt to hide from.")
        return

    nemesis["hide_debuff"] = {
        "expires_at": (datetime.datetime.utcnow() + datetime.timedelta(minutes=30)).isoformat(),
        "rarity_penalty": 0.96,
        "class_penalty": 0.96,
        "description": "Nemesis' shadow unsettles your next hero creation.",
    }
    nemesis.pop("pending_hunt", None)
    set_user_nemesis(ctx.author.id, nemesis)

    await ctx.send(
        "You vanish into the shadows. The Nemesis still hunts you, but your hero-making is weakened for 30 minutes."
    )


@bot.command(name="ConfrontGP")
async def confront_gp(ctx):
    nemesis = get_user_nemesis(ctx.author.id)
    if not nemesis or not nemesis.get("pending_hunt") or nemesis["pending_hunt"].get("status") != "waiting_choice":
        await ctx.send("There is no active Nemesis hunt to confront.")
        return

    hunt = nemesis["pending_hunt"]
    hunt["status"] = "guessing"
    hunt["attempts"] = 0
    hunt["successes"] = 0
    hunt["required_successes"] = 3
    hunt["max_attempts"] = 7
    hunt["started_at"] = datetime.datetime.utcnow().isoformat()
    set_user_nemesis(ctx.author.id, nemesis)

    await ctx.send(
        "You choose to confront the Nemesis. Guess its moves 3 times before 7 attempts are up. Reply with Strike or Shield."
    )


@bot.command(name="HeroSpeakGD")
async def hero_speak_gd(ctx, hero_id: int, *, text: str):
    user_heroes = get_user_heroes(ctx.author.id)
    hero = next((h for h in user_heroes if h.get("id") == hero_id), None)
    if not hero:
        await ctx.send(f"No hero with ID **{hero_id}** found in your collection.")
        return

    hero_name = hero.get("hero_name", hero.get("full_name", "Unknown"))
    class_title = hero.get("class_title", "Unknown")
    message_text = f"{hero_name}-({class_title}) Says: {text}"

    embed = discord.Embed(title="💬 Hero Speech", description=message_text, color=0x00ffcc)
    embed.add_field(name="Hero", value=f"#{hero_id} {hero.get('full_name', 'Unknown')}", inline=False)
    await ctx.send(embed=embed)
    await ctx.message.delete()


def get_emporium_trade_message(state, user_id):
    return (
        f"**THE ADVENTURES EXCHANGE**\n\n"
        f"{state['flavor_text']}\n"
        f"Trade payment: **{state['reward_item']['name']}**.\n"
        f"Requirement: **{state['requirement_text']}**.\n"
        f"This Adventures Exchange refresh allows **{state['trade_limit_per_user']}** trades per user.\n"
        f"Use `!TradeHeroGodPool <id>` to trade a specified hero to the Adventures Exchange."
    )


def hero_matches_emporium(hero, state):
    if not rarity_meets_requirement(hero.get("rarity", ""), state.get("target_rarity", "")):
        return False, f"That hero must be at least **{state['target_rarity']}** rarity."

    if state.get("target_category") == "class":
        if hero.get("class") != state.get("target_item"):
            return False, f"That hero must be the **{state['target_item']}** class."
    else:
        hero_element = hero.get("element_raw", hero.get("element", ""))
        if hero_element != state.get("target_item"):
            return False, f"That hero must be the **{state['target_item']}** element."

    return True, None


@bot.command(name="AE")
async def show_emporium(ctx):
    state = get_emporium_state()
    await ctx.send(get_emporium_trade_message(state, ctx.author.id))


@bot.command(name="TradeHeroGodPool")
async def trade_hero_god_pool(ctx, hero_id: int):
    heroes = load_user_heroes()
    user_id_str = str(ctx.author.id)
    user_heroes = heroes.get(user_id_str, [])

    hero = next((h for h in user_heroes if h.get("id") == hero_id), None)
    if not hero:
        await ctx.send(f"No hero with ID **{hero_id}** found in your collection.")
        return

    state = get_emporium_state()
    user_trades = state.get("trade_counts", {}).get(user_id_str, 0)
    if user_trades >= state.get("trade_limit_per_user", 2):
        await ctx.send("You have already used the Adventures Exchange twice during this refresh. Wait for the next Adventures Exchange refresh.")
        return

    matches, reason = hero_matches_emporium(hero, state)
    if not matches:
        await ctx.send(f"That hero does not match the Adventures Exchange requirement: {reason}")
        return

    reward_item = state["reward_item"]
    item_data = {
        "name": reward_item["name"],
        "type": reward_item["type"],
        "description": reward_item["description"],
        "multiplier": reward_item["multiplier"],
        "created_at": datetime.datetime.utcnow().isoformat(),
    }

    heroes[user_id_str] = [h for h in user_heroes if h.get("id") != hero_id]
    save_user_heroes(heroes)
    add_item_to_user(ctx.author.id, item_data)

    state["trade_counts"][user_id_str] = user_trades + 1
    save_emporium_state(state)

    await ctx.send(
        f"You traded **#{hero_id}** `{hero['full_name']}` to the Adventures Exchange and received **{reward_item['name']}**!\n"
        f"Use `!CheckInvGP` to view your inventory and `!ConsumeGP <itemid>` to activate the item on your next hero roll.\n"
        f"Trades this refresh: **{state['trade_counts'][user_id_str]}/{state['trade_limit_per_user']}**."
    )


@bot.command(name="CheckInvGP")
async def check_inv_gp(ctx):
    user_items = get_user_items(ctx.author.id)
    if not user_items:
        await ctx.send("Your Adventures Exchange inventory is empty. Trade a hero with `!TradeHeroGodPool <id>` to receive a reward item.")
        return

    lines = [f"**ADVENTURES EXCHANGE INVENTORY — {ctx.author.name}**\n\nYou have **{len(user_items)}** item(s):\n"]
    for item in user_items:
        lines.append(
            f"**#{item['id']}** | {item['name']} — {item['description']}\n"
        )

    active_boost = load_user_boosts().get(str(ctx.author.id))
    if active_boost:
        lines.append(f"\n**Active boost ready:** {active_boost.get('name')} (will apply to your next `CH_` roll).\n")

    await ctx.send("\n".join(lines))


@bot.command(name="ConsumeGP")
async def consume_gp(ctx, item_id: int, hero_id: int = None):
    user_id_str = str(ctx.author.id)
    items = get_user_items(ctx.author.id)
    item = next((it for it in items if it.get("id") == item_id), None)
    if not item:
        await ctx.send(f"No item with ID **{item_id}** was found in your Adventures Exchange inventory.")
        return

    if item["type"] == "evolution":
        if hero_id is None:
            await ctx.send(f"To consume **{item['name']}**, you must specify a hero ID: `!ConsumeGP {item_id} <hero_id>`")
            return
        
        heroes = load_user_heroes()
        user_heroes = heroes.get(user_id_str, [])
        hero = next((h for h in user_heroes if h.get("id") == hero_id), None)
        if not hero:
            await ctx.send(f"No hero with ID **{hero_id}** found in your collection.")
            return
        
        # Check if hero is Pseudo+ rarity
        if not hero.get("rarity", "").startswith("Pseudo"):
            await ctx.send(f"The Evolution Stone can only be used on Pseudo+ rarity heroes. **#{hero_id}** `{hero['full_name']}` is {hero.get('rarity', 'Unknown')} rarity.")
            return
        
        element = hero.get("element", "")
        class_name = hero.get("class", "")
        
        if element not in EVOLUTION_TITLES or class_name not in EVOLUTION_TITLES[element]:
            await ctx.send(f"No evolution title available for {element} {class_name} heroes.")
            return
        
        new_title = EVOLUTION_TITLES[element][class_name]
        old_title = hero.get("class_title", class_name)
        
        # Update hero's class_title
        hero["class_title"] = new_title
        hero["full_name"] = build_hero_full_name(hero)
        
        save_user_heroes(heroes)
        remove_item_from_user(ctx.author.id, item_id)
        
        await ctx.send(
            f"You used **{item['name']}** on **#{hero_id}** `{hero['full_name']}`!\n"
            f"Title evolved from **{old_title}** to **{new_title}**."
        )
        return

    # Original logic for other item types
    active_boost = load_user_boosts().get(user_id_str)
    if active_boost:
        await ctx.send("You already have an active Adventures Exchange boost waiting for your next hero roll. Use it before consuming another item.")
        return

    removed_item = remove_item_from_user(ctx.author.id, item_id)
    if not removed_item:
        await ctx.send(f"Unable to consume item **{item_id}**. Please try again.")
        return

    set_user_boost(ctx.author.id, {
        "name": removed_item["name"],
        "type": removed_item["type"],
        "multiplier": removed_item.get("multiplier", 1.0),
        "description": removed_item["description"],
        "activated_at": datetime.datetime.utcnow().isoformat(),
    })

    await ctx.send(
        f"You consumed **{removed_item['name']}**. It will apply to your next hero roll created with `CH_`."
    )


@bot.command(name="ViewHero")
async def view_hero(ctx, hero_id: int):
    """View full details of a specific hero"""
    user_heroes = get_user_heroes(ctx.author.id)
    
    hero = None
    for h in user_heroes:
        if h.get("id") == hero_id:
            hero = h
            break
    
    if not hero:
        await ctx.send(f"No hero with ID **{hero_id}** found in your collection.")
        return
    
    message = f"**HERO DETAILS — #{hero_id}**\n\n"
    message += f"**Name:** {hero['full_name']}\n"
    message += f"**Rarity:** {hero['rarity']}\n"
    message += f"**Rarity Class:** {hero.get('class_title', 'Unknown')}\n"
    message += f"**Class:** {hero['class']}\n"
    message += f"**Divinity:** {hero['divinity']}\n"
    message += f"**Alignment:** {hero['alignment']}\n"
    message += f"**Race:** {hero['race']}\n"
    message += f"**Element:** {hero.get('element_raw', hero.get('element', 'Unknown'))} ({hero.get('element', 'Unknown')})\n"
    message += f"**Feat:** {hero['feat']}\n"
    message += f"**Rolled At:** {hero.get('created_at', 'Unknown')}\n"
    if hero.get('shiny', False):
        message += f"\n**This hero is SHINY!**\n"
    if hero.get('favorite', False):
        message += f"\n**This hero is your FAVORITE! ❤️**\n"
    
    await ctx.send(message)


@bot.command(name="DeleteAllHeroesGodPool")
async def delete_all_heroes_god_pool(ctx):
    """Delete every hero in the calling user's collection (except preserved ones)."""
    heroes = load_user_heroes()
    user_id_str = str(ctx.author.id)

    if not heroes.get(user_id_str):
        await ctx.send("You do not have any heroes to delete.")
        return

    # Remove only non-preserved heroes
    user_heroes = heroes[user_id_str]
    preserved_heroes = [h for h in user_heroes if h.get('preserved', False)]
    deleted_count = len(user_heroes) - len(preserved_heroes)
    
    heroes[user_id_str] = preserved_heroes
    save_user_heroes(heroes)
    
    if deleted_count == 0:
        await ctx.send("All your heroes are preserved! Use `!PreserveHero <id>` to unpreserve them first.")
    else:
        msg = f"**{deleted_count}** hero(es) from **{ctx.author.name}**'s collection have been deleted."
        if len(preserved_heroes) > 0:
            msg += f" **{len(preserved_heroes)}** hero(es) were preserved and remain in your collection."
        await ctx.send(msg)


@bot.command(name="PreserveHero")
async def preserve_hero(ctx, hero_id: int):
    """Preserve a hero to prevent it from being deleted by !DeleteAllHeroesGodPool"""
    heroes = load_user_heroes()
    user_id_str = str(ctx.author.id)
    user_heroes = heroes.get(user_id_str, [])

    if not user_heroes:
        await ctx.send("You do not have any heroes in your collection.")
        return

    hero = None
    for h in user_heroes:
        if h.get("id") == hero_id:
            hero = h
            break

    if not hero:
        await ctx.send(f"No hero with ID **{hero_id}** found in your collection.")
        return

    is_preserved = hero.get('preserved', False)
    hero['preserved'] = not is_preserved
    save_user_heroes(heroes)

    if hero['preserved']:
        await ctx.send(f"Hero **#{hero_id}** `{hero['full_name']}` is now **PRESERVED** and will not be deleted by `!DeleteAllHeroesGodPool`.")
    else:
        await ctx.send(f"Hero **#{hero_id}** `{hero['full_name']}` is no longer preserved.")


@bot.command(name="FavHero")
async def fav_hero(ctx, hero_id: int):
    """Mark a hero as the user's favorite."""
    heroes = load_user_heroes()
    user_id_str = str(ctx.author.id)
    user_heroes = heroes.get(user_id_str, [])

    if not user_heroes:
        await ctx.send("You do not have any heroes in your collection.")
        return

    hero = None
    for h in user_heroes:
        if h.get("id") == hero_id:
            hero = h
        if h.get("favorite", False):
            h["favorite"] = False

    if not hero:
        await ctx.send(f"No hero with ID **{hero_id}** found in your collection.")
        return

    hero["favorite"] = True
    save_user_heroes(heroes)

    await ctx.send(f"Hero **#{hero_id}** `{hero['full_name']}` is now set as your **FAVORITE**! ❤️")


@bot.command(name="NameHero")
async def name_hero(ctx, hero_id: int, *, nickname: str):
    """Rename a hero using a nickname while preserving rarity in the displayed name."""
    heroes = load_user_heroes()
    user_id_str = str(ctx.author.id)
    user_heroes = heroes.get(user_id_str, [])

    if not user_heroes:
        await ctx.send("You do not have any heroes in your collection.")
        return

    hero = None
    for h in user_heroes:
        if h.get("id") == hero_id:
            hero = h
            break

    if not hero:
        await ctx.send(f"No hero with ID **{hero_id}** found in your collection.")
        return

    nickname = nickname.strip()
    if not nickname:
        await ctx.send("Please provide a valid nickname after the hero ID.")
        return

    hero['full_name'] = f"{nickname} - ({hero['rarity']})"
    save_user_heroes(heroes)

    await ctx.send(f"Hero **#{hero_id}** is now named `{hero['full_name']}`.")


@bot.command(name="HeroCheckIn")
async def hero_checkin(ctx, hero_id: int):
    """Check in on what a hero is doing"""
    user_heroes = get_user_heroes(ctx.author.id)

    hero = None
    for h in user_heroes:
        if h.get("id") == hero_id:
            hero = h
            break

    if not hero:
        await ctx.send(f"No hero with ID **{hero_id}** found in your collection.")
        return

    action = random.choice(CHECKIN_ACTIONS)
    hero_name = hero['full_name']
    
    message = f"What is {hero_name} doing?\n\n{hero_name} **is currently {action}**"
    
    await ctx.send(message)

@bot.command(name="ForceGodWeather")
async def force_god_weather(ctx):
    """Reset the event timer and choose a new event; only mrleave may use this."""
    if ctx.author.name != "mrleave":
        await ctx.send("Only the user named `mrleave` may use this command.")
        return

    current_state = load_event_state() or {}
    if current_state:
        await mark_previous_event_ended(current_state)
    next_state = choose_and_activate_event(exclude_name=current_state.get("name"))
    refresh_emporium_state()
    announcement = format_event_announcement(next_state, forced_by=ctx.author.name)
    sent_messages = await send_global_announcement(announcement)
    next_state["announcement_messages"] = sent_messages
    set_current_event(next_state)
    await ctx.send(f"The event timer has been reset and the new event **{next_state['name']}** is now active for 7 hours.")

@bot.command(name="ForceGPText")
async def force_gp_text(ctx, *, message: str):
    """Force GodPool to say anything globally; only mrleave may use this."""
    if ctx.author.name != "mrleave":
        await ctx.send("Only the user named `mrleave` may use this command.")
        return

    await send_global_announcement(message)
    await ctx.send("Message sent globally.")

@bot.command(name="GodGiveItemGP")
async def god_give_item_gp(ctx, item_code: str):
    """Give a specific reward item to mrleave; admin-only."""
    if ctx.author.name != "mrleave":
        await ctx.send("Only the user named `mrleave` may use this command.")
        return

    item_code = item_code.strip().upper()
    item_mapping = {
        "ES": {"name": "Evolution Stone", "type": "evolution", "description": "A mystical stone that can evolve a hero's title based on their element and class.", "multiplier": 1.0},
        "NL": {"name": "Natural Luck Stone", "type": "luck", "description": "Balanced overall luck boost from a solid victory.", "multiplier": 1.20},
        "WL": {"name": "Weak Luck Stone", "type": "luck", "description": "Teensy overall luck boost from an easy victory.", "multiplier": 1.10},
        "EL": {"name": "Enchanted Luck Stone", "type": "luck", "description": "Strong overall luck boost from a hard-fought victory.", "multiplier": 1.30},
        "ET": {"name": "Elite Training Order", "type": "class", "description": "Strong class training boost from a hard-fought victory.", "multiplier": 1.30},
        "NT": {"name": "Normal Training Order", "type": "class", "description": "Balanced class training boost from a solid victory.", "multiplier": 1.20},
        "WT": {"name": "Weak Training Order", "type": "class", "description": "Teensy class training boost from an easy victory.", "multiplier": 1.10},
    }

    item_data = item_mapping.get(item_code)
    if not item_data:
        valid_keys = ", ".join(sorted(item_mapping.keys()))
        await ctx.send(f"Invalid item code. Valid options are: {valid_keys}.")
        return

    item_data["created_at"] = datetime.datetime.utcnow().isoformat()
    add_item_to_user(ctx.author.id, item_data)

    await ctx.send(f"Granted **{item_data['name']}** to **{ctx.author.name}**.")

@bot.command(name="ForceRA")
async def force_ra(ctx, encounter_type: str):
    """Force a specific encounter type for the next !RAGodPool; only mrleave may use this."""
    if ctx.author.name != "mrleave":
        await ctx.send("Only the user named `mrleave` may use this command.")
        return

    valid_types = {"N": "Nemesis", "SO": "Sought Out", "R": "Regular"}
    if encounter_type.upper() not in valid_types:
        await ctx.send(f"Invalid encounter type. Valid types: {', '.join(f'{k} ({v})' for k, v in valid_types.items())}")
        return

    global FORCED_ENCOUNTER_TYPE
    FORCED_ENCOUNTER_TYPE = encounter_type.upper()
    
    await ctx.send(f"Next !RAGodPool will force a **{valid_types[encounter_type.upper()]}** encounter.")

@bot.command(name="GodCmds")
async def god_cmds(ctx):
    """List all admin commands; only mrleave may use this."""
    if ctx.author.name != "mrleave":
        await ctx.send("Only the user named `mrleave` may use this command.")
        return

    admin_commands = [
        "!ForceRA <type> — Force the next !RAGodPool to spawn a specific encounter type (N/Nemesis, SO/Sought Out, R/Regular)",
        "!GodGiveItemGP <code> — Give mrleave a reward item by code (ES, NL, WL, EL, ET, NT, WT)",
        "!ForceGPText <message> — Force the bot to send a global announcement",
        "!ResetEvent — Reset the event timer and choose a new event",
        "!GodPool <message> — Send a message as the bot in the current channel",
        "!CH_ <hero details> — Create a hero with custom details (admin creation)",
    ]
    
    embed = discord.Embed(
        title="Admin Commands",
        description="These commands are restricted to mrleave only.",
        color=0xff0000
    )
    
    for cmd in admin_commands:
        embed.add_field(name=cmd.split(" — ")[0], value=cmd.split(" — ")[1], inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name="Dishero")
async def dishero(ctx, hero_number: int):
    """Delete a specific hero from the user's collection by its listed number."""
    heroes = load_user_heroes()
    user_id_str = str(ctx.author.id)
    user_heroes = heroes.get(user_id_str, [])

    if not user_heroes:
        await ctx.send("You do not have any heroes in your collection.")
        return

    hero_to_remove = None
    for hero in user_heroes:
        if hero.get("id") == hero_number:
            hero_to_remove = hero
            break

    if not hero_to_remove:
        await ctx.send(f"No hero with number **{hero_number}** was found in your collection.")
        return

    heroes[user_id_str] = [hero for hero in user_heroes if hero.get("id") != hero_number]
    save_user_heroes(heroes)
    await ctx.send(f"Hero **#{hero_number}** `{hero_to_remove['full_name']}` has been removed from your collection.")

@bot.event
async def on_message(message):
    await bot.process_commands(message)

    if message.author.bot:
        return

    if message.content.startswith("CH_"):
        try:
            parts = message.content.split("_")

            if len(parts) != 6:
                await message.channel.send("Invalid format. Use: CH_Alignment_Divinity_Race_Element_Class")
                return

            alignment = parts[1]
            divinity = parts[2]
            race = parts[3]
            element = parts[4]
            clazz = parts[5]

            VALID_ALIGNMENTS = {"Valiant", "Good", "Neutral", "Mischievous", "Evil"}
            VALID_DIVINITIES = {"Divine", "Neutral", "Hellish"}
            VALID_RACES = {"Human", "Construct", "Elven", "Goblin", "Beast", "Ogre", "Deep-Crawler", "Celestial", "Angel", "Demon", "Dwarf", "Elemental", "Undead", "Magma-Crawler"}
            VALID_ELEMENTS = set(ELEMENTS.keys())
            VALID_CLASSES = {"Warrior", "Archer", "Assassin", "Mage", "Paladin", "Rogue", "Admiral", "Sniper", "Outlaw", "Bard", "Scavenger", "Ritualist", "Commander", "Defender", "Barbarian"}

            if alignment not in VALID_ALIGNMENTS:
                await message.channel.send(f"Invalid alignment '{alignment}'. Valid: {', '.join(VALID_ALIGNMENTS)}")
                return
            if divinity not in VALID_DIVINITIES:
                await message.channel.send(f"Invalid divinity '{divinity}'. Valid: {', '.join(VALID_DIVINITIES)}")
                return
            if race not in VALID_RACES:
                await message.channel.send(f"Invalid race '{race}'. Valid: {', '.join(VALID_RACES)}")
                return
            if element not in VALID_ELEMENTS:
                await message.channel.send(f"Invalid element '{element}'. Valid: {', '.join(VALID_ELEMENTS)}")
                return
            if clazz not in VALID_CLASSES:
                await message.channel.send(f"Invalid class '{clazz}'. Valid: {', '.join(VALID_CLASSES)}")
                return

            roll_count = increment_user_roll_count(message.author.id)
            is_lucky = roll_count % 10 == 0

            # Rolls (multiplicative system)
            align_roll = roll(ALIGNMENT_MODS[alignment])
            div_roll = roll(DIVINITY_MODS[divinity])
            elem_roll = roll(ELEMENT_MODS)
            class_roll = roll(CLASS_MODS)
            shiny_chance = 0.05

            align_roll, div_roll, elem_roll, class_roll, shiny_chance = apply_event_boosts(
                alignment,
                divinity,
                element,
                clazz,
                race,
                align_roll,
                div_roll,
                elem_roll,
                class_roll,
                shiny_chance,
            )

            nemesis_debuff = get_nemesis_debuff(message.author.id)
            if nemesis_debuff:
                class_roll *= nemesis_debuff.get("class_penalty", 1.0)

            active_boost = pop_user_boost(message.author.id)
            boost_used_text = None
            if active_boost and active_boost.get("type") == "class":
                class_roll *= active_boost.get("multiplier", 1.0)
                boost_used_text = active_boost.get("name")

            rarity_penalty = nemesis_debuff.get("rarity_penalty", 1.0) if nemesis_debuff else 1.0
            total_score = align_roll * div_roll * elem_roll * class_roll * rarity_penalty

            if active_boost and active_boost.get("type") == "luck":
                total_score *= active_boost.get("multiplier", 1.0)
                boost_used_text = active_boost.get("name")

            lucky_bonus = 1.0
            if is_lucky:
                lucky_bonus = random.uniform(1.1, 1.2)
                total_score *= lucky_bonus

            rarity = get_rarity(total_score)

            class_title = get_class_title(class_roll)

            element_good, element_bad = ELEMENTS[element]

            element_title = element  # default for okay rolls
            if elem_roll > 1.1:
                element_title = element_good
                element_part = f" the {element_good}"
            elif elem_roll < 0.9:
                element_title = element_bad
                element_part = f" the {element_bad}"
            else:
                element_part = ""

            name = random_name()
            feat = roll_feat(rarity)

            # Shiny chance (small chance)
            is_shiny = random.random() < shiny_chance

            final_name = f"{class_title} {clazz} {name}{element_part} - ({rarity})"

            # Store hero data
            created_at = datetime.datetime.now().strftime("%H:%M:%S %d %B %Y")

            hero_data = {
                "full_name": final_name,
                "hero_name": name,
                "class": clazz,
                "class_title": class_title,
                "rarity": rarity,
                "divinity": divinity,
                "alignment": alignment,
                "race": race,
                "element": element_title,
                "element_raw": element,
                "element_part": element_part,
                "feat": feat,
                "shiny": is_shiny,
                "favorite": False,
                "preserved": False,
                "created_at": created_at
            }
            
            try:
                add_hero_to_user(message.author.id, hero_data)
            except ValueError as error:
                await message.channel.send(str(error))
                return

            embed = discord.Embed(title="⚔️ Hero Created ⚔️", color=0x00ffcc)
            embed.add_field(name="Hero", value=final_name, inline=False)
            embed.add_field(name="Hero ID", value=str(hero_data["id"]), inline=False)
            embed.add_field(name="Rolled At", value=created_at, inline=False)
            if is_shiny:
                embed.add_field(name="SHINY", value="This hero is SHINY!", inline=False)
            embed.add_field(name="Feat", value=feat, inline=False)
            embed.add_field(name="Class", value=f"{clazz} ({class_title})", inline=True)
            embed.add_field(name="Class Modifier", value=f"{class_roll:.2f}", inline=True)
            embed.add_field(name="Element", value=f"{element} ({element_title})", inline=True)
            embed.add_field(name="Element Modifier", value=f"{elem_roll:.2f}", inline=True)
            embed.add_field(name="Divinity", value=f"{divinity} ({div_roll:.2f})", inline=True)
            embed.add_field(name="Alignment", value=f"{alignment} ({align_roll:.2f})", inline=True)
            embed.add_field(name="Race", value=race, inline=True)
            if is_lucky:
                embed.add_field(name="Lucky Roll", value=f"Yes (x{lucky_bonus:.2f})", inline=True)
            else:
                embed.add_field(name="Lucky Roll", value="No", inline=True)
            if boost_used_text:
                embed.add_field(name="Adventures Exchange Boost", value=boost_used_text, inline=True)
            embed.set_footer(text=f"Hero added to your collection! Roll #{roll_count}.")

            await message.channel.send(embed=embed)

        except Exception as e:
            await message.channel.send(f"Error creating hero: {e}")

    if message.content.startswith("God_CH_"):
        # Admin command: only mrleave can use this
        if str(message.author) != "mrleave":
            await message.channel.send("⚠️ You do not have permission to use this command.")
            return

        try:
            parts = message.content.split("_")
            if len(parts) != 10:
                await message.channel.send("Invalid format. Use: God_CH_Alignment_Divinity_Race_Element_Class_OVR_CS_Shiny")
                return

            alignment = parts[2]
            divinity = parts[3]
            race = parts[4]
            element = parts[5]
            clazz = parts[6]
            ovr_rank = parts[7]
            class_rank = parts[8]
            shiny_str = parts[9]

            VALID_ALIGNMENTS = {"Valiant", "Good", "Neutral", "Mischievous", "Evil"}
            VALID_DIVINITIES = {"Divine", "Neutral", "Hellish"}
            VALID_RACES = {"Human", "Construct", "Elven", "Goblin", "Beast", "Ogre", "Deep-Crawler", "Celestial", "Angel", "Demon", "Dwarf", "Elemental", "Undead", "Magma-Crawler"}
            VALID_ELEMENTS = set(ELEMENTS.keys())
            VALID_CLASSES = {"Warrior", "Archer", "Assassin", "Mage", "Paladin", "Rogue", "Admiral", "Sniper", "Outlaw", "Bard", "Scavenger", "Ritualist", "Commander", "Defender", "Barbarian"}
            VALID_OVR_RANKS = {"Common", "Trained", "Uncommon", "Handy", "Rare", "Pseudo", "Genesis", "Legendary", "Mythical", "Ethereal", "Ascendant", "Primordial", "Omni", "God-Challenger"}
            VALID_CLASS_RANKS = {"Horrible", "Okay", "Apprentice", "Journeyer", "Elite", "Chief", "Masterclass", "Transcendant"}

            if alignment not in VALID_ALIGNMENTS:
                await message.channel.send(f"Invalid alignment '{alignment}'.")
                return
            if divinity not in VALID_DIVINITIES:
                await message.channel.send(f"Invalid divinity '{divinity}'.")
                return
            if race not in VALID_RACES:
                await message.channel.send(f"Invalid race '{race}'.")
                return
            if element not in VALID_ELEMENTS:
                await message.channel.send(f"Invalid element '{element}'.")
                return
            if clazz not in VALID_CLASSES:
                await message.channel.send(f"Invalid class '{clazz}'.")
                return
            if ovr_rank not in VALID_OVR_RANKS:
                await message.channel.send(f"Invalid OVR rank '{ovr_rank}'.")
                return
            if class_rank not in VALID_CLASS_RANKS:
                await message.channel.send(f"Invalid class rank '{class_rank}'.")
                return
            if shiny_str.lower() not in ["yes", "no"]:
                await message.channel.send(f"Shiny must be 'Yes' or 'No'.")
                return

            is_shiny = shiny_str.lower() == "yes"

            element_good, element_bad = ELEMENTS[element]
            element_title = element_good
            element_part = f" the {element_good}"

            name = random_name()
            feat = roll_feat(ovr_rank)

            final_name = f"{class_rank} {clazz} {name}{element_part} - ({ovr_rank})"

            created_at = datetime.datetime.now().strftime("%H:%M:%S %d %B %Y")

            hero_data = {
                "full_name": final_name,
                "hero_name": name,
                "class": clazz,
                "class_title": class_rank,
                "rarity": ovr_rank,
                "divinity": divinity,
                "alignment": alignment,
                "race": race,
                "element": element_title,
                "element_raw": element,
                "element_part": element_part,
                "feat": feat,
                "shiny": is_shiny,
                "favorite": False,
                "preserved": False,
                "created_at": created_at
            }

            try:
                add_hero_to_user(message.author.id, hero_data)
            except ValueError as error:
                await message.channel.send(str(error))
                return

            embed = discord.Embed(title="🔱 Divine Hero Created 🔱", color=0xffd700)
            embed.add_field(name="Hero", value=final_name, inline=False)
            embed.add_field(name="Hero ID", value=str(hero_data["id"]), inline=False)
            embed.add_field(name="Created At", value=created_at, inline=False)
            if is_shiny:
                embed.add_field(name="✨ SHINY ✨", value="This is a SHINY hero!", inline=False)
            embed.add_field(name="Class", value=f"{clazz} ({class_rank})", inline=True)
            embed.add_field(name="OVR Rank", value=ovr_rank, inline=True)
            embed.add_field(name="Element", value=f"{element} ({element_title})", inline=True)
            embed.add_field(name="Divinity", value=divinity, inline=True)
            embed.add_field(name="Alignment", value=alignment, inline=True)
            embed.add_field(name="Race", value=race, inline=True)
            embed.add_field(name="Feat", value=feat, inline=False)
            embed.set_footer(text="Admin hero creation by mrleave.")

            await message.channel.send(embed=embed)

        except Exception as e:
            await message.channel.send(f"Error creating divine hero: {e}")

    choice = message.content.strip().title()
    if choice in NEMESIS_GUESS_OPTIONS:
        state = load_ra_encounter_state()
        active = state.get("active", {})
        encounter = active.get(str(message.author.id))

        if encounter and encounter.get("special_type") == "nemesis_challenge":
            challenge = encounter.get("challenge", {})
            if not challenge.get("pending") or challenge.get("hero_id") is None:
                await message.channel.send("You must first begin the Nemesis encounter with `!FaceRA <Encounter ID> <Hero ID>`.")
                return

            actual_move = random.choice(NEMESIS_GUESS_OPTIONS)
            challenge["attempts"] = challenge.get("attempts", 0) + 1
            challenge["last_actual"] = actual_move
            challenge["last_guess"] = choice

            if choice == actual_move:
                nemesis_data = add_nemesis_victory(message.author.id)
                remove_user_ra_encounter(state, message.author.id)
                msg = f"Your hero guessed correctly! The Nemesis falters with **{actual_move}**."
                if nemesis_data and nemesis_data.get("pending_finish"):
                    msg += "\nThe Nemesis has been defeated. Use `!KillGP` or `!RecruitGP` to finish the saga."
                await message.channel.send(msg)
                return

            guesses_left = challenge.get("remaining_guesses", 3) - challenge["attempts"]
            if guesses_left <= 0:
                remove_user_ra_encounter(state, message.author.id)
                await message.channel.send(
                    f"The Nemesis struck true with **{actual_move}**. Your guesses are spent and the encounter ends in failure."
                )
                return

            active[str(message.author.id)] = encounter
            state["active"] = active
            save_ra_encounter_state(state)
            await message.channel.send(
                f"Incorrect — the Nemesis chose **{actual_move}**. You have **{guesses_left}** guesses left. Try again with Strike or Shield."
            )
            return

        nemesis_data = get_user_nemesis(message.author.id)
        if nemesis_data and nemesis_data.get("pending_hunt") and nemesis_data["pending_hunt"].get("status") == "guessing":
            hunt = nemesis_data["pending_hunt"]
            actual_move = random.choice(NEMESIS_GUESS_OPTIONS)
            hunt["attempts"] = hunt.get("attempts", 0) + 1
            if choice == actual_move:
                hunt["successes"] = hunt.get("successes", 0) + 1
                if hunt["successes"] >= hunt.get("required_successes", 3):
                    add_nemesis_victory(message.author.id)
                    nemesis_data.pop("pending_hunt", None)
                    set_user_nemesis(message.author.id, nemesis_data)
                    msg = f"You predicted the Nemesis' move correctly! The hunt is broken with **{actual_move}**."
                    if nemesis_data.get("pending_finish"):
                        msg += "\nThe Nemesis has been defeated. Use `!KillGP` or `!RecruitGP` to finish the saga."
                    await message.channel.send(msg)
                    return
                set_user_nemesis(message.author.id, nemesis_data)
                await message.channel.send(
                    f"Correct! The Nemesis flinches with **{actual_move}**. Successes: **{hunt['successes']}** / {hunt['required_successes']}. Attempts left: **{hunt['max_attempts'] - hunt['attempts']}**."
                )
                return

            if hunt["attempts"] >= hunt.get("max_attempts", 7):
                nemesis_data.pop("pending_hunt", None)
                set_user_nemesis(message.author.id, nemesis_data)
                await message.channel.send(
                    f"The Nemesis outmaneuvered you with **{actual_move}**. Your hunt attempt has failed."
                )
                return

            set_user_nemesis(message.author.id, nemesis_data)
            await message.channel.send(
                f"Wrong again — the Nemesis chose **{actual_move}**. Successes: **{hunt.get('successes', 0)}** / {hunt.get('required_successes', 3)}. Attempts left: **{hunt['max_attempts'] - hunt['attempts']}**."
            )
            return

bot.run(TOKEN)
