# Profile artwork

Captured on 2026-11-23. Screenshots show public pages without submitting forms, uploading files, or accessing agency accounts.

| File | Source |
| --- | --- |
| `zenith-community.webp` | https://zenith-community.vercel.app/ |
| `shalvariq-photobooth.webp` | https://shalvariq-photobooth.vercel.app/custom |
| `powerless-generator.webp` | https://powerless-generator.vercel.app/ |

`header-dark.svg` and `header-light.svg` are original vector artwork for this profile. Their decorative traces animate once for four seconds, respect reduced motion where supported, and remain visible when animation is unavailable. SVG animation support on the published GitHub profile still needs verification after publication.

The Powerless screenshot reproduces the site's entertainment UI, including its satirical wording; it is not evidence of institutional endorsement. The Shalvariq page is a custom-frame order portal with checkout, not a free full-app demo.

No ERP screenshots are included because public deployment was unavailable and operational images may contain personal or agency data.

## Technology badges

`tech-*.svg` are locally stored Shields.io badges, fetched on 2026-11-23, using Simple Icons where available. Each badge names its technology and links to its documentation in the profile. Logos are embedded as SVG data URIs; rendering needs no live badge service. Java includes the Devicon Java logo from `devicons/devicon@v2.17.0`. JavaFX, Zustand, and Lenis use text badges where this source did not provide a logo. Rust, Electron, Tauri, Hono, and Tailscale reflect the profile owner's stated experience; other core tools were observed in project sources or manifests. Earlier fork/template dependencies are labeled separately.

## Contribution activity

`activity-dark.svg` and `activity-light.svg` are generated from GitHub's GraphQL contribution calendar, with the reporting period and UTC update timestamp embedded in each image. This is a contribution tracker, not a raw count of all commits. Counts depend on GitHub's contribution eligibility and the token's visibility; private repository names and details are not included.

`.github/workflows/activity.yml` refreshes the images daily and can be run manually once published to the default branch with Actions enabled. Until then these are locally generated snapshots. Failed data fetches preserve existing images. The animation is a decorative scanning effect, not an interactive game and not fabricated contributions.

Validation: `python3 tests/check_profile.py` and `python3 tests/check_activity.py`. GitHub's Markdown API is used for the local preview; published image-proxy rendering and scheduled Actions still need verification after push.
