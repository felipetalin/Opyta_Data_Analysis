# GitHub Publish Checklist

## Local Repository State
- [x] Repository initialized
- [x] Main branch configured
- [x] Initial commit created
- [x] Release tag v0.1.0 created

## Security and Hygiene
- [x] .env ignored
- [x] .env.example present
- [x] No credentials hardcoded in source
- [x] .gitignore includes platform and Python artifacts

## Documentation
- [x] README updated with MVP status
- [x] CHANGELOG created
- [x] LICENSE created
- [x] CONTRIBUTING created
- [x] Release notes prepared (docs/RELEASE_v0.1.0.md)

## Publish Steps
1. Create an empty GitHub repository (no README, no license, no .gitignore)
2. Run:
   - ./scripts/publish_github.ps1 -RemoteUrl "https://github.com/<owner>/<repo>.git"
3. In GitHub UI, create release from tag v0.1.0
4. Paste notes from docs/RELEASE_v0.1.0.md
