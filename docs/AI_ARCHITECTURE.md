# AI Architecture

```text
User
  |
  v
Frontend / UI
  |
  v
Backend / API
  |
  v
ai/inference/service.py
  |
  +----------------------+----------------------+
  |                      |                      |
  v                      v                      v
Qwen3-0.6B         Qwen2.5-1.5B          SmolLM2-1.7B
HDFC + LoRA              Base                  Base
  |                      |                      |
  +----------------------+----------------------+
                         |
                         v
                  Common response
```

## AI source tree

```text
ai/
├── config/model/
├── inference/
│   ├── baseline.py
│   ├── finetuned.py
│   ├── generator.py
│   ├── loader.py
│   └── service.py       <-- application integration boundary
├── models/
├── training/
├── evaluation/
├── tests/
└── utils/
```

The application should depend primarily on `ai/inference/service.py`. Training and evaluation code are kept separate from normal inference.
