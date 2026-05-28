frontend/
│
├── public/
│
├── src/
│   ├── assets/                  # Static assets
│   │   ├── icons/
│   │   ├── images/
│
│   ├── styles/                  # Global styling
│   │   ├── variables.css        # colors, spacing, theme tokens
│   │   ├── global.css           # base styles (body, reset)
│   │   ├── theme.css            # dark theme (your dashboard look)
│
│   ├── components/              # Reusable UI components
│   │   ├── DecisionTable/
│   │   │   ├── DecisionTable.jsx
│   │   │   └── DecisionTable.css
│   │   │
│   │   ├── RiskChart/
│   │   │   ├── RiskChart.jsx
│   │   │   └── RiskChart.css
│   │   │
│   │   ├── TrafficChart/
│   │   │   ├── TrafficChart.jsx
│   │   │   └── TrafficChart.css
│   │   │
│   │   ├── UserProfile/
│   │   │   ├── UserProfile.jsx
│   │   │   └── UserProfile.css
│   │   │
│   │   ├── Navbar/
│   │   │   ├── Navbar.jsx
│   │   │   └── Navbar.css
│   │   │
│   │   ├── Sidebar/
│   │   │   ├── Sidebar.jsx
│   │   │   └── Sidebar.css
│   │   │
│   │   ├── StatCard/
│   │   │   ├── StatCard.jsx
│   │   │   └── StatCard.css
│
│   ├── pages/                   # Page-level components
│   │   ├── Dashboard/
│   │   │   ├── Dashboard.jsx
│   │   │   └── Dashboard.css
│   │   │
│   │   ├── Logs/
│   │   │   ├── Logs.jsx
│   │   │   └── Logs.css
│   │   │
│   │   ├── User/
│   │   │   ├── User.jsx
│   │   │   └── User.css
│
│   ├── layouts/                 # Layout wrappers
│   │   ├── MainLayout.jsx       # Sidebar + Navbar + Content
│   │   └── MainLayout.css
│
│   ├── hooks/                   # Custom hooks
│   │   ├── useRealtime.js
│   │   ├── useFetch.js
│
│   ├── services/                # API layer
│   │   ├── api.js
│   │   ├── dashboardService.js
│   │   ├── userService.js
│
│   ├── utils/                   # Helpers
│   │   ├── format.js
│   │   ├── constants.js
│
│   ├── App.jsx
│   ├── main.jsx
│
├── package.json