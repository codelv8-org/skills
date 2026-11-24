# Community Skill Ratings & Reviews

The GitHub Pages catalog remains static. No OAuth client secret, PAT, or database is embedded in the browser.

## Submit a review
Open any skill's detail modal, expand the review form, select your actual AI agent, and give 1–5 stars in each of five dimensions. The overall score is their arithmetic mean. Continue to GitHub to sign in and **submit the public Issue**. The website does not submit it automatically. The text is optional, at most 500 characters. Never include PII, patient information, credentials, internal source data, or other secrets.

The issue title and the structured first lines are required. Use the catalog form for the correct skill ID and version. To revise a review, edit its original issue and ask for reapproval instead of submitting a duplicate.

## Maintainer setup (once)
In [Issues → Labels](https://github.com/codelv8-org/skills/labels), create exactly `skill-review-approved` (suggested color `0e8a16`). No separate external service or GitHub PAT is needed. Confirm Pages deployment via GitHub Actions and allow the standard workflow token to read issues.

## Moderation
Review each submission for format, real use, authentic version, spam, abuse, personal/sensitive data, and disclosure. Apply `skill-review-approved` **only after** approving the exact issue body. Removing the label withdraws the review. Edited issues (including edits in the same second as approval) are excluded until a maintainer removes/reapplies the label after rechecking. If multiple reviews by the same GitHub user ID for a skill/version are approved, the most recently approved wins. The latest version alone determines catalog ratings and ranking; historical versions and agent filters are available in the detail modal. GitHub accounts are authenticated, but actual skill usage is not independently verified.

Labels, relevant issue edits/deletions/transfers, pushes, manual dispatch, and a daily refresh rebuild the static dataset. This is eventually consistent, not real-time. If an issue is public, its original contents are public even before catalog approval; do not submit sensitive data. The JSON builder fails closed for missing approvals and fails the deployment on API errors instead of replacing existing scores with invented zeroes. A moderator should remove the label and redact/remove the original issue when necessary; GitHub Pages/CDN copies may remain briefly.

## Local development
Run `node --test scripts/skill-ratings.test.mjs` and `node --check assets/js/skill-reviews.js`. To build with real GitHub data, use a secure environment with read-only issues permission, `GITHUB_TOKEN`, and `GITHUB_REPOSITORY=codelv8-org/skills`. The deploy workflow sets these automatically. The checked-in JSON files intentionally contain no sample ratings. Review text is rendered using textContent, never injected as HTML.
