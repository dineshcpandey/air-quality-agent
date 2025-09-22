# Air Quality Q&A Agent

This project implements a multi-agent architecture for natural language querying of air quality data, using LangGraph orchestration and progressive enhancement from rule-based to LLM-powered agents.

## Project Structure

```
air-quality-agent/
├── src/
│   ├── agents/          # Query processing agents
│   ├── tools/           # Database tools
│   ├── graphs/          # LangGraph workflows  
│   ├── utils/           # Utilities (cache, db, etc)
│   ├── api/             # FastAPI endpoints
│   └── training/        # SLM data collection
├── config/              # Configuration files
├── tests/               # Test suite
├── docs/                # Documentation
├── scripts/             # Deployment scripts
├── logs/                # Application logs
├── data/                # Training data collection
└── README.md
```

## Implementation Plan & Progress
See `docs/implementation_progress.md` for the step-by-step plan, progress log, and deviations.

## Getting Started
1. Set up the development environment and install dependencies (see `requirements.txt`).
2. Follow the implementation plan in `docs/implementation_progress.md`.
3. Run tests in the `tests/` folder to validate agent functionality.

## Contact & Support
- Project Lead: [Your Name]
- Technical Questions: [Slack/Email]
- Documentation: See `docs/`

---

_Last updated: 21 Sep 2025_
