---
name: documentation-guardian
enabled: true
event: stop
pattern: .*
---

# 🛡️ DOCUMENTATION GUARDIAN

You are about to stop/complete a task. Before you do, ensure you have updated **README.md** with any relevant findings from this session.

### Check for:
- [ ] **New Architecture Patterns**: Did you implement a new pattern (e.g., Hookify rules)?
- [ ] **Environment Variables**: Are there new `GOOGLE_API_KEY` style variables required?
- [ ] **Known Issues**: Did you encounter any Windows-specific bugs (e.g., SSL handshakes)?
- [ ] **CLI Arguments**: Did you add flags like `--debug`?

**Why this matters:**
This project relies on precise, up-to-date technical documentation to prevent regression and help users navigate complex Windows-native constraints.

*This rule was implemented at the user's request to ensure persistent documentation quality.*
