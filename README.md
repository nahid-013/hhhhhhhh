HUNT — Полный production-ready проект (по ТЗ)
Формат: аккуратно по пунктам, технически полно и готово к реализации.Роль: вы — CTO/Lead; я — архитектор/lead backend, game designer и системный архитектор.

1. Краткий обзор (one-liner)
HUNT — Web3 Telegram Mini App на TON: игроки собирают, развивают, скрещивают и торгуют энергетическими существами — Спиритами (NFT). Игра сочетает Web3-экономику, F2P-механику, капсулы, breeding, энергию и 3-чел PvP мини-игры.

2. Высокоуровневая архитектура (production)
Используем next.js для mini app UI и внутренней админки.
Используем node.js для мультиплеерных игр.

3. Сервисы — краткий список + обязанности
1. Auth & Profile
    * Telegram mini_app onboarding, session management, referrals, bans, donations.
2. Game Core
    * Spirits templates, player_spirits, slots, boosts, capsules, inventory, breeding logic.
3. Matchmaking & Battles
    * 3-player battle_session, deterministic simulation + replay log, reward distribution.
4. Economy
    * Lumens accounting, TON payouts/withdraws, purchase flows (capsules, boosts, slots).
5. NFT / TON
    * Mint/burn/transfer, verify on-chain integrity, link nft_id ↔ player_spirits.
6. Admin
    * CRUD, drop rates, analytics, manual minting/rewards.
7. Workers
    * Celery tasks: energy tick, capsule opening, leaderboard updates, delayed payouts.

4. Сущности — ER / SQL схемы (Postgres)
Далее — SQL DDL (упрощённый и production-ready: constraints, FKs, индексы, timestamps).Все timestamp поля TIMESTAMP WITH TIME ZONE DEFAULT now().
4.1. Общие lookup таблицы
CREATE TABLE elements (
  id SERIAL PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,
  name_ru TEXT,
  name_en TEXT,
  icon_url TEXT
);

CREATE TABLE rarities (
  id SERIAL PRIMARY KEY,
  code TEXT UNIQUE NOT NULL, -- common, rare, epic, legendary, mythical
  name_ru TEXT,
  name_en TEXT,
  icon_url TEXT,
  power_factor NUMERIC DEFAULT 1.0 -- balance helper
);
4.2. Users + related
CREATE TABLE users (
  tg_id BIGINT PRIMARY KEY,
  user_name TEXT,
  first_name TEXT,
  last_name TEXT,
  ton_address TEXT,
  ton_balance NUMERIC DEFAULT 0,
  lumens_balance NUMERIC DEFAULT 1000,
  referral_code TEXT UNIQUE NOT NULL,
  referraled_by BIGINT REFERENCES users(tg_id),
  referrals_count INTEGER DEFAULT 0,
  is_banned BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  is_admin BOOLEAN DEFAULT FALSE,
  language TEXT,
  onboarding_step TEXT,
  donate_amount NUMERIC DEFAULT 0,
  last_active TIMESTAMPTZ DEFAULT now()
);
CREATE UNIQUE INDEX idx_users_ton_address ON users(ton_address);
CREATE TABLE bans (
  id SERIAL PRIMARY KEY,
  tg_id BIGINT REFERENCES users(tg_id) ON DELETE CASCADE,
  reason TEXT,
  banned_at TIMESTAMPTZ DEFAULT now(),
  expires_at TIMESTAMPTZ
);
CREATE TABLE donations (
  id SERIAL PRIMARY KEY,
  tg_id BIGINT REFERENCES users(tg_id) ON DELETE CASCADE,
  amount NUMERIC NOT NULL,
  currency TEXT NOT NULL, -- TON/LUMENS etc
  donated_at TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE wallets (
  id SERIAL PRIMARY KEY,
  tg_id BIGINT REFERENCES users(tg_id),
  address TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(address)
);
4.3. Spirits (templates + player)
CREATE TABLE spirits_template (
  id SERIAL PRIMARY KEY,
  code TEXT UNIQUE,
  element_id INT REFERENCES elements(id),
  rarity_id INT REFERENCES rarities(id),
  name_ru TEXT,
  name_en TEXT,
  generation INT DEFAULT 1,
  default_level INT DEFAULT 1,
  default_xp_for_next INT DEFAULT 100,
  description_ru TEXT,
  description_en TEXT,
  base_run INT DEFAULT 1,
  base_jump INT DEFAULT 1,
  base_swim INT DEFAULT 1,
  base_dives INT DEFAULT 1,
  base_fly INT DEFAULT 1,
  base_maneuver INT DEFAULT 1,
  base_max_energy INT DEFAULT 100,
  icon_url TEXT,
  spirit_animation_url TEXT,
  capsule_id INT REFERENCES capsule_template(id),
  is_starter BOOLEAN DEFAULT FALSE,
  is_available BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
capsule_template forward ref — defined later. In actual migrations order accordingly.
CREATE TABLE player_spirits (
  id BIGSERIAL PRIMARY KEY,
  owner_id BIGINT REFERENCES users(tg_id) ON DELETE CASCADE,
  spirit_template_id INT REFERENCES spirits_template(id) ON DELETE SET NULL,
  custom_name TEXT,
  generation INT DEFAULT 1,
  level INT DEFAULT 1,
  xp_for_next_level INT DEFAULT 100,
  xp INT DEFAULT 0,
  description_ru TEXT,
  description_en TEXT,
  base_run INT DEFAULT 1,
  base_jump INT DEFAULT 1,
  base_swim INT DEFAULT 1,
  base_dives INT DEFAULT 1,
  base_fly INT DEFAULT 1,
  base_maneuver INT DEFAULT 1,
  base_max_energy INT DEFAULT 100,
  energy INT DEFAULT 100,
  is_active BOOLEAN DEFAULT FALSE,
  slot_id BIGINT REFERENCES player_slots(id),
  is_minted BOOLEAN DEFAULT FALSE,
  nft_id TEXT, -- ton NFT address / token id
  acquired_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_player_spirits_owner ON player_spirits(owner_id);
4.4. Capsule templates + player capsules
CREATE TABLE capsule_template (
  id SERIAL PRIMARY KEY,
  code TEXT UNIQUE,
  element_id INT REFERENCES elements(id),
  rarity_id INT REFERENCES rarities(id),
  name_ru TEXT,
  name_en TEXT,
  open_time_seconds INT DEFAULT 0,
  price_in_ton NUMERIC DEFAULT 0,
  price_lumens NUMERIC DEFAULT 0,
  icon_url TEXT,
  capsule_animation_url TEXT,
  is_available BOOLEAN DEFAULT TRUE,
  amount INT DEFAULT 0, -- how many left for sale
  fast_open_cost NUMERIC DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE player_capsules (
  id BIGSERIAL PRIMARY KEY,
  owner_id BIGINT REFERENCES users(tg_id) ON DELETE CASCADE,
  capsule_id INT REFERENCES capsule_template(id) ON DELETE SET NULL,
  quantity INT DEFAULT 1,
  is_opened BOOLEAN DEFAULT FALSE,
  is_opening BOOLEAN DEFAULT FALSE,
  opening_started_at TIMESTAMPTZ,
  opening_ends_at TIMESTAMPTZ,
  acquired_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_player_capsules_owner ON player_capsules(owner_id);
4.5. Slots templates + player slots
CREATE TABLE slots_template (
  id SERIAL PRIMARY KEY,
  element_id INT REFERENCES elements(id),
  price_lumens NUMERIC DEFAULT 0,
  sell_price_lumens NUMERIC DEFAULT 0,
  is_starter BOOLEAN DEFAULT FALSE,
  icon_url TEXT,
  is_available BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE player_slots (
  id BIGSERIAL PRIMARY KEY,
  owner_id BIGINT REFERENCES users(tg_id) ON DELETE CASCADE,
  slot_template_id INT REFERENCES slots_template(id),
  element_id INT REFERENCES elements(id),
  acquired_at TIMESTAMPTZ DEFAULT now(),
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_player_slots_owner ON player_slots(owner_id);
4.6. Boosts templates + player boosts
CREATE TABLE boost_template (
  id SERIAL PRIMARY KEY,
  internal_name TEXT,
  name_ru TEXT,
  name_en TEXT,
  description_ru TEXT,
  description_en TEXT,
  price_ton NUMERIC DEFAULT 0,
  boost_xp INT DEFAULT 0,
  amount INT DEFAULT 0,
  icon_url TEXT,
  is_available BOOLEAN DEFAULT TRUE,
  sort_order INT
);

CREATE TABLE player_boosts (
  id BIGSERIAL PRIMARY KEY,
  owner_id BIGINT REFERENCES users(tg_id) ON DELETE CASCADE,
  boost_id INT REFERENCES boost_template(id),
  quantity INT DEFAULT 1,
  acquired_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
4.7. Battle / Matchmaking / Logs
CREATE TABLE battle_sessions (
  id BIGSERIAL PRIMARY KEY,
  mode TEXT, -- e.g. flow_flight ...
  started_at TIMESTAMPTZ DEFAULT now(),
  finished_at TIMESTAMPTZ,
  result_json JSONB, -- stored replay/outcome
  created_by BIGINT REFERENCES users(tg_id)
);

CREATE TABLE battle_players (
  id BIGSERIAL PRIMARY KEY,
  battle_session_id BIGINT REFERENCES battle_sessions(id) ON DELETE CASCADE,
  player_id BIGINT REFERENCES users(tg_id),
  player_spirit_id BIGINT REFERENCES player_spirits(id),
  stats JSONB,
  score NUMERIC,
  rank INT
);
4.8. Economy logs & withdrawals
CREATE TABLE balance_logs (
  id BIGSERIAL PRIMARY KEY,
  tg_id BIGINT REFERENCES users(tg_id),
  change NUMERIC,
  currency TEXT,
  reason TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE withdrawals (
  id BIGSERIAL PRIMARY KEY,
  tg_id BIGINT REFERENCES users(tg_id),
  amount NUMERIC,
  currency TEXT,
  status TEXT DEFAULT 'pending', -- pending/processing/completed/rejected
  created_at TIMESTAMPTZ DEFAULT now(),
  processed_at TIMESTAMPTZ
);

5. ER-диаграмма (текстовое описание)
* users 1 — N → player_spirits, player_capsules, player_slots, player_boosts, donations, bans, balance_logs.
* elements 1 — N → spirits_template, capsule_template, slots_template.
* rarities 1 — N → spirits_template, capsule_template.
* spirits_template 1 — N → player_spirits.
* capsule_template 1 — N → player_capsules.
* slots_template 1 — N → player_slots.
* player_spirits N — 1 → player_slots via slot_id.
* battle_sessions 1 — N → battle_players.
(при необходимости — визуальная схема через dbdiagram / draw.io в артефакте проекта)

6. Файловая структура (предложение)
/hunt/
├─ docker-compose.yml
├─ /services/
│  ├─ /auth_service/       # FastAPI
│  ├─ /game_service/       # FastAPI
│  ├─ /matchmaking_service # FastAPI + websockets
│  ├─ /economy_service     # FastAPI + TON integration
│  ├─ /nft_service         # TON mint/burn/transfer
│  ├─ /admin_service
│  └─ /shared/             # libs: db, schemas, models, utils
├─ /workers/
│  └─ celery_worker/
├─ /infra/
│  ├─ k8s/                 # manifests
│  ├─ nginx/
│  └─ terraform/           # optional
├─ /migrations/            # alembic
├─ /scripts/
├─ /docs/
│  ├─ ER_diagram.png
│  └─ API_specs.md
└─ README.md

7. Game logic — сущности и правила (подробно)
7.1. Спирит (описание)
* NFT: уникальная сущность.
* Атрибуты: element, rarity, generation, level, xp, stats = {run, jump, swim, dives, fly, maneuver, max_energy}.
* energy — текущая энергия; max_energy → базируется на template + generation bonus.
* is_active — в активной команде (требует слот подходящей стихии).
7.2. Стихии
* Набор: fire, water, earth, air, light, dark (пример). Каждая стихия влияет на совместимость слотов/капсул.
7.3. Редкости
* common < rare < epic < legendary < mythical
* Rarity влияет на базовую силу, шанс в капсулах, цену mint, лимит капсул.
7.4. Капсулы
* CapsuleTemplate привязан к элементу и редкости.
* Открытие занимает open_time_seconds. Если игрок платит fast_open_cost (TON или Lumens) — открывается моментально.
* Дроп: набор spirits_template с capsule_id = capsule_template.id. Редкость капсулы ограничивает возможный дроп.
7.5. Слоты
* Каждый слот имеет element_id. Starter slots free.
* Player can buy additional slots (lumens).
* Slot можно продать (sell_price_lumens) → lumens balance.
7.6. Boosts
* Consumable, даёт boost_xp при использовании на spirit.
7.7. Breeding (скрещивание)
Условия:
* Родители: same element (element_id equal).
* Родители: одного и того же spirit_template (спирит = одинаковый код / template).
* Оба уровня = 10.
* Стоимость: фиксированная TON (configurable) + burn fees (люмены).
* Родители сжигаются (burn) → удаляются / помечаются как burned; TON списывается.
* Формула:
    * generation = min(gen_parent1, gen_parent2) + 1
    * stats = max(parent stats, min_stats_for_generation)
    * rarity = max(parent rarity)
* Минимальные статы (table):
    * gen1: 1/1/1/1/1/1
    * gen2: 3/3/3/3/3/3
    * gen3: 5/5/5/5/5/5
    * gen4: 8/8/8/8/8/8
    * gen5: 10/10/10/10/10/10
    * gen6: 12/12/12/12/12/12
    * gen7: 15/15/15/15/15/15
* Новый spirit создаётся как player_spirit с generation, level=1, xp=0, base_stats вычислены как описано.
* NFT: новый спирит не сминтится автоматически (опция — mint on creation for TON fee).
7.8. Energy System
* Каждый action требует energy (например, гонка: 15 energy).
* max_energy берётся из spirit.base_max_energy + generation modifier (например +5 per gen).
* Восстановление: +5 energy каждые 10 минут.
    * Реализация: Redis + Celery tick (cron every 10 minutes) → for each active spirit or each player? Design: per-player aggregate: restore to each spirit up to its max.
    * Redis stores energy_lock and last_tick.
* Instant restore: оплата TON/Lumens → происходит мгновенно (worker verifies payment, updates energy, logs anti-fraud).
* Limits: prevent scripts — rate limiting + server side checks (max restore per hour, suspicious patterns flagged).
7.9. Mini-games PvP (3 игрока)
* Общая идея: матчмейкер собирает 3 игроков, фиксирует player_stats (derived from spirit stats + random seed + power_modifiers), запускает deterministic simulation server-side, сохраняет replay JSON.
* Каждая мини-игра:
    1. Flow Flight — runner/obstacle: key stats {maneuver, flow, reaction}; winner = max(distance).
    2. Deep Dive — vertical depth: {dives, swim/flow}; winner = min(depth value (bigger depth)).
    3. Rhythm Path — QTE: {reaction, impulse}; winner = max(accuracy*speed).
    4. Jump Rush — platform jumps: {maneuver, reaction}; winner = max(distance + combos).
    5. Collecting Frenzy — collect items: {flow, maneuver}; winner = items_collected.
* Reward logic: ranked rewards (1st/2nd/3rd), experience to spirits, lumens/TON depending on mode (free/paid), capsule drops probabilistic.
* Deterministic server simulation: uses a PRNG seed per battle_session (stored) → reproducible results for audits.

8. API — список эндпоинтов, JSON контрактов, параметры, валидации и бизнес-логика
Общие: все ответы в формате JSON: { "ok": bool, "data": {...}, "error": {"code": "...", "message": "..."} }Авторизация: JWT + Telegram signed payload header X-Tg-Signed. Проверка на backend.

/api/v1/profile
GET /api/v1/profile
Описание: получить профиль текущего игрока.Auth: required.Response 200
{
  "ok": true,
  "data": {
    "tg_id": 123456,
    "user_name": "player",
    "first_name": "Ivan",
    "last_name": "Petrov",
    "ton_address": "...",
    "ton_balance": "1.25",
    "lumens_balance": "500",
    "referral_code": "ABCD12",
    "referrals_count": 3,
    "onboarding_step": "completed",
    "donate_amount": "0.5",
    "last_active": "2025-12-07T12:34:56Z"
  }
}
Errors
* 401 unauthorized
* 429 rate limit
PATCH /api/v1/profile
Body
{
  "language": "ru",
  "first_name": "Ivan",
  "last_name": "Petrov",
  "user_name": "ivan_p"
}
Logic
* Validate changes; username unique (if changing).
* Update updated_at.
* Return updated profile.
DELETE /api/v1/profile
Logic
* Soft delete (set is_banned=true? or mark deleted flag).
* Requires admin confirmation for full deletion (endpoint reserved for admin).
Wallet management
* POST /api/v1/profile/wallet/connect — body: { "ton_address": "EQ..." } → validate address (TON SDK / checksum), store in wallets, update users.ton_address. If duplicate: flag multiaccount risk, increment suspicion_score.
* POST /api/v1/profile/wallet/change — change wallet (requires OTP / transaction signature).
* POST /api/v1/profile/wallet/deposit_link — returns a TON deposit address or payment link.
* POST /api/v1/profile/wallet/withdraw — body { amount, currency, to_address }:
    * Checks: min withdraw TON >= 10 TON required in business rules, available balance check, KYC checks (if needed), withdrawal delay (anti-fraud), add withdrawal entry pending, enqueue processing.
* GET /api/v1/profile/wallet/transactions — paginated.
Onboarding endpoints:
* POST /api/v1/profile/onboarding/step — set onboarding_step, accept referral code (apply rewards: +1000 lumens to inviter and invitee, milestone logic for TON rewards).
* Business logic: referral credit immediate for Lumens, TON rewards on milestones (automated via worker).
Donations:
* GET /api/v1/profile/donations
* POST /api/v1/profile/donate — process TON donation via TON SDK, record in donations, apply referral commission (10%) to referrer.

/api/v1/admin/users
* GET /api/v1/admin/users — filters: tg_id, wallet, is_banned, pagination, sort.
* GET /api/v1/admin/users/{tg_id} — full profile + logs.
* PATCH /api/v1/admin/users/{tg_id} — edit (ban/unban, set balances).
* POST /api/v1/admin/users/{tg_id}/ban — body { reason, expires_at } → creates bans row, sets is_banned true.
* POST /api/v1/admin/users/{tg_id}/grant_lumens — admin grant.
* POST /api/v1/admin/users/{tg_id}/mint_spirit — mint specific spirit to user (create player_spirit + optionally mint NFT).
* Errors/Checks: RBAC (is_admin), audit logging.

/api/v1/spirits
GET /api/v1/spirits/catalog
Params: element_id, rarity_id, page, size, searchResponse: list of spirits_template with summary fields: id, name, rarity, element, base stats, icon_url.
GET /api/v1/spirits/my
Response: list player_spirits belonging to user (inactive & active), incl. energy, stats, is_minted flag.
GET /api/v1/spirits/active
Response: current active party (slots + assigned spirits).
POST /api/v1/spirits/{player_spirit_id}/activate
Body: { "slot_id": 123 }Logic:
* Validate slot.element_id == player_spirit.element_id
* Slot free? assign spirit to slot (update player_spirits.is_active=true, slot_id set).
* If slot occupied: error 409 or add swap flow.Errors: 400 invalid compatibility, 403 slot not owned, 404 spirit not found.
POST /api/v1/spirits/{player_spirit_id}/mint
Logic:
* Validate ownership, is_minted==false.
* Charge TON mint fee (config).
* Call NFT Service to mint → returns nft_id → set is_minted=true, nft_id.
* On blockchain success only mark minted.
POST /api/v1/spirits/{player_spirit_id}/burn
Logic:
* Check ownership and burn permissions.
* If parent used in breeding, ensure rules.
* If minted: call NFT burn (on-chain), set is_minted=false, nft_id=null, then delete or mark as burned.
* Charge small lumens fee to burn.
POST /api/v1/spirits/breed
Body:
{
  "parent1_id": 111,
  "parent2_id": 222,
  "pay_with": "TON"
}
Logic (breeding full flow):
1. Validate both owners = current user.
2. Validate same element, same spirit_template_id, both level == 10.
3. Validate breeding cost (TON) present in user's balance; subtract TON.
4. Compute child generation = min(gen1, gen2) + 1.
5. Compute child's stats:
    * for each stat: max(parent_stat, min_stat_for_generation)
6. Rarety = max(rarity_parent1, rarity_parent2).
7. Create new player_spirit (is_minted=false).
8. Burn parents: if minted → call NFT burn; mark player_spirits deleted or flagged burned=true and remove ownership; update logs.
9. Emit event + audit log.Response 200: newly created spirit.
Errors/Checks: parents levels, element, ownership, funds, rate limiting per hour.

/api/v1/admin/spirits
* CRUD on spirits_template (create, update recalc).
* Endpoint to set capsule drop tables: e.g. POST /api/v1/admin/spirits/drops body: { capsule_id: 10, spirit_template_id: 200, weight: 100 }.
* Endpoint to adjust global balancing factors.

/api/v1/capsules
GET /api/v1/capsules/shop
Returns: grouped by element, then by rarity. For each capsule: { id, name, icon_url, price_ton, price_lumens, amount_left, open_time_seconds }.
POST /api/v1/capsules/buy
Body: { "capsule_id": 10, "quantity": 1, "pay_with": "lumens" }Logic:
* Validate inventory (capsule_template.amount).
* Charge user -> decrease lumens/TON.
* Create or increment player_capsules row.
* Log balance_logs.
* Return updated inventory.
GET /api/v1/capsules/my
* List player_capsules for user.
POST /api/v1/capsules/{player_capsule_id}/open
Logic:
* Validate ownership and that capsule not already opening.
* If open_time_seconds == 0 -> resolve immediately: pick drop via weighted random from spirits_template where capsule_id matches. Create player_spirit for user, decrement player_capsules.quantity (or delete).
* If >0 -> set is_opening=true, opening_started_at=now, opening_ends_at = now + seconds, enqueue Celery task to finish opening.
* Fast open: POST /fast_open — pay fast_open_cost (TON or Lumens), resolve immediately.
* On resolve: create player_spirit, persist, return new spirit summary.
Probability logic
* Drop weights based on rarity & capsule rarity. Example: capsule rarity X cannot drop spirits with rarity > capsule.rarity.
Errors: insufficient balance, capsule sold out, illegal open (mismatch owner).
/api/v1/admin/capsules
* CRUD for capsule_template
* Endpoint to set drop rates (mapping capsule_template → spirits_template with weight).
* Admin open (force).

/api/v1/slots
GET /api/v1/slots/templates
* Returns slots_template for purchase.
POST /api/v1/slots/buy
Body: { "slot_template_id": 2 }Logic:
* Charge lumens, create player_slot entry.
* If slot_template.is_starter -> disallow buy (already assigned).
POST /api/v1/slots/sell
Body: { "player_slot_id": 22 }Logic:
* Validate ownership, slot empty (no spirit assigned).
* Credit sell_price_lumens.
GET /api/v1/slots/party
* Return active party: slots + assigned spirits.
/api/v1/admin/slots
* CRUD.

/api/v1/boosts
GET /api/v1/boosts/shop
* Return list of boost_template.
POST /api/v1/boosts/buy
Body: { "boost_id": 1, "qty": 1 }Logic: charge lumens/ton, create/increment player_boosts row.
GET /api/v1/boosts/my
* Inventory.
POST /api/v1/boosts/{player_boost_id}/use
Body: { "player_spirit_id": 333 }Logic:
* Validate ownership, quantity, target spirit owner match.
* Apply boost_xp to target spirit (increase xp, level up if xp >= xp_for_next_level; recalc next xp).
* Reduce quantity.
* Return updated spirit.

9. Matchmaking & Battle Logic (detailed)
9.1. Matchmaking
* Queue per mode, skill matching by power_score = sum(stats * rarity_factor) + ELO / recent_winrate.
* When 3 players matched → create battle_session with seed, lock involved player_spirits, set cooldown on spirits (prevent concurrent participation).
* Notify players via websocket.
9.2. Battle flow
* On session start: fetch player stats (base stats + items/boosts), build deterministic player state.
* Run simulation server-side (no client trust). Use deterministic rules per mini-game (seeded RNG).
* After simulation, compute rank (1/2/3), assign rewards:
    * XP to spirit (tiered)
    * Lumens to players (scaled)
    * Chance to drop capsule (low probability)
* Save result_json (replay) + battle_players records.
* Unlock spirits and update energy (deduct 15 per race).
9.3. Anti-cheat & Integrity
* All results produced server-side; clients only render.
* Replay stored for audits.
* Flagging system for suspicious behaviors (impossible scores).
* Rate limiting per player.

10. TON / NFT integration
10.1. Smart contract & mint flow
* Smart contract: ERC-721 style on TON (NFT collection). Each mint returns nft_id (collection_addr + token_id).
* nft_service responsibilities:
    * Mint (pay gas/how? chain fees)
    * Transfer (verify recipient address)
    * Burn
    * Listen to on-chain events via indexer (or webhook) to reconcile transfers done outside game.
10.2. DB binding
* player_spirits.nft_id stores blockchain token reference.
* Every on-chain transfer update must be reconciled: if user transfers NFT away, set player_spirits.owner=null / is_minted=true? Design: minted spirits remain in DB, with owner_id updated only if transfer initiated via game; external transfers cause is_minted=true but nft_owner_address not equal to user. Reconciliation job flags mismatches.
10.3. Security
* Server signs transactions with a secure key (HSM recommended).
* For user initiated withdraws (TON), require signature challenge (user signs nonce) for high security flows.

11. Анти-фрод (обязательные механики)
1. Wallet duplicates
    * Unique wallet table + heuristic: same IP / device fingerprint / similar registration times → flag multiaccount.
    * On duplicate wallet addresses used across tg_id → auto flag, reduce referral credit, require manual review.
2. Suspicious energy restore
    * Track unnatural restore patterns (multiple instant restores in short period).
    * Rate limits: max N instant restores per 24h.
    * Alerts if restore frequency > threshold.
3. Multiaccount detection
    * Score based on same device, wallet, IP, patterns.
    * Automated actions: throttle, block withdrawals, require KYC.
4. Rate limits
    * API gateway token bucket per user; per endpoint stricter limits for financial endpoints.
5. Withdrawal delays
    * All TON withdrawals queued, manual/automated delay (e.g. 24–72h) for new accounts or flagged users.
6. Audit logs
    * Immutable logs for critical ops (mint, burn, withdraw, transfer, admin changes).

12. Тех. детали: таймеры и очереди
* Celery (Redis broker) tasks
    * tick_energy — every 10 minutes: increment energy by +5 up to max.
        * Implementation: for each player_spirits that need energy -> update DB in batches and update Redis caches.
    * finish_capsule_opening — scheduled at opening_ends_at.
    * process_withdrawals — batch processing, queue to TON service.
    * apply_referral_rewards — on purchases/donations.
* Redis
    * Leaderboards, matchmaking queues, ephemeral locks, token buckets.
* Atomic operations
    * Use DB transactions for money ops (lumens, ton reservations).
    * Use SELECT FOR UPDATE for concurrent buys/breeding.

13. Балансовая модель (экономика)
13.1. Валюты
* TON — on-chain, high value: used for mint, withdrawals, major purchases, fast opens.
* Lumens — in-game currency, soft currency: buying slots, boosts, capsule purchases, breeding partial.
13.2. Начальные значения
* New user: lumens_balance = 1000, ton_balance = 0.
* Referral: inviter + invitee +1000 lumens. Every 5 referrals → +0.5 TON (max 5 TON per inviter).
13.3. Income sources
* Purchases (real money → TON → lumens)
* Battler rewards (lumens + chance capsule)
* NFT sales (secondary market — % fee to game treasury)
* Donations (processed)
13.4. Sinks
* Caps open costs (fast open TON)
* Mint fees (TON)
* Burn fees (lumens)
* Slot purchases
* Marketplace fees
13.5. Fees & Treasury
* Platform takes commission on TON withdrawals/sales (configurable).
* Treasury account on TON for fees.
13.6. Economic balancing rules
* Rarity drop rates configurable per capsule (admin panel).
* Dynamic pricing: capsule_template.amount controls scarcity → price changes via admin scripts.

14. DevOps / CI / Monitoring / Security
* CI: lint, unit tests, integration tests with postgres & redis (GitHub Actions), build docker images, push to registry.
* CD: Kubernetes manifests, helm charts or docker-compose for MVP.
* Secrets: Vault or Kubernetes Secrets (no secrets in repo).
* Backup: daily Postgres backups, WAL archiving.
* Monitoring: Prometheus metrics (request latencies, DB metrics, Celery queue length), Grafana dashboards (economy KPIs).
* Alerting: Slack/Telegram on anomalies (balance drift, queue backlog).
* PenTesting: smart contract audits for TON, backend security review.
* SLA: 99.9% for API; critical endpoints RTO defined.

15. План разработки (sprint plan, 8 sprints — 2 weeks each)
Sprint 0 (planning + infra)
* Architecture approval, repo, CI, dev infra, DB schema initial, basic FastAPI skeleton.
Sprint 1 (core models + auth)
* Users, templates, migrations, onboarding flows, wallet connect, referrals.
Sprint 2 (capsules + boosts + shop)
* Capsule templates, buying, player_capsules, opening (sync immediate), admin CRUD.
Sprint 3 (player_spirits + inventory + slots)
* Player_spirits, slots purchase/sell, party management.
Sprint 4 (energy + workers)
* Redis/Celery, energy tick, open_time tasks, fast open, anti-fraud basics.
Sprint 5 (breeding + NFT integration basics)
* Breeding logic, burn parents, create child, integrate NFT minter stub, admin mint.
Sprint 6 (matchmaking & battle)
* Matchmaking queue, battle_session, 1 mini-game server simulation, reward flows.
Sprint 7 (TON integration & payments)
* Full TON SDK integration, deposits, withdrawals, minting on chain, reconciliation.
Sprint 8 (hardening + analytics + admin)
* Monitoring, logging, admin UIs, policy/anti-fraud rules, production rollout steps.

16. Все формулы (сводка)
* Breeding generation: child_gen = min(gen1, gen2) + 1
* Breeding stat: child_stat = max(parent1_stat, parent2_stat, min_stat_for_generation)
* Energy restore tick: energy += 5 every 10 minutes, capped at max_energy.
* Battle player power score: power = Σ(stat_i * stat_weight_i) * rarity_factor + level_bonus
* Drop selection: weighted random over eligible spirits; weight = base_weight * rarity_weight.
* XP to level: xp_for_next = floor(base * level^1.2) (configurable). Starting base 100.

17. Безопасность и соответствие
* On-chain integrity: every mint/transfer/burn logged with tx_hash; reconcilers ensure DB = chain.
* KYC/AML: required for TON withdrawals > threshold.
* Data privacy: GDPR readiness (user data deletion flow).
* Rate limiting & abuse detection as described.

18. Admin & Analytics
* Admin panel: user search, manual grants, set capsule drop tables, manage templates, view economy dashboards.
* Analytics: daily retention, DAU/MAU, LTV, ARPU, conversion funnel. Exportable CSVs.

19. Технические нюансы реализации (рекомендации)
* Use async SQLAlchemy + Alembic for migrations.
* Use Pydantic models for request/response schemas; reuse across services via shared package.
* Use deterministic battle simulation server-side (no trust).
* For fast operationHUNT — Полный production-ready проект (по ТЗ)
Формат: аккуратно по пунктам, технически полно и готово к реализации.Роль: вы — CTO/Lead; я — архитектор/lead backend, game designer и системный архитектор.

1. Краткий обзор (one-liner)
HUNT — Web3 Telegram Mini App на TON: игроки собирают, развивают, скрещивают и торгуют энергетическими существами — Спиритами (NFT). Игра сочетает Web3-экономику, F2P-механику, капсулы, breeding, энергию и 3-чел PvP мини-игры.

2. Высокоуровневая архитектура (production)
* Frontend
    * Telegram Mini App (HTML5/TS, React/Vite), UI/UX ориентирован на мобильные webview.
    * Websocket для реального времени (game lobbies, матчмейкинг уведомления).
* API Gateway
    * Nginx / Traefik + HTTPS, rate limiting, JWT auth + Telegram mini-app signed payload validation.
* Backend (microservices / monolith hybrid)
    * Auth & Profile Service (FastAPI async)
    * Game Service (FastAPI async) — core: spirits, slots, boosts, capsules, breeding, inventory
    * Matchmaking & Battle Service (FastAPI + Websockets / Redis streams)
    * Economy & Payments Service (TON SDK integration, Lumens accounting)
    * NFT Service (TON minter, transfer, burn)
    * Admin Service (CRUD, analytics)
    * Worker Cluster (Celery + Redis) — background tasks: capsule timers, energy ticks, scheduled payouts
* Data layer
    * PostgreSQL (async SQLAlchemy + Alembic migrations)
    * Redis (cache, leaderboards, ephemeral matchmaking, token buckets)
    * Celery broker (Redis) + result backend (Redis/Postgres)
* Storage
    * S3 compatible (avatars, sprites, capsule assets, animations)
* Monitoring & Logging
    * Prometheus + Grafana, Alertmanager; ELK / Loki for logs.
* CI/CD
    * GitHub Actions / GitLab CI → build, tests, image push, deploy (k8s or Docker Compose for MVP)
* Security
    * WAF, rate limits, multi-account detection, WALLET anti-fraud heuristics.
* Blockchain
    * TON SDK service (node or light-client), on-chain NFT smart contract, indexer for transfers (webhooks).

3. Сервисы — краткий список + обязанности
1. Auth & Profile
    * Telegram mini_app onboarding, session management, referrals, bans, donations.
2. Game Core
    * Spirits templates, player_spirits, slots, boosts, capsules, inventory, breeding logic.
3. Matchmaking & Battles
    * 3-player battle_session, deterministic simulation + replay log, reward distribution.
4. Economy
    * Lumens accounting, TON payouts/withdraws, purchase flows (capsules, boosts, slots).
5. NFT / TON
    * Mint/burn/transfer, verify on-chain integrity, link nft_id ↔ player_spirits.
6. Admin
    * CRUD, drop rates, analytics, manual minting/rewards.
7. Workers
    * Celery tasks: energy tick, capsule opening, leaderboard updates, delayed payouts.

4. Сущности — ER / SQL схемы (Postgres)
Далее — SQL DDL (упрощённый и production-ready: constraints, FKs, индексы, timestamps).Все timestamp поля TIMESTAMP WITH TIME ZONE DEFAULT now().
4.1. Общие lookup таблицы
CREATE TABLE elements (
  id SERIAL PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,
  name_ru TEXT,
  name_en TEXT,
  icon_url TEXT
);

CREATE TABLE rarities (
  id SERIAL PRIMARY KEY,
  code TEXT UNIQUE NOT NULL, -- common, rare, epic, legendary, mythical
  name_ru TEXT,
  name_en TEXT,
  icon_url TEXT,
  power_factor NUMERIC DEFAULT 1.0 -- balance helper
);
4.2. Users + related
CREATE TABLE users (
  tg_id BIGINT PRIMARY KEY,
  user_name TEXT,
  first_name TEXT,
  last_name TEXT,
  ton_address TEXT,
  ton_balance NUMERIC DEFAULT 0,
  lumens_balance NUMERIC DEFAULT 1000,
  referral_code TEXT UNIQUE NOT NULL,
  referraled_by BIGINT REFERENCES users(tg_id),
  referrals_count INTEGER DEFAULT 0,
  is_banned BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  is_admin BOOLEAN DEFAULT FALSE,
  language TEXT,
  onboarding_step TEXT,
  donate_amount NUMERIC DEFAULT 0,
  last_active TIMESTAMPTZ DEFAULT now()
);
CREATE UNIQUE INDEX idx_users_ton_address ON users(ton_address);
CREATE TABLE bans (
  id SERIAL PRIMARY KEY,
  tg_id BIGINT REFERENCES users(tg_id) ON DELETE CASCADE,
  reason TEXT,
  banned_at TIMESTAMPTZ DEFAULT now(),
  expires_at TIMESTAMPTZ
);
CREATE TABLE donations (
  id SERIAL PRIMARY KEY,
  tg_id BIGINT REFERENCES users(tg_id) ON DELETE CASCADE,
  amount NUMERIC NOT NULL,
  currency TEXT NOT NULL, -- TON/LUMENS etc
  donated_at TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE wallets (
  id SERIAL PRIMARY KEY,
  tg_id BIGINT REFERENCES users(tg_id),
  address TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(address)
);
4.3. Spirits (templates + player)
CREATE TABLE spirits_template (
  id SERIAL PRIMARY KEY,
  code TEXT UNIQUE,
  element_id INT REFERENCES elements(id),
  rarity_id INT REFERENCES rarities(id),
  name_ru TEXT,
  name_en TEXT,
  generation INT DEFAULT 1,
  default_level INT DEFAULT 1,
  default_xp_for_next INT DEFAULT 100,
  description_ru TEXT,
  description_en TEXT,
  base_run INT DEFAULT 1,
  base_jump INT DEFAULT 1,
  base_swim INT DEFAULT 1,
  base_dives INT DEFAULT 1,
  base_fly INT DEFAULT 1,
  base_maneuver INT DEFAULT 1,
  base_max_energy INT DEFAULT 100,
  icon_url TEXT,
  spirit_animation_url TEXT,
  capsule_id INT REFERENCES capsule_template(id),
  is_starter BOOLEAN DEFAULT FALSE,
  is_available BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
capsule_template forward ref — defined later. In actual migrations order accordingly.
CREATE TABLE player_spirits (
  id BIGSERIAL PRIMARY KEY,
  owner_id BIGINT REFERENCES users(tg_id) ON DELETE CASCADE,
  spirit_template_id INT REFERENCES spirits_template(id) ON DELETE SET NULL,
  custom_name TEXT,
  generation INT DEFAULT 1,
  level INT DEFAULT 1,
  xp_for_next_level INT DEFAULT 100,
  xp INT DEFAULT 0,
  description_ru TEXT,
  description_en TEXT,
  base_run INT DEFAULT 1,
  base_jump INT DEFAULT 1,
  base_swim INT DEFAULT 1,
  base_dives INT DEFAULT 1,
  base_fly INT DEFAULT 1,
  base_maneuver INT DEFAULT 1,
  base_max_energy INT DEFAULT 100,
  energy INT DEFAULT 100,
  is_active BOOLEAN DEFAULT FALSE,
  slot_id BIGINT REFERENCES player_slots(id),
  is_minted BOOLEAN DEFAULT FALSE,
  nft_id TEXT, -- ton NFT address / token id
  acquired_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_player_spirits_owner ON player_spirits(owner_id);
4.4. Capsule templates + player capsules
CREATE TABLE capsule_template (
  id SERIAL PRIMARY KEY,
  code TEXT UNIQUE,
  element_id INT REFERENCES elements(id),
  rarity_id INT REFERENCES rarities(id),
  name_ru TEXT,
  name_en TEXT,
  open_time_seconds INT DEFAULT 0,
  price_in_ton NUMERIC DEFAULT 0,
  price_lumens NUMERIC DEFAULT 0,
  icon_url TEXT,
  capsule_animation_url TEXT,
  is_available BOOLEAN DEFAULT TRUE,
  amount INT DEFAULT 0, -- how many left for sale
  fast_open_cost NUMERIC DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE player_capsules (
  id BIGSERIAL PRIMARY KEY,
  owner_id BIGINT REFERENCES users(tg_id) ON DELETE CASCADE,
  capsule_id INT REFERENCES capsule_template(id) ON DELETE SET NULL,
  quantity INT DEFAULT 1,
  is_opened BOOLEAN DEFAULT FALSE,
  is_opening BOOLEAN DEFAULT FALSE,
  opening_started_at TIMESTAMPTZ,
  opening_ends_at TIMESTAMPTZ,
  acquired_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_player_capsules_owner ON player_capsules(owner_id);
4.5. Slots templates + player slots
CREATE TABLE slots_template (
  id SERIAL PRIMARY KEY,
  element_id INT REFERENCES elements(id),
  price_lumens NUMERIC DEFAULT 0,
  sell_price_lumens NUMERIC DEFAULT 0,
  is_starter BOOLEAN DEFAULT FALSE,
  icon_url TEXT,
  is_available BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE player_slots (
  id BIGSERIAL PRIMARY KEY,
  owner_id BIGINT REFERENCES users(tg_id) ON DELETE CASCADE,
  slot_template_id INT REFERENCES slots_template(id),
  element_id INT REFERENCES elements(id),
  acquired_at TIMESTAMPTZ DEFAULT now(),
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_player_slots_owner ON player_slots(owner_id);
4.6. Boosts templates + player boosts
CREATE TABLE boost_template (
  id SERIAL PRIMARY KEY,
  internal_name TEXT,
  name_ru TEXT,
  name_en TEXT,
  description_ru TEXT,
  description_en TEXT,
  price_ton NUMERIC DEFAULT 0,
  boost_xp INT DEFAULT 0,
  amount INT DEFAULT 0,
  icon_url TEXT,
  is_available BOOLEAN DEFAULT TRUE,
  sort_order INT
);

CREATE TABLE player_boosts (
  id BIGSERIAL PRIMARY KEY,
  owner_id BIGINT REFERENCES users(tg_id) ON DELETE CASCADE,
  boost_id INT REFERENCES boost_template(id),
  quantity INT DEFAULT 1,
  acquired_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
4.7. Battle / Matchmaking / Logs
CREATE TABLE battle_sessions (
  id BIGSERIAL PRIMARY KEY,
  mode TEXT, -- e.g. flow_flight ...
  started_at TIMESTAMPTZ DEFAULT now(),
  finished_at TIMESTAMPTZ,
  result_json JSONB, -- stored replay/outcome
  created_by BIGINT REFERENCES users(tg_id)
);

CREATE TABLE battle_players (
  id BIGSERIAL PRIMARY KEY,
  battle_session_id BIGINT REFERENCES battle_sessions(id) ON DELETE CASCADE,
  player_id BIGINT REFERENCES users(tg_id),
  player_spirit_id BIGINT REFERENCES player_spirits(id),
  stats JSONB,
  score NUMERIC,
  rank INT
);
4.8. Economy logs & withdrawals
CREATE TABLE balance_logs (
  id BIGSERIAL PRIMARY KEY,
  tg_id BIGINT REFERENCES users(tg_id),
  change NUMERIC,
  currency TEXT,
  reason TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE withdrawals (
  id BIGSERIAL PRIMARY KEY,
  tg_id BIGINT REFERENCES users(tg_id),
  amount NUMERIC,
  currency TEXT,
  status TEXT DEFAULT 'pending', -- pending/processing/completed/rejected
  created_at TIMESTAMPTZ DEFAULT now(),
  processed_at TIMESTAMPTZ
);

5. ER-диаграмма (текстовое описание)
* users 1 — N → player_spirits, player_capsules, player_slots, player_boosts, donations, bans, balance_logs.
* elements 1 — N → spirits_template, capsule_template, slots_template.
* rarities 1 — N → spirits_template, capsule_template.
* spirits_template 1 — N → player_spirits.
* capsule_template 1 — N → player_capsules.
* slots_template 1 — N → player_slots.
* player_spirits N — 1 → player_slots via slot_id.
* battle_sessions 1 — N → battle_players.
(при необходимости — визуальная схема через dbdiagram / draw.io в артефакте проекта)

6. Файловая структура (предложение)
/hunt/
├─ docker-compose.yml
├─ backend
├─ frontend
└─ README.md

7. Game logic — сущности и правила (подробно)
7.1. Спирит (описание)
* NFT: уникальная сущность.
* Атрибуты: element, rarity, generation, level, xp, stats = {run, jump, swim, dives, fly, maneuver, max_energy}.
* energy — текущая энергия; max_energy → базируется на template + generation bonus.
* is_active — в активной команде (требует слот подходящей стихии).
7.2. Стихии
* Набор: fire, water, earth, air, light, dark (пример). Каждая стихия влияет на совместимость слотов/капсул/бустов.
7.3. Редкости
* common < rare < epic < legendary < mythical
* Rarity влияет на базовую силу, шанс в капсулах, цену mint, лимит капсул.
7.4. Капсулы
* CapsuleTemplate привязан к элементу и редкости.
* Открытие занимает open_time_seconds. Если игрок платит fast_open_cost (TON или Lumens) — открывается моментально.
* Дроп: набор spirits_template с capsule_id = capsule_template.id. Редкость капсулы ограничивает возможный дроп.
7.5. Слоты
* Каждый слот имеет element_id. Starter slots free.
* Player can buy additional slots (lumens).
* Slot можно продать (sell_price_lumens) → lumens balance.
7.6. Boosts
* Consumable, даёт boost_xp при использовании на spirit.
7.7. Breeding (скрещивание)
Условия:
* Родители: same element (element_id equal).
* Родители: одного и того же spirit_template (спирит = одинаковый код / template).
* Оба уровня = 10.
* Стоимость: фиксированная TON (configurable) + burn fees (люмены).
* Родители сжигаются (burn) → удаляются / помечаются как burned; TON списывается.
* Формула:
    * generation = min(gen_parent1, gen_parent2) + 1
    * stats = max(parent stats, min_stats_for_generation)
    * rarity = max(parent rarity)
* Минимальные статы (table):
    * gen1: 1/1/1/1/1/1
    * gen2: 3/3/3/3/3/3
    * gen3: 5/5/5/5/5/5
    * gen4: 8/8/8/8/8/8
    * gen5: 10/10/10/10/10/10
    * gen6: 12/12/12/12/12/12
    * gen7: 15/15/15/15/15/15
* Новый spirit создаётся как player_spirit с generation, level=1, xp=0, base_stats вычислены как описано.
* NFT: новый спирит не сминтится автоматически (опция — mint on creation for TON fee).
7.8. Energy System
* Каждый action требует energy (например, гонка: 15 energy).
* max_energy берётся из spirit.base_max_energy + generation modifier (например +5 per gen).
* Восстановление: +5 energy каждые 10 минут.
    * Реализация: Redis + Celery tick (cron every 10 minutes) → for each active spirit or each player? Design: per-player aggregate: restore to each spirit up to its max.
    * Redis stores energy_lock and last_tick.
* Instant restore: оплата TON/Lumens → происходит мгновенно (worker verifies payment, updates energy, logs anti-fraud).
* Limits: prevent scripts — rate limiting + server side checks (max restore per hour, suspicious patterns flagged).
7.9. Mini-games PvP (3 игрока)
* Общая идея: матчмейкер собирает 3 игроков, фиксирует player_stats (derived from spirit stats + random seed + power_modifiers), запускает deterministic simulation server-side, сохраняет replay JSON.
* Каждая мини-игра:
    1. Flow Flight — runner/obstacle: key stats {maneuver, flow, reaction}; winner = max(distance).
    2. Deep Dive — vertical depth: {dives, swim/flow}; winner = min(depth value (bigger depth)).
    3. Rhythm Path — QTE: {reaction, impulse}; winner = max(accuracy*speed).
    4. Jump Rush — platform jumps: {maneuver, reaction}; winner = max(distance + combos).
    5. Collecting Frenzy — collect items: {flow, maneuver}; winner = items_collected.
* Reward logic: ranked rewards (1st/2nd/3rd), experience to spirits, lumens/TON depending on mode (free/paid), capsule drops probabilistic.
* Deterministic server simulation: uses a PRNG seed per battle_session (stored) → reproducible results for audits.

8. API — список эндпоинтов, JSON контрактов, параметры, валидации и бизнес-логика
Общие: все ответы в формате JSON: { "ok": bool, "data": {...}, "error": {"code": "...", "message": "..."} }Авторизация: JWT + Telegram signed payload header X-Tg-Signed. Проверка на backend.

/api/v1/profile
GET /api/v1/profile
Описание: получить профиль текущего игрока.Auth: required.Response 200
{
  "ok": true,
  "data": {
    "tg_id": 123456,
    "user_name": "player",
    "first_name": "Ivan",
    "last_name": "Petrov",
    "ton_address": "...",
    "ton_balance": "1.25",
    "lumens_balance": "500",
    "referral_code": "ABCD12",
    "referrals_count": 3,
    "onboarding_step": "completed",
    "donate_amount": "0.5",
    "last_active": "2025-12-07T12:34:56Z"
  }
}
Errors
* 401 unauthorized
* 429 rate limit
PATCH /api/v1/profile
Body
{
  "language": "ru",
  "first_name": "Ivan",
  "last_name": "Petrov",
  "user_name": "ivan_p"
}
Logic
* Validate changes; username unique (if changing).
* Update updated_at.
* Return updated profile.
DELETE /api/v1/profile
Logic
* Soft delete (set is_banned=true? or mark deleted flag).
* Requires admin confirmation for full deletion (endpoint reserved for admin).
Wallet management
* POST /api/v1/profile/wallet/connect — body: { "ton_address": "EQ..." } → validate address (TON SDK / checksum), store in wallets, update users.ton_address. If duplicate: flag multiaccount risk, increment suspicion_score.
* POST /api/v1/profile/wallet/change — change wallet (requires OTP / transaction signature).
* POST /api/v1/profile/wallet/deposit_link — returns a TON deposit address or payment link.
* POST /api/v1/profile/wallet/withdraw — body { amount, currency, to_address }:
    * Checks: min withdraw TON >= 10 TON required in business rules, available balance check, KYC checks (if needed), withdrawal delay (anti-fraud), add withdrawal entry pending, enqueue processing.
* GET /api/v1/profile/wallet/transactions — paginated.
Onboarding endpoints:
* POST /api/v1/profile/onboarding/step — set onboarding_step, accept referral code (apply rewards: +1000 lumens to inviter and invitee, milestone logic for TON rewards).
* Business logic: referral credit immediate for Lumens, TON rewards on milestones (automated via worker).
Donations:
* GET /api/v1/profile/donations
* POST /api/v1/profile/donate — process TON donation via TON SDK, record in donations, apply referral commission (10%) to referrer.

/api/v1/admin/users
* GET /api/v1/admin/users — filters: tg_id, wallet, is_banned, pagination, sort.
* GET /api/v1/admin/users/{tg_id} — full profile + logs.
* PATCH /api/v1/admin/users/{tg_id} — edit (ban/unban, set balances).
* POST /api/v1/admin/users/{tg_id}/ban — body { reason, expires_at } → creates bans row, sets is_banned true.
* POST /api/v1/admin/users/{tg_id}/grant_lumens — admin grant.
* POST /api/v1/admin/users/{tg_id}/mint_spirit — mint specific spirit to user (create player_spirit + optionally mint NFT).
* Errors/Checks: RBAC (is_admin), audit logging.

/api/v1/spirits
GET /api/v1/spirits/catalog
Params: element_id, rarity_id, page, size, searchResponse: list of spirits_template with summary fields: id, name, rarity, element, base stats, icon_url.
GET /api/v1/spirits/my
Response: list player_spirits belonging to user (inactive & active), incl. energy, stats, is_minted flag.
GET /api/v1/spirits/active
Response: current active party (slots + assigned spirits).
POST /api/v1/spirits/{player_spirit_id}/activate
Body: { "slot_id": 123 }Logic:
* Validate slot.element_id == player_spirit.element_id
* Slot free? assign spirit to slot (update player_spirits.is_active=true, slot_id set).
* If slot occupied: error 409 or add swap flow.Errors: 400 invalid compatibility, 403 slot not owned, 404 spirit not found.
POST /api/v1/spirits/{player_spirit_id}/mint
Logic:
* Validate ownership, is_minted==false.
* Charge TON mint fee (config).
* Call NFT Service to mint → returns nft_id → set is_minted=true, nft_id.
* On blockchain success only mark minted.
POST /api/v1/spirits/{player_spirit_id}/burn
Logic:
* Check ownership and burn permissions.
* If parent used in breeding, ensure rules.
* If minted: call NFT burn (on-chain), set is_minted=false, nft_id=null, then delete or mark as burned.
* Charge small lumens fee to burn.
POST /api/v1/spirits/breed
Body:
{
  "parent1_id": 111,
  "parent2_id": 222,
  "pay_with": "TON"
}
Logic (breeding full flow):
1. Validate both owners = current user.
2. Validate same element, same spirit_template_id, both level == 10.
3. Validate breeding cost (TON) present in user's balance; subtract TON.
4. Compute child generation = min(gen1, gen2) + 1.
5. Compute child's stats:
    * for each stat: max(parent_stat, min_stat_for_generation)
6. Rarety = max(rarity_parent1, rarity_parent2).
7. Create new player_spirit (is_minted=false).
8. Burn parents: if minted → call NFT burn; mark player_spirits deleted or flagged burned=true and remove ownership; update logs.
9. Emit event + audit log.Response 200: newly created spirit.
Errors/Checks: parents levels, element, ownership, funds, rate limiting per hour.

/api/v1/admin/spirits
* CRUD on spirits_template (create, update recalc).
* Endpoint to set capsule drop tables: e.g. POST /api/v1/admin/spirits/drops body: { capsule_id: 10, spirit_template_id: 200, weight: 100 }.
* Endpoint to adjust global balancing factors.

/api/v1/capsules
GET /api/v1/capsules/shop
Returns: grouped by element, then by rarity. For each capsule: { id, name, icon_url, price_ton, price_lumens, amount_left, open_time_seconds }.
POST /api/v1/capsules/buy
Body: { "capsule_id": 10, "quantity": 1, "pay_with": "lumens" }Logic:
* Validate inventory (capsule_template.amount).
* Charge user -> decrease lumens/TON.
* Create or increment player_capsules row.
* Log balance_logs.
* Return updated inventory.
GET /api/v1/capsules/my
* List player_capsules for user.
POST /api/v1/capsules/{player_capsule_id}/open
Logic:
* Validate ownership and that capsule not already opening.
* If open_time_seconds == 0 -> resolve immediately: pick drop via weighted random from spirits_template where capsule_id matches. Create player_spirit for user, decrement player_capsules.quantity (or delete).
* If >0 -> set is_opening=true, opening_started_at=now, opening_ends_at = now + seconds, enqueue Celery task to finish opening.
* Fast open: POST /fast_open — pay fast_open_cost (TON or Lumens), resolve immediately.
* On resolve: create player_spirit, persist, return new spirit summary.
Probability logic
* Drop weights based on rarity & capsule rarity. Example: capsule rarity X cannot drop spirits with rarity > capsule.rarity.
Errors: insufficient balance, capsule sold out, illegal open (mismatch owner).
/api/v1/admin/capsules
* CRUD for capsule_template
* Endpoint to set drop rates (mapping capsule_template → spirits_template with weight).
* Admin open (force).

/api/v1/slots
GET /api/v1/slots/templates
* Returns slots_template for purchase.
POST /api/v1/slots/buy
Body: { "slot_template_id": 2 }Logic:
* Charge lumens, create player_slot entry.
* If slot_template.is_starter -> disallow buy (already assigned).
POST /api/v1/slots/sell
Body: { "player_slot_id": 22 }Logic:
* Validate ownership, slot empty (no spirit assigned).
* Credit sell_price_lumens.
GET /api/v1/slots/party
* Return active party: slots + assigned spirits.
/api/v1/admin/slots
* CRUD.

/api/v1/boosts
GET /api/v1/boosts/shop
* Return list of boost_template.
POST /api/v1/boosts/buy
Body: { "boost_id": 1, "qty": 1 }Logic: charge lumens/ton, create/increment player_boosts row.
GET /api/v1/boosts/my
* Inventory.
POST /api/v1/boosts/{player_boost_id}/use
Body: { "player_spirit_id": 333 }Logic:
* Validate ownership, quantity, target spirit owner match.
* Apply boost_xp to target spirit (increase xp, level up if xp >= xp_for_next_level; recalc next xp).
* Reduce quantity.
* Return updated spirit.

9. Matchmaking & Battle Logic (detailed)
9.1. Matchmaking
* Queue per mode, skill matching by power_score = sum(stats * rarity_factor) + ELO / recent_winrate.
* When 3 players matched → create battle_session with seed, lock involved player_spirits, set cooldown on spirits (prevent concurrent participation).
* Notify players via websocket.
9.2. Battle flow
* On session start: fetch player stats (base stats + items/boosts), build deterministic player state.
* Run simulation server-side (no client trust). Use deterministic rules per mini-game (seeded RNG).
* After simulation, compute rank (1/2/3), assign rewards:
    * XP to spirit (tiered)
    * Lumens to players (scaled)
    * Chance to drop capsule (low probability)
* Save result_json (replay) + battle_players records.
* Unlock spirits and update energy (deduct 15 per race).
9.3. Anti-cheat & Integrity
* All results produced server-side; clients only render.
* Replay stored for audits.
* Flagging system for suspicious behaviors (impossible scores).
* Rate limiting per player.

10. TON / NFT integration
10.1. Smart contract & mint flow
* Smart contract: ERC-721 style on TON (NFT collection). Each mint returns nft_id (collection_addr + token_id).
* nft_service responsibilities:
    * Mint (pay gas/how? chain fees)
    * Transfer (verify recipient address)
    * Burn
    * Listen to on-chain events via indexer (or webhook) to reconcile transfers done outside game.
10.2. DB binding
* player_spirits.nft_id stores blockchain token reference.
* Every on-chain transfer update must be reconciled: if user transfers NFT away, set player_spirits.owner=null / is_minted=true? Design: minted spirits remain in DB, with owner_id updated only if transfer initiated via game; external transfers cause is_minted=true but nft_owner_address not equal to user. Reconciliation job flags mismatches.
10.3. Security
* Server signs transactions with a secure key (HSM recommended).
* For user initiated withdraws (TON), require signature challenge (user signs nonce) for high security flows.

11. Анти-фрод (обязательные механики)
1. Wallet duplicates
    * Unique wallet table + heuristic: same IP / device fingerprint / similar registration times → flag multiaccount.
    * On duplicate wallet addresses used across tg_id → auto flag, reduce referral credit, require manual review.
2. Suspicious energy restore
    * Track unnatural restore patterns (multiple instant restores in short period).
    * Rate limits: max N instant restores per 24h.
    * Alerts if restore frequency > threshold.
3. Multiaccount detection
    * Score based on same device, wallet, IP, patterns.
    * Automated actions: throttle, block withdrawals, require KYC.
4. Rate limits
    * API gateway token bucket per user; per endpoint stricter limits for financial endpoints.
5. Withdrawal delays
    * All TON withdrawals queued, manual/automated delay (e.g. 24–72h) for new accounts or flagged users.
6. Audit logs
    * Immutable logs for critical ops (mint, burn, withdraw, transfer, admin changes).

12. Тех. детали: таймеры и очереди
* Celery (Redis broker) tasks
    * tick_energy — every 10 minutes: increment energy by +5 up to max.
        * Implementation: for each player_spirits that need energy -> update DB in batches and update Redis caches.
    * finish_capsule_opening — scheduled at opening_ends_at.
    * process_withdrawals — batch processing, queue to TON service.
    * apply_referral_rewards — on purchases/donations.
* Redis
    * Leaderboards, matchmaking queues, ephemeral locks, token buckets.
* Atomic operations
    * Use DB transactions for money ops (lumens, ton reservations).
    * Use SELECT FOR UPDATE for concurrent buys/breeding.

13. Балансовая модель (экономика)
13.1. Валюты
* TON — on-chain, high value: used for mint, withdrawals, major purchases, fast opens.
* Lumens — in-game currency, soft currency: buying slots, boosts, capsule purchases, breeding partial.
13.2. Начальные значения
* New user: lumens_balance = 1000, ton_balance = 0.
* Referral: inviter + invitee +1000 lumens. Every 5 referrals → +0.5 TON (max 5 TON per inviter).
13.3. Income sources
* Purchases (real money → TON → lumens)
* Battler rewards (lumens + chance capsule)
* NFT sales (secondary market — % fee to game treasury)
* Donations (processed)
13.4. Sinks
* Caps open costs (fast open TON)
* Mint fees (TON)
* Burn fees (lumens)
* Slot purchases
* Marketplace fees
13.5. Fees & Treasury
* Platform takes commission on TON withdrawals/sales (configurable).
* Treasury account on TON for fees.
13.6. Economic balancing rules
* Rarity drop rates configurable per capsule (admin panel).
* Dynamic pricing: capsule_template.amount controls scarcity → price changes via admin scripts.

14. DevOps / CI / Monitoring / Security
* CI: lint, unit tests, integration tests with postgres & redis (GitHub Actions), build docker images, push to registry.
* CD: Kubernetes manifests, helm charts or docker-compose for MVP.
* Secrets: Vault or Kubernetes Secrets (no secrets in repo).
* Backup: daily Postgres backups, WAL archiving.
* Monitoring: Prometheus metrics (request latencies, DB metrics, Celery queue length), Grafana dashboards (economy KPIs).
* Alerting: Slack/Telegram on anomalies (balance drift, queue backlog).
* PenTesting: smart contract audits for TON, backend security review.
* SLA: 99.9% for API; critical endpoints RTO defined.

15. План разработки (sprint plan, 8 sprints — 2 weeks each)
Sprint 0 (planning + infra)
* Architecture approval, repo, CI, dev infra, DB schema initial, basic FastAPI skeleton.
Sprint 1 (core models + auth)
* Users, templates, migrations, onboarding flows, wallet connect, referrals.
Sprint 2 (capsules + boosts + shop)
* Capsule templates, buying, player_capsules, opening (sync immediate), admin CRUD.
Sprint 3 (player_spirits + inventory + slots)
* Player_spirits, slots purchase/sell, party management.
Sprint 4 (energy + workers)
* Redis/Celery, energy tick, open_time tasks, fast open, anti-fraud basics.
Sprint 5 (breeding + NFT integration basics)
* Breeding logic, burn parents, create child, integrate NFT minter stub, admin mint.
Sprint 6 (matchmaking & battle)
* Matchmaking queue, battle_session, 1 mini-game server simulation, reward flows.
Sprint 7 (TON integration & payments)
* Full TON SDK integration, deposits, withdrawals, minting on chain, reconciliation.
Sprint 8 (hardening + analytics + admin)
* Monitoring, logging, admin UIs, policy/anti-fraud rules, production rollout steps.

16. Все формулы (сводка)
* Breeding generation: child_gen = min(gen1, gen2) + 1
* Breeding stat: child_stat = max(parent1_stat, parent2_stat, min_stat_for_generation)
* Energy restore tick: energy += 5 every 10 minutes, capped at max_energy.
* Battle player power score: power = Σ(stat_i * stat_weight_i) * rarity_factor + level_bonus
* Drop selection: weighted random over eligible spirits; weight = base_weight * rarity_weight.
* XP to level: xp_for_next = floor(base * level^1.2) (configurable). Starting base 100.

17. Безопасность и соответствие
* On-chain integrity: every mint/transfer/burn logged with tx_hash; reconcilers ensure DB = chain.
* KYC/AML: required for TON withdrawals > threshold.
* Data privacy: GDPR readiness (user data deletion flow).
* Rate limiting & abuse detection as described.

18. Admin & Analytics
* Admin panel: user search, manual grants, set capsule drop tables, manage templates, view economy dashboards.
* Analytics: daily retention, DAU/MAU, LTV, ARPU, conversion funnel. Exportable CSVs.

19. Технические нюансы реализации (рекомендации)
* Use async SQLAlchemy + Alembic for migrations.
* Use Pydantic models for request/response schemas; reuse across services via shared package.
* Use deterministic battle simulation server-side (no trust).
* For fast operations (buy capsule), use optimistic locks + idempotency keys to prevent double spend.
* Celery scheduled tasks: timezones in UTC.
* For TON interactions, use a dedicated service with HSM/secure key storage.

20. Резюме игровых мировых текстов (для UI / lore)
* Спириты — эфирные существа-энергии, рождающиеся из капсул. Каждый принадлежит к стихии (Огонь, Вода, Земля, Воздух, Свет, Тьма), имеет редкость (Обычный → Мифический), поколение и статистики — они решают успех в мини-играх.
* Капсулы — контейнеры энергии. Обычные капсулы дают простых спиритов; мифические — высокую редкость.
* Слоты — подготовленные места в вашей партии; каждый слот ассоциирован со стихией.
* Бусты — концентрата опыта, применяемого к спиритам.
* Скрещивание — альянс двух взрослых спиритов даёт новое поколение, сильнее по минимуму и наследующее лучшую редкость.
* Энергия — ограниченный ресурс, восстанавливаемый со временем или моментально за плату.
* PvP мини-игры — аренды для спиритов, где навыки решают исход. Победы приносят опыт, награды и шанс найти редкую капсулу.

21. Примеры JSON-ответов и ошибок (унифицировано)
Успешный ответ
{ "ok": true, "data": { /* payload */ } }
Ошибка
{
  "ok": false,
  "error": {
    "code": "INSUFFICIENT_FUNDS",
    "message": "Not enough lumens to buy capsule",
    "details": null
  }
}
Валидации
* All numeric money values as strings or decimal to prevent JS float issues.
* Consistent error codes: UNAUTHORIZED, NOT_FOUND, INVALID_INPUT, RATE_LIMITED, FRAUD_SUSPECTED, INSUFFICIENT_FUNDS, COMPATIBILITY_ERROR, ALREADY_OPENING.

22. Checklist для MVP запуска
* DB schema + migrations
* Auth via Telegram signed payload
* Core endpoints (profile, spirits, capsules, boosts, slots)
* Celery worker + Redis energy tick + capsule open tasks
* Simple deterministic battle simulation (one mini-game)
* NFT service stub + DB hooks
* Admin CRUD for templates & drop rates
* CI pipeline & Docker images
* Basic monitoring (Prometheus) & logging
* Anti-fraud basics (wallet uniqueness, rate limiting)
* Documentation + API spec (OpenAPI)


21. Примеры JSON-ответов и ошибок (унифицировано)
Успешный ответ
{ "ok": true, "data": { /* payload */ } }
Ошибка
{
  "ok": false,
  "error": {
    "code": "INSUFFICIENT_FUNDS",
    "message": "Not enough lumens to buy capsule",
    "details": null
  }
}
Валидации
* All numeric money values as strings or decimal to prevent JS float issues.
* Consistent error codes: UNAUTHORIZED, NOT_FOUND, INVALID_INPUT, RATE_LIMITED, FRAUD_SUSPECTED, INSUFFICIENT_FUNDS, COMPATIBILITY_ERROR, ALREADY_OPENING.

22. Checklist для MVP запуска
* DB schema + migrations
* Auth via Telegram signed payload
* Core endpoints (profile, spirits, capsules, boosts, slots)
* Celery worker + Redis energy tick + capsule open tasks
* Simple deterministic battle simulation (one mini-game)
* NFT service stub + DB hooks
* Admin CRUD for templates & drop rates
* CI pipeline & Docker images
* Basic monitoring (Prometheus) & logging
* Anti-fraud basics (wallet uniqueness, rate limiting)
* Documentation + API spec (OpenAPI)

Сделай все подсказки и обьяснения на русском языке в коде а также пиши очень простой код, чтобы можно было легко его читать который можно будет легко запускать с помощью makefile