<!-- Thanks for contributing to NetMedic! -->

## Summary

<!-- One or two lines describing what this PR does. -->

## Linked issue

<!-- "Closes #123", "Fixes #456", or "n/a" if it stands alone. -->

## Type of change

- [ ] Bug fix
- [ ] New feature
- [ ] Refactor / cleanup (no behavior change)
- [ ] Translation (new language or fix)
- [ ] Documentation only
- [ ] CI / build

## Testing

<!-- Show what you ran. For Windows-specific paths, paste the command + output. -->

```powershell
python -m compileall -q netmedic
python run.py status
```

## Checklist

- [ ] I ran `python -m compileall -q netmedic` cleanly.
- [ ] I updated `CHANGELOG.md` under the `[Unreleased]` section if behavior changed.
- [ ] If I added user-facing strings, I added their keys to **all** files under `locales/`.
- [ ] If I added a DNS provider, it is uncensored / unfiltered (per CONTRIBUTING.md).
- [ ] I am the original author of this contribution and license it under MIT.
