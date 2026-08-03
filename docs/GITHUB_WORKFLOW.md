# AgrowNova GitHub Checkpoint Workflow

## Branches
- `main`: last verified stable version.
- `develop`: combined tested refinements.
- `feature/<name>`: one isolated feature or fix.

## First recovery checkpoint
After local testing passes:

```bash
git checkout -b recovery/stable-github-baseline
git add .
git commit -m "Recover and document stable AgrowNova GitHub baseline"
git push -u origin recovery/stable-github-baseline
```

Do not merge into `main` until the local checklist passes.

## Every later refinement
```bash
git checkout develop
git pull origin develop
git checkout -b feature/clear-feature-name
# make and test one controlled change
git add .
git commit -m "Describe the completed refinement"
git push -u origin feature/clear-feature-name
```

After verification, merge through GitHub and tag stable milestones:

```bash
git checkout main
git pull origin main
git tag -a v1.0.0-recovery -m "Verified AgrowNova recovery baseline"
git push origin v1.0.0-recovery
```
