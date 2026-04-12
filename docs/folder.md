ai-api-security-system/
│
├── README.md
├── .env
├── docker-compose.yml
├── requirements.txt
│
├── docs/                              # 📄 Documentation
│   ├── SRS.md
│   ├── architecture.md
│   ├── diagrams.md
│   └── research_notes.md
│
├── backend/                           # 🚀 FastAPI Backend
│   ├── app/
│   │   ├── main.py                    # Entry point
│   │   │
│   │   ├── core/                      # ⚙️ Core configs
│   │   │   ├── config.py
│   │   │   ├── security.py            # API key/JWT validation
│   │   │   └── logging.py
│   │   │
│   │   ├── api/                       # 🌐 API routes
│   │   │   ├── routes/
│   │   │   │   ├── monitor.py         # traffic endpoints
│   │   │   │   ├── admin.py           # dashboard APIs
│   │   │   │   └── health.py
│   │   │   └── deps.py
│   │   │
│   │   ├── middleware/                # 🔍 Request interception
│   │   │   └── request_middleware.py
│   │   │
│   │   ├── identity/                  # 🧠 Identity Layer
│   │   │   ├── resolver.py            # API key/JWT extraction
│   │   │   └── signals.py             # IP, device, timing
│   │   │
│   │   ├── features/                  # 📊 Feature Engineering
│   │   │   └── feature_builder.py
│   │   │
│   │   ├── ml/                        # 🤖 ML Inference
│   │   │   ├── predictor.py
│   │   │   └── model_loader.py
│   │   │
│   │   ├── risk/                      # 📈 Risk Scoring
│   │   │   └── risk_engine.py
│   │   │
│   │   ├── policy/                    # ⚖️ Policy Engine
│   │   │   ├── decision_engine.py
│   │   │   └── penalty_manager.py
│   │   │
│   │   ├── explainability/            # 💬 Explainability Layer
│   │   │   └── explainer.py
│   │   │
│   │   ├── state/                     # ⚡ State Management
│   │   │   ├── redis_client.py
│   │   │   └── state_manager.py
│   │   │
│   │   ├── db/                        # 🧱 Database
│   │   │   ├── session.py
│   │   │   ├── base.py
│   │   │   └── models/
│   │   │       ├── user.py
│   │   │       ├── api_key.py         # minimal identity mapping
│   │   │       ├── request_log.py
│   │   │       ├── decision_log.py
│   │   │       └── feedback.py
│   │   │
│   │   ├── schemas/                   # 📦 Pydantic schemas
│   │   │
│   │   └── services/                  # 🧩 Orchestration logic
│   │       └── pipeline_service.py    # end-to-end flow
│   │
│   └── tests/
│
├── ml/                                # 🧠 Training & Self-Learning
│   ├── models/
│   │   ├── anomaly.pkl
│   │   └── classifier.pkl
│   │
│   ├── training/
│   │   ├── train.py
│   │   ├── retrain.py
│   │   └── online_learning.py
│   │
│   ├── data/
│   │   └── dataset.csv
│   │
│   └── features/
│       └── feature_pipeline.py
│
├── worker/                            # 🔄 Background Jobs
│   ├── tasks/
│   │   ├── retrain_task.py
│   │   └── aggregation_task.py
│   │
│   └── worker.py
│
├── frontend/                          # 🎨 React Dashboard
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Users.jsx
│   │   │   └── Logs.jsx
│   │   │
│   │   ├── components/
│   │   │   ├── TrafficChart.jsx
│   │   │   ├── RiskChart.jsx
│   │   │   ├── DecisionTable.jsx
│   │   │   └── UserProfile.jsx
│   │   │
│   │   ├── services/
│   │   │   └── api.js
│   │   │
│   │   └── hooks/
│   │
│   └── public/
│
├── scripts/                           # 🧪 Simulation & Utilities
│   ├── simulate_users.py
│   ├── simulate_attack.py
│   └── seed_data.py
│
├── infra/                             # ⚙️ DevOps
│   ├── docker/
│   ├── nginx/
│   └── configs/
│
└── tests/
    ├── backend/
    ├── ml/
    └── integration/