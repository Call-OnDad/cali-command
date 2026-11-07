"""
content_auditor.py - On-page SEO Content Analyzer, Keyword Density Checker,
Readability Scorer, and Schema.org JSON-LD Rich Snippet Generator.
"""

import json
import math
import re
from typing import Dict, List


class ContentAuditor:
    def __init__(self):
        pass

    def audit_content(
        self,
        text: str,
        target_keyword: str = "",
        title: str = "",
        meta_description: str = "",
        slug: str = ""
    ) -> Dict:
        """Performs a comprehensive SEO content audit on input text."""
        clean_text = text.strip()
        words = re.findall(r'\b[a-zA-Z0-9_\'-]+\b', clean_text.lower())
        word_count = len(words)

        sentences = re.split(r'[.!?]+', clean_text)
        sentences = [s.strip() for s in sentences if s.strip()]
        sentence_count = len(sentences) or 1

        syllable_count = sum(self._count_syllables(w) for w in words)

        # Flesch Reading Ease
        # 206.835 - 1.015 * (total words / total sentences) - 84.6 * (total syllables / total words)
        if word_count > 0:
            words_per_sent = word_count / sentence_count
            syll_per_word = syllable_count / word_count
            reading_ease = round(206.835 - (1.015 * words_per_sent) - (84.6 * syll_per_word), 1)
            reading_ease = max(0.0, min(100.0, reading_ease))
        else:
            reading_ease = 0.0

        if reading_ease >= 80:
            readability_label = "Very Easy (Conversational)"
        elif reading_ease >= 60:
            readability_label = "Standard / Accessible"
        elif reading_ease >= 45:
            readability_label = "Fairly Difficult (Technical)"
        else:
            readability_label = "Very Complex / Academic"

        # Keyword Analysis
        kw = target_keyword.strip().lower()
        kw_count = 0
        kw_density = 0.0
        kw_in_title = False
        kw_in_meta = False
        kw_in_slug = False
        kw_in_first_100 = False

        if kw and word_count > 0:
            kw_tokens = kw.split()
            kw_len = len(kw_tokens)
            if kw_len == 1:
                kw_count = words.count(kw)
            else:
                kw_count = clean_text.lower().count(kw)

            kw_density = round((kw_count * kw_len / word_count) * 100, 2)
            kw_in_title = kw in title.lower()
            kw_in_meta = kw in meta_description.lower()
            kw_in_slug = kw.replace(" ", "-") in slug.lower() or kw.replace(" ", "") in slug.lower()

            first_100_words = " ".join(words[:100])
            kw_in_first_100 = kw in first_100_words

        # Headings extraction
        h1_matches = re.findall(r'^#\s+(.+)$', clean_text, re.MULTILINE)
        h2_matches = re.findall(r'^##\s+(.+)$', clean_text, re.MULTILINE)
        h3_matches = re.findall(r'^###\s+(.+)$', clean_text, re.MULTILINE)

        # Content Score Calculation (0-100)
        score = 100
        checks = []

        # 1. Word count
        if word_count < 300:
            score -= 20
            checks.append({"status": "fail", "msg": f"Thin content ({word_count} words). Aim for at least 600+ words."})
        elif word_count < 600:
            score -= 10
            checks.append({"status": "warn", "msg": f"Moderate length ({word_count} words). 1000+ words rank higher."})
        else:
            checks.append({"status": "pass", "msg": f"Comprehensive content length ({word_count} words)."})

        # 2. Title Checks
        title_len = len(title)
        if not title:
            score -= 15
            checks.append({"status": "fail", "msg": "Missing SEO title."})
        elif title_len < 40 or title_len > 60:
            score -= 5
            checks.append({"status": "warn", "msg": f"Title length ({title_len} chars) is outside optimal 45-60 char range."})
        else:
            checks.append({"status": "pass", "msg": f"Optimal title length ({title_len} chars)."})

        # 3. Meta Description Checks
        desc_len = len(meta_description)
        if not meta_description:
            score -= 15
            checks.append({"status": "fail", "msg": "Missing meta description."})
        elif desc_len < 120 or desc_len > 160:
            score -= 5
            checks.append({"status": "warn", "msg": f"Meta description length ({desc_len} chars) outside optimal 130-155 range."})
        else:
            checks.append({"status": "pass", "msg": f"Optimal meta description length ({desc_len} chars)."})

        # 4. Target Keyword Checks
        if kw:
            if kw_in_title:
                checks.append({"status": "pass", "msg": "Target keyword present in title tag."})
            else:
                score -= 10
                checks.append({"status": "fail", "msg": "Target keyword missing from title tag."})

            if kw_in_meta:
                checks.append({"status": "pass", "msg": "Target keyword present in meta description."})
            else:
                score -= 5
                checks.append({"status": "warn", "msg": "Target keyword missing from meta description."})

            if kw_in_first_100:
                checks.append({"status": "pass", "msg": "Target keyword introduced in first 100 words."})
            else:
                score -= 8
                checks.append({"status": "warn", "msg": "Target keyword missing from opening paragraph."})

            if 1.0 <= kw_density <= 2.5:
                checks.append({"status": "pass", "msg": f"Healthy keyword density ({kw_density}%)."})
            elif kw_density < 1.0:
                score -= 5
                checks.append({"status": "warn", "msg": f"Low keyword density ({kw_density}%). Increase naturally."})
            else:
                score -= 10
                checks.append({"status": "fail", "msg": f"Keyword stuffing risk ({kw_density}%). Keep below 2.5%."})

        # 5. Headings Checks
        if len(h1_matches) == 1:
            checks.append({"status": "pass", "msg": "Exactly one H1 heading found."})
        elif len(h1_matches) == 0:
            score -= 10
            checks.append({"status": "warn", "msg": "No H1 heading found (# Heading)."})
        else:
            score -= 5
            checks.append({"status": "warn", "msg": f"Multiple H1 headings detected ({len(h1_matches)})."})

        if len(h2_matches) >= 2:
            checks.append({"status": "pass", "msg": f"Well-structured subheadings ({len(h2_matches)} H2 sections)."})
        else:
            score -= 5
            checks.append({"status": "warn", "msg": "Break content into more H2 subsections (## Heading)."})

        score = max(15, min(100, score))

        # Schema.org JSON-LD Generation
        schema_json_ld = self.generate_article_schema(
            title=title or "Cali Media Article",
            description=meta_description or clean_text[:150],
            url=f"https://cali-media.ltd/{slug}" if slug else "https://cali-media.ltd/"
        )

        return {
            "overall_score": score,
            "word_count": word_count,
            "readability": {
                "flesch_score": reading_ease,
                "label": readability_label,
                "sentences": sentence_count,
                "avg_words_per_sentence": round(words_per_sent if word_count > 0 else 0, 1)
            },
            "keyword_metrics": {
                "target_keyword": kw,
                "occurrences": kw_count,
                "density_percent": kw_density,
                "in_title": kw_in_title,
                "in_meta": kw_in_meta,
                "in_slug": kw_in_slug,
                "in_first_100": kw_in_first_100
            },
            "headings": {
                "h1": h1_matches,
                "h2": h2_matches,
                "h3": h3_matches
            },
            "checks": checks,
            "serp_preview": {
                "title": title or "Your Page Title Goes Here",
                "url": f"https://cali-media.ltd/{slug or 'example-post'}",
                "description": meta_description or (clean_text[:155] + "...")
            },
            "generated_schema": schema_json_ld
        }

    def generate_article_schema(self, title: str, description: str, url: str) -> Dict:
        """Generates standard Schema.org Article JSON-LD markup."""
        return {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": title,
            "description": description,
            "url": url,
            "author": {
                "@type": "Organization",
                "name": "Cali Media Limited",
                "url": "https://cali-media.ltd"
            },
            "publisher": {
                "@type": "Organization",
                "name": "Cali Media Group",
                "logo": {
                    "@type": "ImageObject",
                    "url": "https://cali-media.ltd/assets/logo.png"
                }
            }
        }

    def _count_syllables(self, word: str) -> int:
        w = word.lower().strip()
        if len(w) <= 3:
            return 1
        w = re.sub(r'(?:[^laeiouy]|ed|es|e)$', '', w)
        w = re.sub(r'^y', '', w)
        matches = re.findall(r'[aeiouy]{1,2}', w)
        return max(1, len(matches))
