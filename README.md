# Liminal

**在答案出现之前，先看见你如何观看。**
**Before the answer, notice how you see.**

Liminal is a bilingual, two-pass tarot reflection experiment. Pass 1 remains
question-blind and reads the participant's free association as a situated
meaning-making process. After the question is revealed, Pass 2 brings that
process, the card's structure, and the real decision together without treating
the card as prediction or the reading as diagnosis.

## Current status

- The contract-driven Pass 1 and Pass 2 engine is connected to DeepSeek and has
  passed the current human regression gate.
- A responsive Chinese/English display demo now covers the full interaction:
  landing page, card draw and orientation, typed or browser-supported speech
  input, Pass 1, question reveal, Pass 2, takeaway question, and contact footer.
- The demo API keeps the frozen Pass 1 session in memory only and returns only
  user-facing readings to the browser.
- This remains a local alpha. Production hosting, consent records, rate limits,
  persistent history, crisis resources, and field review of all tarot assets
  are not complete.

## Run the display demo

Create an ignored `.env.local` from `.env.example` and add the DeepSeek API key.
Then start the local reading service from the repository root:

```bash
.venv/bin/python -m engine.v2.demo_api
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. The Vite development server proxies `/api` to the
local reading service on `127.0.0.1:8787`.

## Repository map

- `frontend/` — bilingual React/Vite display demo and visual system
- `engine/v2/` — current staged model workflow, contracts, tests, and local demo API
- `engine/cards_*.json` — provisional runtime tarot records
- `engine/v2/data/rws_knowledge.json` — source-linked shadow knowledge base awaiting field review

Participant transcripts, questions, model outputs, and API keys must never be
committed to the public repository.
