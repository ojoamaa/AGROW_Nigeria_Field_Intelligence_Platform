# GitHub and Render Release

1. Clone the existing GitHub repository.
2. Copy this package's contents into the cloned repository, preserving `.git`.
3. Copy your local `.env` only for testing; it is ignored by Git.
4. Run `python -m streamlit run app.py` and complete the acceptance test.
5. Create a release branch:

   git checkout -b release/agrownova-production-baseline-v1
   git add .
   git status
   git commit -m "Establish verified AgrowNova production baseline v1"
   git push -u origin release/agrownova-production-baseline-v1

6. Configure Render to deploy that branch.
7. Confirm Render environment variables match `.env.example`.
8. Deploy the latest commit and repeat the acceptance test on the public URL.
