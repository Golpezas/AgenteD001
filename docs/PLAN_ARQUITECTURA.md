# PLAN DE ARQUITECTURA — ASISTENTE COMERCIAL Y OPERATIVO

## Stack Tecnológico

| Capa | Tecnología | Versión |
|------|-----------|---------|
| Backend | FastAPI (Python) | 3.12+ |
| Frontend | React + TypeScript + Vite | |
| Base de Datos | PostgreSQL | 16+ |
| ORM | SQLAlchemy + Alembic | |
| Contenedor | Docker + docker-compose | |
| Notificaciones | WebSocket + SMTP + WhatsApp API | |

---

## Arquitectura General

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                         │
│  Dashboard │ Propuestas │ Tareas │ Clientes │ Precios       │
├─────────────────────────────────────────────────────────────┤
│                    API REST (FastAPI)                        │
├──────────┬──────────┬──────────┬──────────┬─────────────────┤
│ Data     │ Price    │ Proposal│ Task     │ Notif.           │
│ Ingestion│ Engine   │ Generator│ Manager  │ Service          │
│ (OCR,    │ (GAP     │ (PDF,   │ (State   │ (WS, Email,      │
│ Paste,   │ Analysis)│ Email,  │ Machine) │ WhatsApp)        │
│ Upload)  │          │ WApp)   │          │                  │
├──────────┴──────────┴──────────┴──────────┴─────────────────┤
│                       PostgreSQL                             │
│  clientes │ productos │ precios │ reglas │ tareas │ notifs   │
└─────────────────────────────────────────────────────────────┘
```

---

## Módulos del Sistema

### 1. Data Ingestion Layer
- **Pegado inteligente**: Texto copiado desde Excel, Bitrix24, Zeus ERP → parseo automático de campos
- **OCR en screenshots**: Subís captura → extracción de texto → alimenta al engine
- **Subida de archivos**: PDF, XLSX, TXT
- **Validación**: Reglas de validación antes de usar datos en cálculos

### 2. Price Engine (GAP Analysis)
- Catálogo de productos (ZEUS tiers, Balcony planes, add-ons)
- Precios con rangos de fecha (pre Sep 2025 vs post)
- Factores de cálculo de licenciamiento (x5, x2, x1, x6, x3)
- Reglas de descuento (10% Canal Digital, 20% Alianza, etc.)
- Políticas de negocio (precio asegurado 4 meses, permanencia mínima)
- **Lógica GAP**: Δ = Estado Solicitado (F) − Estado Actual (A+B)
- Solo cotizar diferencia técnica, no duplicar

### 3. Proposal Generator
- Templates estandarizados de propuesta económica
- Generación de PDF
- Borrador de Email listo para enviar
- Borrador de WhatsApp listo para enviar
- Historial de versiones de propuestas

### 4. Client Management
- CRUD completo de clientes/empresas
- Seguimiento histórico (deals, propuestas, contratos)
- Links a Bitrix24 CRM y Confluence
- Datos fiscales, representantes legales, verticales

### 5. Task Manager (State Machine)
- Ciclo de vida: PENDING → IN_PROGRESS → COMPLETED | CANCELLED
- Categorías: Email, WhatsApp, Bitrix24, Recotización
- Prioridades: Alta, Media, Baja
- Dashboard con métricas: completadas, pendientes, % avance
- Checklists dentro de tareas

### 6. Notification & Reminder System (CRÍTICO)
- **In-app**: Notificaciones en tiempo real vía WebSocket
- **Email**: Recordatorios programados vía SMTP
- **WhatsApp**: Alertas vía API (Twilio / WhatsApp Business)
- **Worker de fondo**: Revisa tareas cada N minutos
- **Escalamiento**: Si pasa deadline sin completar → alerta más insistente
- **Configurable**: Intervalos, canales, horarios de silencio

### 7. Integration Layer
- Bitrix24 API (estado de deals, campos personalizados)
- Email sending (SMTP)
- WhatsApp API
- PDF generation (WeasyPrint / ReportLab)

---

## Modelo de Datos (Esquema Alto Nivel)

### companies
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | UUID | PK |
| business_name | VARCHAR | Razón Social |
| cuit | VARCHAR | CUIT |
| legal_rep | VARCHAR | Representante Legal |
| dni | VARCHAR | DNI |
| fiscal_address | TEXT | Domicilio Fiscal |
| province | VARCHAR | Provincia |
| vertical | VARCHAR | Vertical (Ej: Pinturería) |
| client_type | VARCHAR | nuevo / actual |
| technology_tier | VARCHAR | Express / Advanced / Premium |
| lead_origin | VARCHAR | Origen del lead |
| executive | VARCHAR | Ejecutivo de Negocios |
| bitrix_url | TEXT | | |
| bitrix_id | VARCHAR | | |
| confluence_url | TEXT | | |
| created_at | TIMESTAMP | |

### products
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | UUID | PK |
| code | VARCHAR | BAL002, MPE002, etc. |
| name | TEXT | Nombre del producto |
| family | VARCHAR | Balcony, Zeus, MasPedidos, etc. |
| category | VARCHAR | monthly_fee, license, implementation, hours |

### price_list_items
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | UUID | PK |
| product_id | UUID | FK → products |
| price | DECIMAL | Monto |
| currency | VARCHAR | ARS / EUR |
| effective_from | DATE | |
| effective_to | DATE | nullable |
| is_partner_price | BOOLEAN | |
| is_new_client_price | BOOLEAN | Precios post Sep 2025 |

### pricing_rules
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | UUID | PK |
| name | VARCHAR | |
| rule_type | VARCHAR | discount / factor / policy / benefit |
| technology_tier | VARCHAR | Express / Advanced / Premium / all |
| conditions | JSONB | Condiciones de aplicación |
| value | DECIMAL | % o factor |
| description | TEXT | |

### deals
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | UUID | PK |
| company_id | UUID | FK → companies |
| status | VARCHAR | open / won / lost |
| deal_size | VARCHAR | "3 Total: 1 Full + 2 Pos" |
| total_amount | DECIMAL | |
| created_at | TIMESTAMP | |
| closed_at | TIMESTAMP | nullable |

### proposals
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | UUID | PK |
| deal_id | UUID | FK → deals |
| status | VARCHAR | draft / review / sent / accepted / rejected |
| gap_data | JSONB | Datos del análisis GAP |
| total_bruto | DECIMAL | |
| total_descuentos | DECIMAL | |
| total_final | DECIMAL | |
| payment_terms | TEXT | |
| validity_date | DATE | |
| pdf_path | TEXT | |
| email_draft | TEXT | |
| whatsapp_draft | TEXT | |
| created_at | TIMESTAMP | |
| version | INTEGER | |

### tasks
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | UUID | PK |
| company_id | UUID | FK → companies, nullable |
| deal_id | UUID | FK → deals, nullable |
| title | VARCHAR | |
| description | TEXT | |
| category | VARCHAR | email / whatsapp / bitrix24 / recotizacion / other |
| status | VARCHAR | pending / in_progress / completed / cancelled |
| priority | VARCHAR | high / medium / low |
| due_date | TIMESTAMP | |
| completed_at | TIMESTAMP | nullable |
| reminder_enabled | BOOLEAN | default true |
| reminder_interval_minutes | INTEGER | default 30 |

### notifications
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | UUID | PK |
| task_id | UUID | FK → tasks, nullable |
| channel | VARCHAR | in_app / email / whatsapp |
| status | VARCHAR | pending / sent / failed |
| sent_at | TIMESTAMP | nullable |
| error_message | TEXT | nullable |

### reminder_configs
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | UUID | PK |
| channel | VARCHAR | in_app / email / whatsapp |
| enabled | BOOLEAN | |
| interval_minutes | INTEGER | |
| quiet_hours_start | TIME | nullable |
| quiet_hours_end | TIME | nullable |

---

## Estructura de Directorios

```
agente-d/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # Entry point FastAPI
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── clients.py
│   │   │   ├── proposals.py
│   │   │   ├── tasks.py
│   │   │   ├── notifications.py
│   │   │   ├── knowledge_base.py
│   │   │   └── analytics.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── security.py
│   │   │   └── exceptions.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── company.py
│   │   │   ├── product.py
│   │   │   ├── price_list.py
│   │   │   ├── pricing_rule.py
│   │   │   ├── deal.py
│   │   │   ├── proposal.py
│   │   │   ├── task.py
│   │   │   └── notification.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── company.py
│   │   │   ├── proposal.py
│   │   │   ├── task.py
│   │   │   └── ...
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── gap_analysis.py        # Motor GAP Analysis
│   │   │   ├── price_engine.py        # Cálculo de precios
│   │   │   ├── proposal_generator.py  # Generación de propuestas
│   │   │   ├── task_manager.py        # State machine de tareas
│   │   │   ├── notification_service.py # Notificaciones multi-canal
│   │   │   ├── email_service.py
│   │   │   ├── whatsapp_service.py
│   │   │   ├── ocr_service.py         # OCR para screenshots
│   │   │   └── parser_service.py      # Parseo de texto pegado
│   │   └── workers/
│   │       ├── __init__.py
│   │       └── reminder_worker.py     # Worker de recordatorios
│   ├── migrations/                    # Alembic
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/                # Atomic design
│   │   │   ├── ui/                    # Atoms: Button, Input, Card, Modal
│   │   │   ├── layout/               # Shell, Sidebar, Header
│   │   │   ├── clients/              # ClientForm, ClientTable
│   │   │   ├── proposals/            # ProposalForm, ProposalPreview
│   │   │   ├── tasks/                # TaskCard, TaskList, TaskDashboard
│   │   │   └── notifications/        # NotificationBell, ReminderConfig
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Clients.tsx
│   │   │   ├── Proposals.tsx
│   │   │   ├── Tasks.tsx
│   │   │   ├── KnowledgeBase.tsx
│   │   │   └── Settings.tsx
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts
│   │   │   ├── useTasks.ts
│   │   │   └── useNotifications.ts
│   │   ├── services/
│   │   │   └── api.ts                 # API client
│   │   ├── store/                     # Estado global (Zustand/Redux)
│   │   ├── types/                     # TypeScript interfaces
│   │   └── App.tsx
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── docs/
│   ├── PLAN_ARQUITECTURA.md          # Este documento
│   ├── API.md                         # Documentación de endpoints
│   ├── DATABASE.md                    # Schema detallado
│   ├── BUSINESS_RULES.md              # Reglas de negocio documentadas
│   ├── USER_GUIDE.md                  # Guía de usuario
│   └── DEV_SETUP.md                   # Setup de desarrollo
├── .env.example
└── README.md
```

---

## Flujo de Datos Crítico

### GAP Analysis (Propuesta Económica)

```
1. INPUT: Usuario pega texto/sube captura con datos del cliente
   ├── Razón Social, CUIT, Representante
   ├── Setup Actual (A+B): qué tiene contratado hoy
   └── Setup Solicitado (F): qué quiere

2. PROCESO: Price Engine
   ├── Buscar cliente en BD (o crearlo)
   ├── Buscar productos/abonos actuales
   ├── Determinar si es pre/post Sep 2025
   ├── Calcular Δ = F − (A+B)
   ├── Aplicar factores de licenciamiento (x5, x2, etc.)
   ├── Aplicar descuentos vigentes
   └── Calcular fee mensual + licenciamiento

3. OUTPUT: Propuesta formateada
   ├── PDF de propuesta económica
   ├── Borrador de Email
   └── Borrador de WhatsApp
```

### Recordatorio de Tareas

```
1. Tarea creada con due_date y prioridad
2. Worker de fondo corre cada N minutos:
   ├── Revisa tareas PENDING con due_date próximo
   ├── Calcula tiempo restante
   └── Si está dentro de ventana de alerta:
       ├── In-app: WebSocket → notificación en dashboard
       ├── Email: SMTP → mail recordatorio
       └── WhatsApp: API → mensaje de alerta
3. Si pasa deadline:
   └── Escalar: cambiar prioridad, notificación más insistente
4. Usuario completa tarea → estado COMPLETED → no más alertas
```

---

## Plan de Implementación por Fases

### Fase 1: Fundación
**Objetivo**: Que el proyecto compile, corra en Docker, y tenga lo básico funcional.

- [ ] Setup Docker: FastAPI + React + PostgreSQL + Nginx (opcional)
- [ ] Backend: app base con health check, config, database session
- [ ] Backend: modelos SQLAlchemy + migración inicial Alembic
- [ ] Backend: CRUD de empresas/clientes (API REST)
- [ ] Backend: CRUD de productos y lista de precios
- [ ] Frontend: scaffold con Vite + React + TypeScript
- [ ] Frontend: layout base (sidebar, header, routing)
- [ ] Frontend: página de clientes (listar + crear)
- [ ] Frontend: página de productos/precios (listar)
- [ ] Documentación: DEV_SETUP.md, .env.example

### Fase 2: Motor de Precios
**Objetivo**: El núcleo del negocio funcionando.

- [ ] Backend: modelo pricing_rules + seed de reglas actuales
- [ ] Backend: PriceEngine service (factores, descuentos, políticas)
- [ ] Backend: GAP Analysis service (cálculo de delta)
- [ ] Backend: API de análisis (POST /api/gap-analysis)
- [ ] Frontend: form de análisis GAP (setup actual vs solicitado)
- [ ] Frontend: visualización de resultado del análisis
- [ ] Tests: unit tests del price engine

### Fase 3: Generador de Propuestas
**Objetivo**: Generar documentos listos para enviar.

- [ ] Backend: modelo proposals + versionado
- [ ] Backend: ProposalGenerator service
- [ ] Backend: generación de PDF con WeasyPrint/ReportLab
- [ ] Backend: generación de borrador de Email
- [ ] Backend: generación de borrador de WhatsApp
- [ ] Backend: API de propuestas (CRUD + generar)
- [ ] Frontend: editor/preview de propuestas
- [ ] Frontend: historial de propuestas por cliente

### Fase 4: Task Manager
**Objetivo**: Organizar el día a día operativo.

- [ ] Backend: modelo tasks + state machine
- [ ] Backend: TaskManager service (CRUD + transiciones)
- [ ] Backend: API de tareas
- [ ] Frontend: TaskDashboard con métricas y estados
- [ ] Frontend: TaskCard con acciones rápidas
- [ ] Frontend: filtros y búsqueda de tareas
- [ ] Frontend: checklists dentro de tareas

### Fase 5: Recordatorios (CRÍTICO)
**Objetivo**: Que no se te escape NADA.

- [ ] Backend: WebSocket manager para notificaciones en tiempo real
- [ ] Backend: EmailService (SMTP)
- [ ] Backend: WhatsAppService (Twilio/API)
- [ ] Backend: NotificationService (unifica canales)
- [ ] Backend: ReminderWorker (tarea programada con APScheduler / Celery)
- [ ] Backend: escalamiento de alertas por overdue
- [ ] Backend: API de notificaciones + configuración
- [ ] Frontend: NotificationBell con contador en vivo
- [ ] Frontend: configuración de preferencias de recordatorios
- [ ] Frontend: integración WebSocket para alerts en tiempo real

### Fase 6: Integración y Polish
**Objetivo**: Refinamiento profesional.

- [ ] Backend: integración API Bitrix24 (consultar deals)
- [ ] Backend: ParserService para texto pegado desde Excel/CRM
- [ ] Backend: OCR service (Tesseract) para screenshots
- [ ] Backend: importación masiva de datos históricos
- [ ] Frontend: responsive design completo (mobile-first)
- [ ] Frontend: modo offline / carga optimista
- [ ] Tests: integration tests + end-to-end
- [ ] Documentación: API.md, USER_GUIDE.md, BUSINESS_RULES.md
- [ ] Performance: caché, indexing, query optimization

---

## Reglas de Negocio Documentadas (Pendiente para BUSINESS_RULES.md)

- [ ] 20 políticas de comercio del documento "Politica zeus cloud erp.txt"
- [ ] Factores de cálculo por tecnología (Express / Advanced / Premium)
- [ ] Precios grandfathered (pre Sep 2025) vs nuevos
- [ ] Descuentos acumulables (Canal Digital 10%, Gestión Comercial 10%, Alianza 20%)
- [ ] Permanencia mínima: 6 meses (ampliaciones), 360 días (contratos)
- [ ] Precio asegurado: 4 meses para nuevos clientes
- [ ] Facturación: arranca en implementación (regla 24/48hs), prorrateo inicial
- [ ] Débito Automático Mandatorio
- [ ] Financiamiento: hasta 4 pagos sin interés, o 25% TF + 75% financiado IPC
- [ ] Beneficio Corporativo: 15% OFF vitalicio para MB10 (SAO MEDIALUNAS) en SUPERPOPI

---

## Notas de Arquitectura

### Patrones
- **Repository Pattern**: Capa de acceso a datos desacoplada
- **Service Layer**: Lógica de negocio en servicios, no en endpoints
- **DTOs (Pydantic)**: Validación en entrada y salida de datos
- **State Machine**: Tareas con transiciones explícitas y validación

### Seguridad
- Autenticación JWT (simple para single-user, extensible a multi-user)
- Variables de entorno para secrets (DB password, API keys)
- CORS configurado solo para frontend
- Validación de todos los inputs (Pydantic + SQLAlchemy)

### Performance
- Indexación en campos de búsqueda frecuente (CUIT, business_name, status)
- Conexión pool a PostgreSQL (SQLAlchemy pool_size configurable)
- WebSocket para notificaciones en tiempo real (evita polling)
- Worker de recordatorios separado del servidor web

### Portabilidad
- Docker compose para entorno completo
- Variables de entorno para configuración
- Migraciones automáticas con Alembic
- Seed data para precios y reglas iniciales

---

*Documento generado el 28/07/2026*
*Próxima sesión: Continuar con Fase 1 — Fundación*
