# ODIN (Northeast Integrated Data Observatory) — Backend API

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)](https://fastapi.tiangolo.com/)
[![Poetry](https://img.shields.io/badge/Poetry-deps%20manager-1f6feb.svg)](https://python-poetry.org/)
[![MongoDB](https://img.shields.io/badge/DB-MongoDB-47A248.svg)](https://www.mongodb.com/)
[![Clean Architecture](https://img.shields.io/badge/Architecture-Clean%20Architecture-green.svg)](#architecture)
[![License](https://img.shields.io/badge/License-See%20LICENSE-informational.svg)](#license)

ODIN-Backend is the RESTful API for ODIN, built with FastAPI following Clean Architecture principles. Provides endpoints for accessing data processed by the ETL, dashboards, and analytics.


## 🏗️ Architecture (Clean Architecture)

server/
├── src/
│   ├── domain/
│   │   ├── entities/
│   │   │   └── school.py
│   │   ├── enums/
│   │   │   ├── enum_uf.py
│   │   │   └── enum_dependencies_administrativa.py
│   │   ├── repositories/
│   │   └── value_objects/
│   ├── application/
│   │   ├── use_cases/
│   │   └── dto/
│   ├── infrastructure/
│   │   ├── database/
│   │   │   └── mongodb_repositories.py
│   │   └── config/
│   └── presentation/
│       ├── api/
│       │   └── routes/
│       ├── controllers/
│       └── middleware/
├── tests/
├── pyproject.toml
├── poetry.lock
└── README.md


## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Poetry 1.6+
- MongoDB (local/Compose/Atlas)


## 🙏 Acknowledgments
Built by LEMA/UFPB to strengthen open, high-quality data infrastructure for the Northeast of Brazil.