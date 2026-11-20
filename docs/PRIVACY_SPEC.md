# PRIVACY SPEC

Applies to every mode, and is a hard gate for team mode.

## Principles

1. **Match, never rate.** Data is used to match people to work. No leaderboards, no "productivity" scores, no ranking people against each other.
2. **Transparent profiles.** Each person can see their full profile and the evidence behind it, and can correct or hide entries.
3. **Humans decide.** The tool suggests; a person assigns. No auto-assignment.
4. **Minimum data.** Only technical skills and work history relevant to matching. No personal attributes, no inference about health, background or personality.
5. **Growth by default.** A stretch dial and `want_to_learn` keep people from being pigeonholed into what they already do.

## Solo mode

- Only public GitHub data plus what the user types in.
- Profiles stored locally in `DATA_DIR`; `issuematch profile LOGIN --delete` removes them.

## Team mode (before it ships)

- CVs and Jira data are personal data. Check GDPR (and works-council rules in Germany) and any local law before processing.
- Consent and a clear notice of what is collected and why.
- Retention limit and deletion on request.
- Access control: a person sees their own profile; leads see matches, not raw evidence beyond what the person allows.
- Audit log of who viewed or changed a profile.

## Engineering rules

- Never log tokens or full CV text.
- Fixtures and eval sets are scrubbed of emails and private data.
