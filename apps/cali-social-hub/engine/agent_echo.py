"""
agent_echo.py - Next-Generation Social Media Specialist Agent.
Built on lessons learned: zero platform spam, strict character constraints,
authentic brand voices, and mandatory proof-of-work evidence logging.
"""

import json
import logging
import re
import time
from typing import Dict, List

logger = logging.getLogger("cali.social.echo")

BRAND_VOICES = {
    "call-on.dad": {
        "persona": "Arthur & Trevor (Practical, direct, consumer champion)",
        "tone": "No-nonsense, helpful, protective against utility traps, DIY repairs.",
        "hashtags": ["#CallOnDad", "#ConsumerRights", "#UKTrades", "#HandymanTips"]
    },
    "call-on.mom": {
        "persona": "Hilda (Warm, reassuring British home advice)",
        "tone": "Heartfelt, practical household budgeting, community care, smart savings.",
        "hashtags": ["#CallOnMom", "#FamilySavings", "#HomeBudgeting", "#SmartLiving"]
    },
    "cali-media.ltd": {
        "persona": "The Director & Cali (Autonomous media leadership)",
        "tone": "Confident, forward-thinking, emphasizing sovereign local software.",
        "hashtags": ["#CaliMedia", "#AutonomousTech", "#LocalVideo", "#DataSovereignty"]
    },
    "call-on.media": {
        "persona": "Dexter (Fast-paced creative coordinator)",
        "tone": "Snappy, engaging, visual storytelling, viral video pacing.",
        "hashtags": ["#CallOnMedia", "#ShortsCreator", "#VideoProduction", "#Storytelling"]
    },
    "call-on.shop": {
        "persona": "Crew Club (Official mascot merchandise)",
        "tone": "Fun, exclusive, apparel drops, community pride.",
        "hashtags": ["#CrewClub", "#MascotMerch", "#CaliShop", "#OfficialGear"]
    }
}

NETWORK_LIMITS = {
    "bluesky": 300,
    "mastodon": 500,
    "pinterest": 500,
    "tiktok": 2200,
    "instagram": 2200,
    "linkedin": 3000,
    "youtube_posts": 5000,
    "facebook": 63206,
    "tumblr": 10000
}


class AgentEcho:
    def __init__(self):
        self.name = "Echo"
        self.generation = 2
        self.role = "Omnichannel Social Publishing Specialist"

    def optimize_post(self, caption: str, network: str, brand: str) -> Dict:
        """
        Validates, formats and optimizes social copy according to network limits
        and brand guidelines, returning actionable warnings and character metrics.
        """
        limit = NETWORK_LIMITS.get(network, 2000)
        char_count = len(caption)
        brand_info = BRAND_VOICES.get(brand, BRAND_VOICES["cali-media.ltd"])

        warnings = []
        if char_count > limit:
            warnings.append(f"Caption exceeds {network} character limit ({char_count}/{limit} chars). Trim by {char_count - limit} chars.")
        elif char_count < 20:
            warnings.append("Caption is very brief. Consider adding a clear call-to-action or hook.")

        # Check hashtag presence
        existing_tags = re.findall(r'#\w+', caption)
        suggested_tags = [t for t in brand_info["hashtags"] if t.lower() not in [et.lower() for et in existing_tags]]

        return {
            "valid": len(warnings) == 0,
            "char_count": char_count,
            "char_limit": limit,
            "chars_remaining": max(0, limit - char_count),
            "warnings": warnings,
            "brand_voice": brand_info["persona"],
            "suggested_hashtags": suggested_tags[:4],
            "estimated_reading_seconds": max(2, round(char_count / 25))
        }

    def generate_variations(self, topic: str, brand: str) -> List[Dict]:
        """Generates tailored social copy variations across short, medium, and engaging styles."""
        brand_info = BRAND_VOICES.get(brand, BRAND_VOICES["cali-media.ltd"])
        tags = " ".join(brand_info["hashtags"][:3])

        return [
            {
                "style": "Direct & Punchy (Shorts / Bluesky / X)",
                "caption": f"{topic}\n\nHere is what you need to know today to stay ahead. Clean, actionable, and verified.\n\n{tags}"
            },
            {
                "style": "Storytelling & Context (LinkedIn / Facebook)",
                "caption": f"When it comes to {topic.lower()}, most people get caught off guard by the details.\n\nAt Cali Media, our philosophy is simple: complete transparency and zero unnecessary fluff. Keep your setup independent, verify the fine print, and protect your time.\n\nWhat is your experience with this?\n\n{tags}"
            },
            {
                "style": "Short-Form Video Hook (TikTok / Reels / YouTube)",
                "caption": f"⚠️ Don't make this mistake with {topic.lower()}!\n\nWatch till the end for the quick fix that saves you hours.\n\nFollow for more daily guides.\n\n{tags}"
            }
        ]
