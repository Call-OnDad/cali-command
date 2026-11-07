# Canonical Locked-In Character Voice & Image Record

**Status:** Permanently Locked & Approved by Antony (Updated 2026-11-06).  
**Scope:** Universal 1-to-1 Voice and Image locks for all Cali Media videos, shorts, Google Flow animations, and website representations. All candidate picking, alternative auditions, and manual selection steps have been retired.

---

## The 7 Official Character Pairings (1 Voice = 1 Image)

| Character | Role & Department | Locked Voice | Locked 3D Render / Flow Frame | Locked Web Portrait |
| :--- | :--- | :--- | :--- | :--- |
| **Cali** | Command Lead & Operations | `cali.mp3` *(Jenny Dioco 1.0x)* | `locked_images/renders/cali.png` *(Reception Office)* | `locked_images/portraits/cali.webp` |
| **Arthur** | Methodical Auditor & Housing | `arthur.mp3` *(Kokoro natural 0.93x)* | `locked_images/renders/arthur.png` *(Desk & Office)* | `locked_images/portraits/arthur.webp` |
| **Hilda** | Family Care & Domestic Ops | `hilda.mp3` *(Late mum reference 0.85x)* | `locked_images/renders/hilda.png` *(Kitchen Office)* | `locked_images/portraits/hilda.webp` |
| **Trevor** | Maintenance & Tradesmen | `trevor.mp3` *(Audition Take 2 1.0x)* | `locked_images/renders/trevor.png` *(Workshop & Office)* | `locked_images/portraits/trevor.webp` |
| **Dexter** | Developer & Tech Safety | `dexter.mp3` *(Audition Take 3 1.06x)* | `locked_images/renders/dexter.png` *(Tech Desk & Monitors)* | `locked_images/portraits/dexter.webp` |
| **Odin** | Quality Overseer & Mascot | `odin.mp3` *(Michael Approved 0.96x)* | `locked_images/renders/odin.png` *(Office Bed)* | `locked_images/portraits/odin.webp` |
| **The Director** | Founder & Executive Vision | `the-director.mp3` *(Antony Clone 0.92x)* | `locked_images/renders/the_director.png` *(Approved Full-Body)* | `locked_images/portraits/the_director.webp` |

---

## Canonical Asset Repositories

1. **Locked Voice Masters:** `apps/cali-video-studio/locked_voices/` & `Local-video-studio/05-Voices/`
2. **Locked 3D Renders / Flow Frames:** `apps/cali-video-studio/locked_images/renders/` & `Local-video-studio/Images/Locked-Characters/renders/`
3. **Locked Web Portraits:** `apps/cali-video-studio/locked_images/portraits/` & `My Websites/media/assets/characters/crew/`
4. **Machine-Readable Manifest:** `LOCKED-CHARACTER-MANIFEST.json` and `LOCAL-VOICE-SELECTIONS.json`

---

## Production Rules

1. **1 Character = 1 Voice = 1 Image:** Tools and scripts must strictly pull the locked pair without prompting for manual selection.
2. **Loudness Mastering:** Normalized through FFmpeg to **`-16 LUFS`** dialogue streaming target with zero clipping before multiplexing.
3. **Consistent Representation:** The 3D render frame is the canonical starting frame for video pipelines; the Web portrait is the canonical headshot for websites and cards.

