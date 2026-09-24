# Noor Project Structure

```text
Noor/
├── .github/
│   └── workflows/
│       └── ci.yml
├── config/
│   ├── policy.yaml
│   ├── skills.yaml
│   └── tools.yaml
├── docs/
│   ├── AGILE_PROTOTYPING.md
│   ├── ARCHITECTURE.md
│   ├── MULTI_REPO.md
│   ├── PROJECT_MIND.md
│   ├── PROJECT_STRUCTURE.md
│   └── ROADMAP.md
├── src/
│   └── noor/
│       ├── __init__.py
│       ├── agent.py
│       ├── discovery.py
│       ├── executor.py
│       ├── mind.py
│       ├── models.py
│       ├── permissions.py
│       ├── selector.py
│       ├── verifier.py
│       ├── integrations/
│       ├── memory/
│       ├── skills/
│       ├── tools/
│       └── ui/
├── tests/
│   ├── test_mind.py
│   └── test_policy.py
├── .env.example
├── .gitignore
└── pyproject.toml
```

This is the initial scaffold. Feature implementations are added behind the boundaries rather than putting business logic into one monolithic agent file.
