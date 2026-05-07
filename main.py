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
            with open(HEROES_FILE, "r") as f:
                return json.load(f)
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
                    print(f"Failed to save heroes to Gist: {response.status_code}")
            else:
                print(f"Failed to fetch Gist for saving: {response.status_code}")
        except Exception as e:
            print(f"Error saving heroes to Gist: {e}")
    else:
        with open(HEROES_FILE, "w") as f:
            json.dump(heroes_data, f, indent=2)


def load_user_roll_counts():
    """Load persisted roll counts for users."""
    if USE_GIST:
        try:
            response = requests.get(GIST_URL, headers=HEADERS)
            if response.status_code == 200:
                gist_data = response.json()
                counts_content = gist_data['files'].get('user_roll_counts.json', {}).get('content', '{}')
                return json.loads(counts_content)
            else:
                print(f"Failed to load roll counts from Gist: {response.status_code}")
                return {}
        except Exception as e:
            print(f"Error loading roll counts from Gist: {e}")
            return {}
    else:
        if ROLL_COUNTER_FILE.exists():
            with open(ROLL_COUNTER_FILE, "r") as f:
                return json.load(f)
        return {}


def save_user_roll_counts(counts):
    """Save persisted roll counts for users."""
    if USE_GIST:
        try:
            # Get current Gist data
            response = requests.get(GIST_URL, headers=HEADERS)
            if response.status_code == 200:
                gist_data = response.json()
                files = gist_data.get('files', {})
                # Update roll counts
                files['user_roll_counts.json'] = {
                    "content": json.dumps(counts, indent=2)
                }
                data = {"files": files}
                response = requests.patch(GIST_URL, headers=HEADERS, json=data)
                if response.status_code not in [200, 201]:
                    print(f"Failed to save roll counts to Gist: {response.status_code}")
            else:
                print(f"Failed to fetch Gist for saving: {response.status_code}")
        except Exception as e:
            print(f"Error saving roll counts to Gist: {e}")
    else:
        with open(ROLL_COUNTER_FILE, "w") as f:
            json.dump(counts, f, indent=2)


def increment_user_roll_count(user_id):
    """Increment the user's roll count and return the new count."""
    counts = load_user_roll_counts()
    user_id_str = str(user_id)
    counts[user_id_str] = counts.get(user_id_str, 0) + 1
    save_user_roll_counts(counts)
    return counts[user_id_str]

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

def get_next_hero_id(user_id):
    """Get the next hero ID for a user's collection."""
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
    return f"🌟 **{title}** is now active!\n{boost}\n\n{details}\n\n{time_str} remain\n\n{footer}"


def format_event_ended_message(state):
    """Create the announcement text for an ended event."""
    title = state.get("name", "The previous event")
    return f"✅ **{title}** has ended. A new event is now active."


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
            align_roll *= random.uniform(1.4, 1.9)
    elif event_name == "Celestial Convergence":
        if divinity == "Divine":
            div_roll *= random.uniform(1.35, 1.75)
        if element == "Celestial":
            elem_roll *= random.uniform(1.35, 1.75)
    elif event_name == "Infernal Surge":
        if element in ["Lava", "Magma", "Fire"]:
            elem_roll *= random.uniform(1.25, 1.7)
            if random.random() < 0.2:
                elem_roll *= random.uniform(0.55, 1.3)
    elif event_name == "The Hollow Fog":
        if element in ["Mist", "Dark"]:
            shiny_chance += 0.12
    elif event_name == "Verdant Bloom":
        if element in ["Plants", "Life"]:
            elem_roll *= random.uniform(1.25, 1.7)
            if elem_roll < 1.0:
                elem_roll *= 0.75
    elif event_name == "Thunder Dominion":
        if element in ["Lightning", "Air"]:
            class_roll *= random.uniform(1.25, 1.65)
    elif event_name == "The Drowned Tide":
        if element in ["Water", "Rain"]:
            elem_roll *= random.uniform(1.3, 1.75)
            shiny_chance += 0.1
    elif event_name == "Gravecall Night":
        if race == "Undead" or element == "Death":
            align_roll *= random.uniform(1.5, 2.1)
    elif event_name == "Prismatic Awakening":
        if element in ["Glass", "Crystal", "Color"]:
            class_roll *= random.uniform(1.35, 1.8)
    elif event_name == "The Beast Hunt":
        if race == "Beast" or element == "Beast":
            class_roll *= random.uniform(1.35, 1.8)
    elif event_name == "Eclipse of Judgment":
        align_roll *= random.uniform(1.4, 2.0)
    elif event_name == "Forgeheart Festival":
        if element in ["Steel", "Earth"]:
            elem_roll *= random.uniform(1.35, 1.8)
    elif event_name == "The Rotting Bloom":
        if element in ["Spore", "Poison"]:
            elem_roll *= random.uniform(1.4, 1.95)
            shiny_chance += 0.15
    elif event_name == "Starfall Cataclysm":
        if element in ["Celestial", "Equinox"]:
            align_roll *= random.uniform(1.4, 1.9)
            class_roll *= random.uniform(1.25, 1.6)
    elif event_name == "The Ashen Era":
        if element in ["Fire", "Lava", "Magma"]:
            class_roll *= random.uniform(1.35, 1.8)
    elif event_name == "Sanctuary of Dawn":
        if element == "Light" or alignment in ["Good", "Valiant"]:
            if div_roll < 1.0:
                div_roll *= 1.25
            if align_roll < 1.0:
                align_roll *= 1.25
    elif event_name == "The Rift Collapse":
        elem_roll *= 2.0
    elif event_name == "The Wandering Tempest":
        if element in ["Air", "Rain", "Lightning"]:
            elem_roll *= random.uniform(1.3, 1.75)
    elif event_name == "Kingdoms at War":
        if clazz in ["Commander", "Paladin", "Admiral", "Warrior"]:
            class_roll *= random.uniform(1.5, 2.0)
    elif event_name == "The Abyss Stares Back":
        if element in ["Corruption", "Dark"] or alignment in ["Mischievous", "Evil"]:
            bonus = random.uniform(0.45, 1.1)
            align_roll *= bonus
            elem_roll *= random.uniform(0.75, 1.25)

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

# Multiplicative modifiers (1.0 = neutral, >1.0 = boost, <1.0 = penalty)
ALIGNMENT_MODS = {
    "Valiant": (0.9, 2.35),
    "Good": (1.10, 1.85),
    "Neutral": (0.95, 1.85),
    "Mischievous": (0.65, 2.65),
    "Evil": (0.58, 2.75),
}

DIVINITY_MODS = {
    "Divine": (0.77, 2.00),
    "Neutral": (0.8, 1.85),
    "Hellish": (0.6, 2.3),
}

ELEMENT_MODS = (0.8, 1.0)
CLASS_MODS = (0.8, 1.0)


RARITY_TIERS = [
    (0.0, "Common"),
    (0.55, "Trained"),
    (0.8, "Uncommon"),
    (1.2, "Handy"),
    (1.7, "Rare"),
    (3.9, "Pseudo"),
    (4.5, "Genisis"),
    (5.75, "Legendary"),
    (6.4, "Mythical"),
    (7.1, "Ethereal"),
    (8.9, "Ascendant"),
    (9.5, "Primordial"),
    (10.0, "Omni"),
    (11.0, "God-Challenger"),
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
    (1.2, "Transcendent"),
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

@bot.command(name="HerosGodPool")
async def heros_god_pool(ctx):
    """Display all heroes in a user's collection (name, rarity, and ID only)"""
    user_heroes = get_user_heroes(ctx.author.id)
    
    if not user_heroes:
        await ctx.send(f"**HERO COLLECTION — {ctx.author.name}**\n\nYou currently have **0 heroes** in your collection. Create one with `CH_Alignment_Divinity_Race_Element_Class`!")
        return
    
    # Build the message with just name, rarity, and ID
    message = f"**HERO COLLECTION — {ctx.author.name}**\n\nYou currently have **{len(user_heroes)}** heroes in your collection:\n\n---\n\n"
    
    for hero in user_heroes:
        icons = ""
        if hero.get('shiny', False):
            icons += " ✨"
        if hero.get('favorite', False):
            icons += " ❤️"
        message += f"**#{hero['id']}** | {hero['full_name']}{icons} | ⭐ {hero['rarity']}\n"
    
    message += f"\n---\n*Use `!ViewHero <number>` to see a hero's full details.*\n✨ Shiny   ❤️ Favorite"
    
    # Discord has a 2000 character limit per message, so split if needed
    if len(message) > 2000:
        # Split into multiple messages
        chunks = []
        current = f"**HERO COLLECTION — {ctx.author.name}**\n\nYou currently have **{len(user_heroes)}** heroes in your collection:\n\n---\n\n"
        
        for hero in user_heroes:
            icons = ""
            if hero.get('shiny', False):
                icons += " ✨"
            if hero.get('favorite', False):
                icons += " ❤️"
            hero_text = f"**#{hero['id']}** | {hero['full_name']}{icons} | ⭐ {hero['rarity']}\n"
            
            if len(current) + len(hero_text) > 1900:  # Leave room for footer
                chunks.append(current)
                current = hero_text
            else:
                current += hero_text
        
        if current:
            chunks.append(current + f"\n---\n*Use `!ViewHero <number>` to see a hero's full details.*\n✨ Shiny   ❤️ Favorite")
        
        for chunk in chunks:
            await ctx.send(chunk)
    else:
        await ctx.send(message)


@bot.command(name="GodPoolCmds")
async def godpool_cmds(ctx):
    """Display every GodPool command and what it does."""
    help_text = (
        "**GodPool Command List**\n\n"
        "`!CH` — Create a new hero using `CH_Alignment_Divinity_Race_Element_Class`.\n"
        "`!HerosGodPool` — List your heroes with ID, name, and rarity.\n"
        "`!ViewHero <id>` — Show full details for one hero.\n"
        "`!DeleteAllHerosGodPool` — Delete all your heroes except those preserved.\n"
        "`!PreserveHero <id>` — Toggle preservation so a hero is not deleted by `!DeleteAllHerosGodPool`.\n"
        "`!FavHero <id>` — Mark a hero as your favorite.\n"
        "`!NameHero <id> <nickname>` — Rename a hero while preserving its displayed rarity.\n"
        "`!HeroCheckIn <id>` — Check in on what a hero is currently doing.\n"
        "`!Dishero <id>` — Delete a specific hero from your collection.\n"
        "`!ForceGodWeather` — Reset the event timer and choose a new event (only `mrleave`).\n"
        "`!GodPoolCmds` — Show this command list.\n"
    )
    await ctx.send(help_text)


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
    message += f"**Element:** {hero['element']}\n"
    message += f"**Feat:** {hero['feat']}\n"
    message += f"**Rolled At:** {hero.get('created_at', 'Unknown')}\n"
    if hero.get('shiny', False):
        message += f"\n**This hero is SHINY!**\n"
    if hero.get('favorite', False):
        message += f"\n**This hero is your FAVORITE! ❤️**\n"
    
    await ctx.send(message)


@bot.command(name="DeleteAllHerosGodPool")
async def delete_all_heros_god_pool(ctx):
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
    """Preserve a hero to prevent it from being deleted by !DeleteAllHerosGodPool"""
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
        await ctx.send(f"Hero **#{hero_id}** `{hero['full_name']}` is now **PRESERVED** and will not be deleted by `!DeleteAllHerosGodPool`.")
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
    announcement = format_event_announcement(next_state, forced_by=ctx.author.name)
    sent_messages = await send_global_announcement(announcement)
    next_state["announcement_messages"] = sent_messages
    set_current_event(next_state)
    await ctx.send(f"The event timer has been reset and the new event **{next_state['name']}** is now active for 7 hours.")

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

            alignment = parts[1]
            divinity = parts[2]
            race = parts[3]
            element = parts[4]
            clazz = parts[5]

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

            total_score = align_roll * div_roll * elem_roll * class_roll
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
                "class": clazz,
                "class_title": class_title,
                "rarity": rarity,
                "divinity": divinity,
                "alignment": alignment,
                "race": race,
                "element": element_title,
                "feat": feat,
                "shiny": is_shiny,
                "favorite": False,
                "preserved": False,
                "created_at": created_at
            }
            
            add_hero_to_user(message.author.id, hero_data)

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
            embed.set_footer(text=f"Hero added to your collection! Roll #{roll_count}.")

            await message.channel.send(embed=embed)

        except Exception as e:
            await message.channel.send(f"Error creating hero: {e}")


bot.run(TOKEN)