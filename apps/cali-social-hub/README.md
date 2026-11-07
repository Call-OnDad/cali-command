# Cali Social Media & Publishing Hub (`apps/cali-social-hub`)

Standalone, decoupled social media management and publishing hub for Cali Media Group.
Modeled on **Postiz** and **Buffer**, powered by **Next-Gen Agent Echo**.

## Key Features

1. **Next-Gen Specialist Agent: Echo (Generation 2)**
   - Built with lessons learned from previous agent trajectories.
   - Strict platform character limit enforcement (e.g. Bluesky 300, TikTok 2,200, LinkedIn 3,000).
   - Brand voice calibration across `cali-media.ltd`, `call-on.dad`, `call-on.mom`, `call-on.media`, and `call-on.shop`.
   - Immutable evidence receipts generated for every broadcast (`REC-1762345000-xxxx`).

2. **Cross-Platform Coverage (9 Networks)**
   - TikTok (Shorts & Video)
   - YouTube Posts & Shorts
   - Facebook Reels & Pages
   - Instagram Reels & Posts
   - LinkedIn (Updates & Articles)
   - Pinterest (Pins & Infographics)
   - Bluesky (AT Protocol microblogging)
   - Mastodon (Fediverse microblogging)
   - Tumblr (Long & short form visual copy)

3. **Video Studio Asset Bridge**
   - Automatically connects to `apps/cali-video-studio/exports/`.
   - 1-click attachment of rendered mascot MP4s and thumbnails to social schedules.

4. **Visual Queue & Content Calendar**
   - Filter by brand or status (`Scheduled`, `Published`, `Draft`).
   - "Publish Now" broadcast trigger with live URL verification links.

## How to Launch

- **Double-click:** [`Launch-Social-Hub.cmd`](file:///d:/The%20Cali%20Project/apps/cali-social-hub/Launch-Social-Hub.cmd)
- **Port:** `http://127.0.0.1:8793`
