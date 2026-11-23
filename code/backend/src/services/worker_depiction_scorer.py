"""
Pure, stateless scoring and keyword-planning utilities for discovering museum
artifacts that visually depict ancient workers (artisans, agricultural laborers,
scribes, merchants, enslaved people, medical practitioners, and workshop scenes).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, List, Literal, Optional, Sequence, Tuple

WorkerConfidence = Literal["high", "medium", "low", "none"]

MAX_SCORED_TEXT_LEN = 20_000

WORKER_SEARCH_PRESETS: List[Dict[str, Any]] = [
    {
        "id": "all_ancient_workers",
        "name": "All Ancient Workers",
        "description": "High-precision worker roles, workshops, tomb models, and labor scenes across trades.",
        "keywords": [
            "work scene",
            "potter",
            "weaver",
            "blacksmith",
            "scribe",
            "baker",
            "farmer",
            "carpenter",
            "sculptor",
            "shoemaker",
            "fisherman",
            "shepherd",
            "merchant",
            "slave",
            "physician",
            "glassblower",
            "ushabti",
            "hephaestus",
        ],
        "recommended_date_start": -3000,
        "recommended_date_end": 899,
    },
    {
        "id": "artisans_workshops",
        "name": "Artisans & Workshops",
        "description": "Potters, smiths, weavers, sculptors, shoemakers, glassblowers, and ancient workshop scenes.",
        "keywords": [
            "potter",
            "blacksmith",
            "weaver",
            "sculptor",
            "carpenter",
            "shoemaker",
            "cobbler",
            "jeweler",
            "glassblower",
            "vitrearii",
            "fuller",
            "tanner",
            "stonemason",
            "carver",
            "woodworker",
            "metalworker",
            "workshop",
            "ergasterion",
            "hephaestus",
            "vulcan",
        ],
        "recommended_date_start": -2500,
        "recommended_date_end": 899,
    },
    {
        "id": "agriculture_food",
        "name": "Agriculture & Food Production",
        "description": "Farmers, harvesters, bakers, brewers, butchers, shepherds, and rural estate labor.",
        "keywords": [
            "farmer",
            "baker",
            "brewer",
            "butcher",
            "shepherd",
            "fisherman",
            "harvester",
            "plowman",
            "winemaker",
            "miller",
            "herdsman",
            "peasant",
            "bakery",
            "brewery",
            "olive harvest",
            "vintage",
            "grain harvest",
        ],
        "recommended_date_start": -3000,
        "recommended_date_end": 899,
    },
    {
        "id": "scribes_trade_maritime",
        "name": "Scribes, Medicine & Trade",
        "description": "Scribes, physicians, midwives, merchants, sailors, shipwrights, and market scenes.",
        "keywords": [
            "scribe",
            "merchant",
            "trader",
            "physician",
            "midwife",
            "doctor",
            "sailor",
            "rower",
            "shipwright",
            "boatbuilder",
            "banker",
            "shopkeeper",
            "caravan",
            "barber",
            "weighing",
        ],
        "recommended_date_start": -3000,
        "recommended_date_end": 899,
    },
    {
        "id": "enslaved_monumental",
        "name": "Enslaved Labor & Monumental Work",
        "description": "Enslaved workers, servants, porters, miners, brickmakers, builders, and funerary ushabti figures.",
        "keywords": [
            "slave",
            "enslaved",
            "servant",
            "attendant",
            "porter",
            "bearer",
            "miner",
            "brickmaker",
            "builder",
            "laborer",
            "serf",
            "captive",
            "ushabti",
            "shabti",
            "apprentice",
        ],
        "recommended_date_start": -3000,
        "recommended_date_end": 899,
    },
]

TYPO_CORRECTIONS: Dict[str, str] = {
    "pesant": "peasant",
    "carvan": "caravan",
    "ergateri": "ergasterion",
}

LOW_PRECISION_GENERIC_KEYWORDS: FrozenSet[str] = frozenset({
    "glass",
    "craft",
    "tool",
    "mold",
    "mould",
    "bow",
    "saw",
    "press",
    "grain",
    "scene",
    "work",
    "product",
    "producer",
    "maker",
    "shop",
    "sow",
    "driver",
    "construction",
    "cutter",
    "painter",
    "kiln",
    "oven",
    "furnace",
    "drill",
    "smelt",
})

HIGH_PRECISION_WORKER_TERMS: FrozenSet[str] = frozenset({
    "ancient worker",
    "work scene",
    "glass maker",
    "olive harvest",
    "grain harvest",
    "tomb model",
    "craftsman",
    "craftsmen",
    "craftworker",
    "craftworkers",
    "artisan",
    "artisans",
    "potter",
    "potters",
    "weaver",
    "weavers",
    "blacksmith",
    "blacksmiths",
    "scribe",
    "scribes",
    "sculptor",
    "sculptors",
    "baker",
    "bakers",
    "brewer",
    "brewers",
    "farmer",
    "farmers",
    "butcher",
    "butchers",
    "carpenter",
    "carpenters",
    "apprentice",
    "jeweler",
    "jewelers",
    "goldsmith",
    "silversmith",
    "glassblower",
    "vitrearii",
    "ergasterion",
    "slave",
    "slaves",
    "enslaved",
    "servant",
    "servants",
    "attendant",
    "porter",
    "bearer",
    "shoemaker",
    "cobbler",
    "tailor",
    "carver",
    "smith",
    "builder",
    "midwife",
    "physician",
    "doctor",
    "serf",
    "peasant",
    "merchant",
    "trader",
    "shopkeeper",
    "banker",
    "fisherman",
    "shepherd",
    "herdsman",
    "sailor",
    "rower",
    "shipwright",
    "boatbuilder",
    "mason",
    "stonemason",
    "fuller",
    "tanner",
    "miner",
    "brickmaker",
    "harvester",
    "plowman",
    "winemaker",
    "miller",
    "barber",
    "laborer",
    "labourer",
    "captive",
    "ushabti",
    "shabti",
    "workshop",
    "caravan",
    "hephaestus",
    "vulcan",
    "daedalus",
    "pygmalion",
    "woodworker",
    "metalworker",
})

_MET_TAG_RULES: List[Tuple[Tuple[str, ...], Tuple[str, ...]]] = [
    (("scribe",), ("Scribes",)),
    (("potter", "pottery", "kiln"), ("Pottery", "Working")),
    (("weaver", "weaving", "spinner", "spinning", "loom"), ("Weaving", "Spinning")),
    (("blacksmith", "smith", "metalworker", "smithy", "forge"), ("Blacksmiths", "Working")),
    (("carpenter", "woodworker", "carpentry", "shipwright", "boatbuilder"), ("Carpenters", "Working")),
    (("sculptor", "stonemason", "mason", "carver"), ("Sculptors",)),
    (("baker", "bakery"), ("Bakers", "Working")),
    (("brewer", "brewery", "brewing"), ("Brewing", "Working")),
    (("butcher", "slaughterhouse"), ("Butchers", "Working")),
    (("farmer", "peasant", "harvester", "plowman", "harvest", "agriculture"), ("Farmers", "Harvesting", "Agriculture")),
    (("shepherd", "herdsman"), ("Shepherds",)),
    (("fisherman", "fishing"), ("Fishermen", "Fishing")),
    (("sailor", "rower"), ("Sailors",)),
    (("slave", "enslaved", "captive", "miner", "brickmaker", "porter", "bearer", "builder"), ("Slaves", "Servants", "Working")),
    (("servant", "attendant", "ushabti", "shabti"), ("Servants",)),
    (("physician", "doctor", "midwife"), ("Doctors",)),
    (("merchant", "trader", "shopkeeper", "banker", "caravan", "weighing"), ("Merchants",)),
    (("hephaestus",), ("Hephaestus",)),
    (("vulcan",), ("Vulcan",)),
    (("daedalus",), ("Daedalus",)),
    (
        (
            "ancient worker",
            "work scene",
            "worker",
            "craftsman",
            "craftsmen",
            "craftworker",
            "workshop",
            "ergasterion",
            "apprentice",
            "laborer",
            "labourer",
            "serf",
            "shoemaker",
            "cobbler",
            "jeweler",
            "glassblower",
            "glass maker",
            "vitrearii",
            "fuller",
            "tanner",
            "tailor",
            "barber",
            "winemaker",
            "miller",
        ),
        ("Working", "Craftworkers"),
    ),
]

# Controlled museum subject-tag terms indicating depicted labor or workers
_CONTROLLED_SUBJECT_TERMS: FrozenSet[str] = frozenset({
    "working",
    "worker",
    "workers",
    "craftworker",
    "craftworkers",
    "craftsman",
    "craftsmen",
    "artisan",
    "artisans",
    "scribe",
    "scribes",
    "farmer",
    "farmers",
    "farming",
    "baker",
    "bakers",
    "baking",
    "brewer",
    "brewers",
    "brewing",
    "weaving",
    "weaver",
    "weavers",
    "spinning",
    "spinner",
    "blacksmith",
    "blacksmiths",
    "smith",
    "smiths",
    "carpenter",
    "carpenters",
    "carpentry",
    "sculptor",
    "sculptors",
    "potter",
    "potters",
    "pottery making",
    "shepherd",
    "shepherds",
    "fisherman",
    "fishermen",
    "fishing",
    "sailor",
    "sailors",
    "slave",
    "slaves",
    "slavery",
    "enslaved",
    "servant",
    "servants",
    "merchant",
    "merchants",
    "doctor",
    "doctors",
    "physician",
    "physicians",
    "midwife",
    "butcher",
    "butchers",
    "shoemaker",
    "shoemakers",
    "cobbler",
    "mason",
    "masons",
    "stonemason",
    "harvesting",
    "harvest",
    "agriculture",
    "plowing",
    "ploughing",
    "plowman",
    "ushabti",
    "shabti",
    "hephaestus",
    "vulcan",
    "daedalus",
    "workshop",
    "workshops",
    "laborer",
    "labourer",
    "laborers",
    "labourers",
    "miner",
    "miners",
    "mining",
    "fuller",
    "tanner",
    "porter",
    "porters",
    "miller",
    "winemaker",
    "brickmaker",
    "rowing",
    "rower",
    "rowers",
    "shipwright",
    "peasant",
    "peasants",
    "glassblower",
    "jeweler",
    "goldsmith",
    "silversmith",
    "weighing",
})

# Regex patterns to strip maker/artist attribution boilerplate BEFORE lowercasing
_CASE_SENSITIVE_ATTR_RE = re.compile(
    r"\b(?:the\s+)?(?:[A-Z][A-Za-z0-9'\-]{1,35}\s+){1,3}Painter\b"
)
_ATTRIBUTION_BOILERPLATE_RE = re.compile(
    r"(?:"
    r"\battributed to\b[^.;,\n]{0,90}"
    r"|\b(?:in the\s+)?(?:manner|circle|follower|school|workshop|studio|group|class) of\b[^.;,\n]{0,80}"
    r"|\bunknown (?:maker|artist|craftsman|potter|painter|sculptor|weaver|smith|artisan)s?\b"
    r"|\bsigned by\b[^.;,\n]{0,60}\b(?:potter|painter|maker)\b"
    r"|\b(?:made|fashioned|crafted|thrown|blown|cast|forged|woven|painted) (?:by|from|of|in)\b[^.;,\n]{0,55}"
    r"|\b(?:artist|maker|potter|painter)\s*:\s*[^.;\n]{0,80}"
    r")",
    re.IGNORECASE,
)
_COMPOUND_NOISE_RE = re.compile(
    r"\b(?:"
    r"works? of art"
    r"|open-?work|metal-?work|wood-?work|stone-?work|gold-?work|silver-?work|iron-?work"
    r"|lace-?work|needle-?work|net-?work|frame-?work|earth-?work|art-?work|master-?work|inlay-?work|basket-?work"
    r"|craftsmanship|workmanship"
    r"|moul?d-?blown|free-?blown|wheel-?thrown|hand-?built|press-?moul?ded"
    r"|bow (?:fibula|brooch|harp|lyre)s?"
    r"|rain-?bows?"
    r"|saw-?tooth"
    r"|wood grain|grain of"
    r"|glass-?making technique"
    r")\b",
    re.IGNORECASE,
)

# Worker terms anchored strictly to occupations, actions, and mythic artisans
_WORKER_OCCUPATION_TERMS: Tuple[str, ...] = (
    "ancient worker",
    "ancient workers",
    "worker",
    "workers",
    "workmen",
    "workman",
    "workwomen",
    "workwoman",
    "craftworker",
    "craftworkers",
    "craftsman",
    "craftsmen",
    "artisan",
    "artisans",
    "potter",
    "potters",
    "weaver",
    "weavers",
    "blacksmith",
    "blacksmiths",
    "scribe",
    "scribes",
    "sculptor",
    "sculptors",
    "baker",
    "bakers",
    "brewer",
    "brewers",
    "farmer",
    "farmers",
    "butcher",
    "butchers",
    "carpenter",
    "carpenters",
    "shoemaker",
    "shoemakers",
    "cobbler",
    "cobblers",
    "jeweler",
    "jewelers",
    "jeweller",
    "goldsmith",
    "goldsmiths",
    "silversmith",
    "silversmiths",
    "bronzesmith",
    "ironsmith",
    "glassblower",
    "glassblowers",
    "glassmaker",
    "glass maker",
    "vitrearius",
    "vitrearii",
    "fuller",
    "fullers",
    "tanner",
    "tanners",
    "stonemason",
    "stonemasons",
    "mason",
    "masons",
    "woodworker",
    "metalworker",
    "tailor",
    "tailors",
    "carver",
    "carvers",
    "builder",
    "builders",
    "apprentice",
    "apprentices",
    "merchant",
    "merchants",
    "trader",
    "traders",
    "shopkeeper",
    "shopkeepers",
    "banker",
    "bankers",
    "slave",
    "slaves",
    "enslaved",
    "servant",
    "servants",
    "attendant",
    "attendants",
    "porter",
    "porters",
    "bearer",
    "bearers",
    "miner",
    "miners",
    "brickmaker",
    "brickmakers",
    "laborer",
    "laborers",
    "labourer",
    "labourers",
    "serf",
    "serfs",
    "peasant",
    "peasants",
    "captive",
    "captives",
    "physician",
    "physicians",
    "midwife",
    "midwives",
    "doctor",
    "doctors",
    "surgeon",
    "barber",
    "shepherd",
    "shepherds",
    "herdsman",
    "herdsmen",
    "fisherman",
    "fishermen",
    "sailor",
    "sailors",
    "mariner",
    "mariners",
    "rower",
    "rowers",
    "oarsman",
    "oarsmen",
    "shipwright",
    "boatbuilder",
    "harvester",
    "harvesters",
    "plowman",
    "ploughman",
    "winemaker",
    "miller",
    "millers",
    "ushabti",
    "shabti",
    "hephaestus",
    "vulcan",
    "daedalus",
    "pygmalion",
    "work gang",
    "work scene",
    "working scene",
    "kneading dough",
    "spinning wool",
    "weaving at a loom",
    "harvesting olives",
    "harvesting grain",
    "harvesting wheat",
    "treading grapes",
    "making bricks",
    "brick-making",
    "smelting bronze",
    "casting bronze",
    "hammering iron",
    "forging",
    "throwing on a wheel",
    "shaping pottery",
    "quarrying",
    "reaping",
    "threshing",
    "winnowing",
    "plowing",
    "ploughing",
    "slaughterhouse",
    "women weaving",
    "woman weaving",
    "weaving wool",
    "spinning thread",
    "men harvesting",
    "men plowing",
    "men ploughing",
    "baking bread",
    "brewing beer",
    "blowing glass",
    "mending nets",
    "making shoes",
)

_WORKPLACE_TERMS: Tuple[str, ...] = (
    "workshop",
    "workshops",
    "ergasterion",
    "bakery",
    "brewery",
    "smithy",
    "forge",
    "granary",
    "fullery",
    "tannery",
    "boatyard",
    "carpenter's shop",
    "potter's shop",
)

_OCCUPATION_PATTERN = "|".join(
    sorted((re.escape(term) for term in _WORKER_OCCUPATION_TERMS), key=len, reverse=True)
)
_WORKPLACE_PATTERN = "|".join(
    sorted((re.escape(term) for term in _WORKPLACE_TERMS), key=len, reverse=True)
)

_WORKER_TERM_RE = re.compile(rf"\b(?:{_OCCUPATION_PATTERN})\b", re.IGNORECASE)
_WORKPLACE_TERM_RE = re.compile(rf"\b(?:{_WORKPLACE_PATTERN})\b", re.IGNORECASE)

_DEPICTION_CUES = (
    r"depicting|depicts|depiction of|showing|shows|represented|representing|"
    r"scene(?:s)?(?: of| with)?|tomb model|funerary model|model of|"
    r"relief(?:s)?(?: of| with)?|stele|stela|figurine|statuette|statue|"
    r"figure(?:s)? of|fresco|wall painting|painting|mosaic|plaque|"
    r"sarcophagus|portrait|bust|gravestone|tombstone|epitaph|group of"
)
_TITLE_DEPICT_WORKER_RE = re.compile(
    rf"\b(?:{_DEPICTION_CUES})\b[^.;]{{0,70}}\b(?:{_OCCUPATION_PATTERN}|{_WORKPLACE_PATTERN})\b"
    rf"|\b(?:{_OCCUPATION_PATTERN})\b[^.;]{{0,50}}\b(?:relief|stele|stela|figurine|statuette|statue|fresco|mosaic|model|painting|ushabti|shabti)\b",
    re.IGNORECASE,
)
_DESC_DEPICT_PHRASE_RE = re.compile(
    rf"\b(?:depicting|depicts|depiction of|showing|shows|scene(?:s)?(?: of| with)?|"
    rf"model of|tomb model|funerary model|relief of|painting of|fresco of|mosaic of|figure of|portraying)\b"
    rf"[^.;\n]{{0,90}}\b(?P<term>{_OCCUPATION_PATTERN}|{_WORKPLACE_PATTERN})\b",
    re.IGNORECASE,
)
_FIGURATIVE_MEDIUM_RE = re.compile(
    r"\b(?:relief|stele|stela|fresco|wall painting|mosaic|tomb model|funerary model|"
    r"figurine|statuette|statue|ushabti|shabti|amphora|kylix|krater|lekythos|pelike|"
    r"hydria|skyphos|oinochoe|vase|alabastron|sarcophagus|plaque|gem|intaglio|cameo|"
    r"seal|gold-glass|roundel|ostracon|papyrus|painting|medallion|terracotta lamp)\b",
    re.IGNORECASE,
)
_OCCUPATIONAL_INSCRIPTION_RE = re.compile(
    r"\b(?:sutor|faber|pistor|medicus|pictor|vitrearius|fullo|ergasterion|"
    r"shoemaker|blacksmith|scribe|physician|baker|potter|weaver|carpenter|sculptor|merchant|craftsman|workshop)\b",
    re.IGNORECASE,
)

_PLAIN_TOOL_RE = re.compile(
    r"\b(?:"
    r"loom ?weights?|spindle ?whorls?|iron saw|bronze saw|handsaw|saw blade|"
    r"bronze drill|bow drill|chisel|adze|awl|fish ?hook|net sinker|"
    r"scale weight|balance weight|stylus|stilus|wax tablet|"
    r"casting moul?d|lamp moul?d|glass moul?d|millstone|quern|mortar and pestle|"
    r"sickle|plowshare|ploughshare|hoe|spade|trowel|plumb bob|anvil|tongs|"
    r"crucible|shuttle|bobbin|shears|cleaver|pickaxe|brick stamp|bread stamp"
    r")\b",
    re.IGNORECASE,
)
_GENERIC_SINGLE_TOOL_WORDS: FrozenSet[str] = frozenset({
    "saw",
    "mold",
    "mould",
    "tool",
    "needle",
    "hammer",
    "axe",
    "drill",
    "stylus",
    "weight",
})


@dataclass
class WorkerDepictionResult:
    """Structured relevance score and explanation for an artifact's depiction of ancient workers."""

    score: int
    confidence: WorkerConfidence
    signals: List[str] = field(default_factory=list)
    is_plain_tool: bool = False


def _safe_str(val: Any) -> str:
    if not isinstance(val, str):
        return ""
    cleaned = re.sub(r"\s+", " ", val).strip()
    if len(cleaned) > MAX_SCORED_TEXT_LEN:
        return cleaned[:MAX_SCORED_TEXT_LEN]
    return cleaned


def _scrub_noise(text: str) -> str:
    """Strip maker/artist attribution credits and non-worker compound words before scoring."""
    if not text:
        return ""
    scrubbed = _CASE_SENSITIVE_ATTR_RE.sub(" ", text)
    scrubbed = _ATTRIBUTION_BOILERPLATE_RE.sub(" ", scrubbed)
    scrubbed = _COMPOUND_NOISE_RE.sub(" ", scrubbed)
    return re.sub(r"\s+", " ", scrubbed).strip()


def prepare_worker_keywords(keywords: Sequence[str], worker_focused: bool = True) -> List[str]:
    """Normalize typos, collapse singular/plural dupes, and prioritize worker-depiction keywords."""
    cleaned_raw: List[str] = []
    seen_exact: set[str] = set()
    for raw in keywords:
        if not isinstance(raw, str):
            continue
        norm = re.sub(r"\s+", " ", raw).strip()
        if not norm:
            continue
        if worker_focused:
            norm = TYPO_CORRECTIONS.get(norm.lower(), norm)
        low = norm.lower()
        if low not in seen_exact:
            seen_exact.add(low)
            cleaned_raw.append(norm)

    if not worker_focused:
        return cleaned_raw

    lower_set = {kw.lower() for kw in cleaned_raw}
    deduped: List[str] = []
    for kw in cleaned_raw:
        low = kw.lower()
        if len(low) > 3 and low.endswith("s") and low[:-1] in lower_set:
            continue
        if len(low) > 4 and low.endswith("es") and low[:-2] in lower_set:
            continue
        deduped.append(kw)

    tier_phrases: List[str] = []
    tier_worker_roles: List[str] = []
    tier_generic: List[str] = []

    for kw in deduped:
        low = kw.lower()
        if low in LOW_PRECISION_GENERIC_KEYWORDS:
            tier_generic.append(kw)
        elif " " in low or low in HIGH_PRECISION_WORKER_TERMS:
            if " " in low and any(term in low for term in ("worker", "scene", "harvest", "model", "maker")):
                tier_phrases.append(kw)
            else:
                tier_worker_roles.append(kw)
        else:
            tier_worker_roles.append(kw)

    prioritized = tier_phrases + tier_worker_roles
    if len(prioritized) >= 3:
        return prioritized
    return prioritized + tier_generic


def expand_met_subject_tags(keywords: Sequence[str], max_tags: int = 12) -> List[str]:
    """Map user keywords to Met Collection API Getty AAT depicted subject tags (`tags=true`)."""
    selected: List[str] = []
    seen: set[str] = set()

    def _add(tag: str) -> None:
        low = tag.lower()
        if low not in seen and len(selected) < max_tags:
            seen.add(low)
            selected.append(tag)

    for raw in keywords:
        if not isinstance(raw, str):
            continue
        norm = TYPO_CORRECTIONS.get(raw.strip().lower(), raw.strip().lower())
        if not norm:
            continue
        tokens = set(re.findall(r"[a-z]+", norm))
        for triggers, aat_tags in _MET_TAG_RULES:
            if any(
                trig == norm or (trig in tokens) or (" " in trig and trig in norm)
                for trig in triggers
            ):
                for tag in aat_tags:
                    _add(tag)
        if len(selected) >= max_tags:
            break

    return selected


def interleave_keyword_buckets(buckets: Sequence[Sequence[Any]], cap: int) -> List[Any]:
    """Interleave queued items across keyword buckets in round-robin order up to `cap`."""
    if cap <= 0 or not buckets:
        return []
    result: List[Any] = []
    max_len = max((len(b) for b in buckets), default=0)
    for idx in range(max_len):
        for bucket in buckets:
            if idx < len(bucket):
                result.append(bucket[idx])
                if len(result) >= cap:
                    return result
    return result


def score_worker_depiction(
    *,
    title: Optional[str] = None,
    description: Optional[str] = None,
    subject_tags: Optional[Sequence[Optional[str]]] = None,
    visual_alt_text: Optional[str] = None,
    object_name: Optional[str] = None,
    inscriptions: Optional[str] = None,
    material: Optional[str] = None,  # noqa: ARG001 - accepted for signature uniformity; intentionally excluded from positive scoring
) -> WorkerDepictionResult:
    """
    Score how strongly an artifact depicts an ancient worker or labor scene (0-100).

    Controlled depiction metadata (`subject_tags`), visual alt-text, cleaned titles,
    and scholarly descriptions contribute positive points; artist/maker attributions,
    manufacturing-technique terms, and plain utilitarian tools are suppressed.
    """
    raw_title = _safe_str(title)
    raw_object_name = _safe_str(object_name)
    raw_description = _safe_str(description)
    raw_alt = _safe_str(visual_alt_text)
    raw_inscr = _safe_str(inscriptions)

    clean_title = _scrub_noise(raw_title)
    clean_obj_name = _scrub_noise(raw_object_name)
    title_combined = " ".join(p for p in (clean_title, clean_obj_name) if p).strip()

    clean_visual = _scrub_noise(" ".join(p for p in (raw_alt, raw_description) if p))

    score = 0
    signals: List[str] = []

    def _add_signal(msg: str) -> None:
        if msg not in signals and len(signals) < 6:
            signals.append(msg)

    # 1. Controlled depiction subject tags (AAT / Wikidata P180 / AIC subject_titles / V&A contentPerson)
    matched_subject_tags: List[str] = []
    seen_subject_low: set[str] = set()
    for raw_tag in subject_tags or ():
        tag = _safe_str(raw_tag)
        if not tag:
            continue
        low_tag = tag.lower()
        if low_tag in seen_subject_low:
            continue
        tag_tokens = set(re.findall(r"[a-z]+", low_tag))
        if low_tag in _CONTROLLED_SUBJECT_TERMS or (tag_tokens & _CONTROLLED_SUBJECT_TERMS) or _WORKER_TERM_RE.search(tag):
            seen_subject_low.add(low_tag)
            matched_subject_tags.append(tag)
            if len(matched_subject_tags) >= 2:
                break

    if matched_subject_tags:
        score += 35 if len(matched_subject_tags) == 1 else 50
        for tag in matched_subject_tags:
            _add_signal(f"Subject tag: {tag}")

    # 2. Title & object_name depiction scoring
    has_title_depict_worker = False
    if title_combined:
        depict_match = _TITLE_DEPICT_WORKER_RE.search(title_combined)
        worker_match = _WORKER_TERM_RE.search(title_combined)
        workplace_match = _WORKPLACE_TERM_RE.search(title_combined)
        if depict_match and worker_match:
            has_title_depict_worker = True
            score += 45
            _add_signal(f"Title depicts worker: {worker_match.group(0).lower()}")
        elif worker_match:
            score += 35
            _add_signal(f"Title mentions worker: {worker_match.group(0).lower()}")
        elif depict_match and workplace_match:
            has_title_depict_worker = True
            score += 40
            _add_signal(f"Title depicts workplace: {workplace_match.group(0).lower()}")
        elif workplace_match:
            score += 30
            _add_signal(f"Title mentions workplace: {workplace_match.group(0).lower()}")

    # 3. Visual alt-text & description scoring
    has_desc_depict = False
    if clean_visual:
        phrase_match = _DESC_DEPICT_PHRASE_RE.search(clean_visual)
        if phrase_match:
            has_desc_depict = True
            score += 40
            _add_signal(f"Visual depiction: {phrase_match.group('term').lower()}")

        distinct_terms: List[str] = []
        for match in _WORKER_TERM_RE.finditer(clean_visual):
            term = match.group(0).lower()
            if term not in distinct_terms:
                distinct_terms.append(term)
            if len(distinct_terms) >= 2:
                break

        if distinct_terms:
            score += 22 if len(distinct_terms) == 1 else 34
            _add_signal(f"Catalog text: {distinct_terms[0]}")
        elif not phrase_match:
            wp_match = _WORKPLACE_TERM_RE.search(clean_visual)
            if wp_match:
                score += 15
                _add_signal(f"Workplace reference: {wp_match.group(0).lower()}")

    # 4. Figurative / narrative medium bonus (only boosts items that already show worker relevance)
    if score > 0:
        medium_context = " ".join(p for p in (title_combined, raw_alt, raw_description) if p)
        if _FIGURATIVE_MEDIUM_RE.search(medium_context):
            score += 10
            _add_signal("Figurative medium")

    # 5. Explicit occupational inscription evidence (excludes simple "made by" stamps)
    if raw_inscr and _OCCUPATIONAL_INSCRIPTION_RE.search(raw_inscr):
        score += 15
        _add_signal("Occupational inscription")

    # 6. Plain physical tool / implement suppression
    raw_title_plus_obj = " ".join(p for p in (raw_title, raw_object_name) if p).strip()
    is_single_tool_name = (
        raw_title.lower() in _GENERIC_SINGLE_TOOL_WORDS
        or raw_object_name.lower() in _GENERIC_SINGLE_TOOL_WORDS
    )
    looks_like_tool = bool(_PLAIN_TOOL_RE.search(raw_title_plus_obj) or is_single_tool_name)
    has_figurative_title = bool(_FIGURATIVE_MEDIUM_RE.search(title_combined))
    has_strong_depiction = bool(
        matched_subject_tags or has_title_depict_worker or has_desc_depict or has_figurative_title
    )

    is_plain_tool = False
    if looks_like_tool and not has_strong_depiction:
        is_plain_tool = True
        score = min(score, 20)
        signals = ["Plain tool/implement (no depicted worker)"] if score > 0 else []

    final_score = max(0, min(100, int(score)))
    if final_score >= 65:
        confidence: WorkerConfidence = "high"
    elif final_score >= 35:
        confidence = "medium"
    elif final_score > 0:
        confidence = "low"
    else:
        confidence = "none"

    return WorkerDepictionResult(
        score=final_score,
        confidence=confidence,
        signals=signals[:6],
        is_plain_tool=is_plain_tool,
    )
