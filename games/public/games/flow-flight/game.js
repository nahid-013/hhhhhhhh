// Flow Flight - T-Rex Style Game
// Получаем параметры из URL
const urlParams = new URLSearchParams(window.location.search);
const sessionId = urlParams.get('sessionId') || 'test-session';
const spiritId = urlParams.get('spiritId') || 'test-spirit';
const serverUrl = urlParams.get('server') || 'http://localhost:9000';

// Конфигурация игры в стиле T-Rex
const GAME_CONFIG = {
  width: 800,
  height: 600,
  baseSpeed: 200,
  // Единая дорожка для всех игроков
  track: { y: 300, groundY: 330 },
  playerSize: 40,
  gravity: 1500,
  jumpForce: -500,
  obstacleWidth: 30,
  obstacleHeight: 50,
};

// Цвета игроков
const PLAYER_COLORS = [
  { main: 0x00ffff, glow: 0x00ffff, name: 'Cyan' },
  { main: 0xff6b6b, glow: 0xff6b6b, name: 'Red' },
  { main: 0x6bff6b, glow: 0x6bff6b, name: 'Green' },
];

// Состояние игры
let socket = null;
let gameState = {
  phase: 'connecting',
  players: [],
  myId: null,
  countdown: 3,
  seed: 0,
};

// ============ Сцена ожидания ============
class WaitingScene extends Phaser.Scene {
  constructor() {
    super({ key: 'WaitingScene' });
  }

  create() {
    // Фон
    this.add.rectangle(400, 300, 800, 600, 0x1a1a2e);

    // Заголовок
    this.add.text(400, 150, '🏃 FLOW FLIGHT', {
      fontSize: '48px',
      fill: '#00ffff',
      fontFamily: 'Arial',
      fontStyle: 'bold',
    }).setOrigin(0.5);

    // Статус подключения
    this.statusText = this.add.text(400, 280, 'Подключение...', {
      fontSize: '28px',
      fill: '#ffffff',
      fontFamily: 'Arial',
    }).setOrigin(0.5);

    // Информация об очереди
    this.queueText = this.add.text(400, 340, '', {
      fontSize: '22px',
      fill: '#aaaaaa',
      fontFamily: 'Arial',
    }).setOrigin(0.5);

    // Анимированные точки
    this.dots = '';
    this.time.addEvent({
      delay: 500,
      callback: () => {
        this.dots = this.dots.length >= 3 ? '' : this.dots + '.';
      },
      loop: true,
    });

    // Подключаемся к серверу
    this.connectToServer();
  }

  update() {
    if (gameState.phase === 'connecting' || gameState.phase === 'queue') {
      // Анимация ожидания
    }
  }

  connectToServer() {
    socket = io(serverUrl, {
      auth: {
        sessionId: sessionId,
        spiritId: spiritId,
      },
    });

    socket.on('connect', () => {
      console.log('Connected to server');
      gameState.myId = socket.id;
      this.statusText.setText('Подключено!');

      setTimeout(() => {
        socket.emit('join-queue', 'flow-flight');
        gameState.phase = 'queue';
        this.statusText.setText('Поиск игроков...');
      }, 500);
    });

    socket.on('queue-status', (data) => {
      this.queueText.setText(`Игроков: ${data.playersInQueue} / ${data.playersNeeded}`);
    });

    socket.on('match-found', (data) => {
      console.log('Match found:', data);
      gameState.players = data.players;
      this.statusText.setText('Матч найден!');
      this.queueText.setText('Подготовка...');
    });

    socket.on('game-countdown', (data) => {
      gameState.phase = 'countdown';
      gameState.countdown = data.count;

      if (data.count > 0) {
        this.statusText.setText(data.count.toString());
        this.statusText.setFontSize('96px');
        this.statusText.setColor('#ffff00');
      } else {
        this.statusText.setText('СТАРТ!');
        this.statusText.setColor('#00ff00');
      }
      this.queueText.setText('');
    });

    socket.on('game-start', (data) => {
      console.log('Game started:', data);
      gameState.phase = 'playing';
      gameState.seed = data.seed;
      gameState.players = data.players;
      gameState.finishDistance = data.finishDistance || 3000;
      gameState.noObstacles = data.noObstacles || false;
      gameState.obstacleSettings = data.obstacleSettings || {
        count: 50,
        minSpacing: 150,
        safeZoneStart: 500,
      };
      this.scene.start('GameScene');
    });

    socket.on('error', (data) => {
      console.error('Socket error:', data);
      this.statusText.setText('Ошибка: ' + data.message);
    });

    socket.on('disconnect', () => {
      console.log('Disconnected from server');
      this.statusText.setText('Отключено от сервера');
    });
  }
}

// ============ Основная игровая сцена ============
class GameScene extends Phaser.Scene {
  constructor() {
    super({ key: 'GameScene' });
  }

  create() {
    this.players = {};
    this.obstacles = [];
    this.cameraX = 0;
    this.targetCameraX = 0; // Целевая позиция камеры для плавной интерполяции
    this.cameraLerpSpeed = 0.1; // Скорость интерполяции камеры (0.1 = плавно, 1 = мгновенно)
    this.finishDistance = gameState.finishDistance || 3000;
    this.finishLine = null;

    // Создаём фон и дорожки
    this.createBackground();
    this.createTracks();

    // Генерируем препятствия
    this.generateObstacles(gameState.seed);

    // Создаём финишную линию
    this.createFinishLine();

    // Создаём игроков
    this.createPlayers();

    // UI
    this.createUI();

    // Управление
    this.setupControls();

    // Socket события
    this.setupSocketEvents();
  }

  createBackground() {
    // Градиентный фон (небо)
    const graphics = this.add.graphics();
    graphics.fillGradientStyle(0x1a1a3e, 0x1a1a3e, 0x0a0a1a, 0x0a0a1a, 1);
    graphics.fillRect(0, 0, 800, 600);

    // Облака (декоративные)
    for (let i = 0; i < 5; i++) {
      const cloud = this.add.ellipse(
        100 + i * 200,
        50 + Math.random() * 40,
        80 + Math.random() * 40,
        30,
        0x2a2a4a,
        0.5
      );
      cloud.setScrollFactor(0);
    }
  }

  createTracks() {
    // Единая дорожка для всех игроков
    const track = GAME_CONFIG.track;
    const graphics = this.add.graphics();
    graphics.lineStyle(3, 0x3a3a5a, 1);
    graphics.strokeRect(0, track.groundY - 5, 800, 3);
    graphics.setScrollFactor(0);
  }

  createFinishLine() {
    // Контейнер для финишной линии
    this.finishLine = this.add.container(0, 0);

    // Финишная линия - вертикальная полоса с шашечками
    const lineGraphics = this.add.graphics();

    // Фоновая полоса
    lineGraphics.fillStyle(0xffffff, 0.3);
    lineGraphics.fillRect(-5, 50, 10, 500);

    // Шашечный узор
    const squareSize = 20;
    for (let row = 0; row < 25; row++) {
      for (let col = 0; col < 2; col++) {
        const isWhite = (row + col) % 2 === 0;
        lineGraphics.fillStyle(isWhite ? 0xffffff : 0x000000, 0.8);
        lineGraphics.fillRect(-squareSize + col * squareSize, 50 + row * squareSize, squareSize, squareSize);
      }
    }
    this.finishLine.add(lineGraphics);

    // Надпись "ФИНИШ"
    const finishText = this.add.text(0, 30, '🏁 ФИНИШ', {
      fontSize: '24px',
      fill: '#ffff00',
      fontFamily: 'Arial',
      fontStyle: 'bold',
      stroke: '#000000',
      strokeThickness: 3,
    }).setOrigin(0.5);
    this.finishLine.add(finishText);
  }

  createPlayers() {
    const track = GAME_CONFIG.track;
    const baseY = track.groundY - GAME_CONFIG.playerSize / 2;

    // Сначала создаём всех игроков кроме локального (они будут сзади)
    // Потом создаём локального игрока (он будет спереди)
    const sortedPlayers = [...gameState.players].sort((a, b) => {
      const aIsMe = a.id === gameState.myId ? 1 : 0;
      const bIsMe = b.id === gameState.myId ? 1 : 0;
      return aIsMe - bIsMe; // Локальный игрок создаётся последним = сверху
    });

    sortedPlayers.forEach((playerData, sortedIndex) => {
      const isMe = playerData.id === gameState.myId;
      // Находим оригинальный индекс для цвета
      const originalIndex = gameState.players.findIndex(p => p.id === playerData.id);
      const colorScheme = PLAYER_COLORS[originalIndex % PLAYER_COLORS.length];

      // Контейнер для спирита
      const container = this.add.container(100, baseY);

      // Устанавливаем depth: локальный игрок всегда сверху
      // Другие игроки имеют меньший depth
      if (isMe) {
        container.setDepth(100); // Локальный игрок всегда на переднем плане
      } else {
        container.setDepth(10 + sortedIndex); // Другие игроки сзади
      }

      // Свечение
      const glow = this.add.ellipse(0, 0, 60, 60, colorScheme.glow, 0.3);
      container.add(glow);

      // Тело спирита (овал - как бегущий персонаж)
      const body = this.add.ellipse(0, 0, GAME_CONFIG.playerSize, GAME_CONFIG.playerSize * 0.8, colorScheme.main);
      container.add(body);

      // Глаза (смотрят вперёд)
      const eyeL = this.add.circle(8, -6, 6, 0xffffff);
      const eyeR = this.add.circle(8, 6, 6, 0xffffff);
      const pupilL = this.add.circle(10, -6, 3, 0x000000);
      const pupilR = this.add.circle(10, 6, 3, 0x000000);
      container.add([eyeL, eyeR, pupilL, pupilR]);

      // Ноги (анимированные)
      const legL = this.add.rectangle(-5, 18, 8, 16, colorScheme.main);
      const legR = this.add.rectangle(5, 18, 8, 16, colorScheme.main);
      container.add([legL, legR]);

      // Индикатор "это я" - только для локального игрока
      if (isMe) {
        const indicator = this.add.text(0, -45, '▼ ВЫ', {
          fontSize: '14px',
          fill: '#00ffff',
          fontFamily: 'Arial',
        }).setOrigin(0.5);
        container.add(indicator);
      }

      // Для других игроков: уменьшаем масштаб и добавляем прозрачность
      // чтобы визуально показать что они "сзади"
      if (!isMe) {
        container.setScale(0.75); // Немного меньше
        container.setAlpha(0.6); // Полупрозрачные
      }

      this.players[playerData.id] = {
        container,
        glow,
        body,
        legL,
        legR,
        isMe,
        isBot: playerData.isBot || false,
        baseY: baseY,
        y: baseY,
        velocityY: 0,
        isJumping: false,
        distance: 0,
        isAlive: true,
        runPhase: 0,
        colorScheme, // Сохраняем цветовую схему
      };
    });
  }

  generateObstacles(seed) {
    // Если режим без препятствий или count = 0 - не генерируем
    const settings = gameState.obstacleSettings || { count: 50, minSpacing: 150, safeZoneStart: 500 };

    if (gameState.noObstacles || settings.count === 0) {
      console.log('No obstacles mode enabled');
      return;
    }

    // Простой PRNG - ИДЕНТИЧНЫЙ серверу!
    let state = seed;
    const random = () => {
      state = (state * 1664525 + 1013904223) % 4294967296;
      return state / 4294967296;
    };

    // Настройки из сервера
    const obstacleCount = settings.count;
    const minSpacing = settings.minSpacing;
    const safeZoneStart = settings.safeZoneStart;
    const finishDistance = this.finishDistance || 3000;

    // Зона для размещения препятствий
    const availableDistance = finishDistance - safeZoneStart - 100;

    console.log(`Generating ${obstacleCount} obstacles on single track from ${safeZoneStart} to ${finishDistance}`);

    const track = GAME_CONFIG.track;
    const positions = [];

    // Генерируем позиции для единой дорожки
    for (let i = 0; i < obstacleCount; i++) {
      const basePosition = safeZoneStart + (availableDistance / obstacleCount) * i;
      const randomOffset = (random() - 0.5) * (availableDistance / obstacleCount) * 0.5;
      let x = basePosition + randomOffset;

      // Проверяем минимальное расстояние от предыдущих
      for (const prevX of positions) {
        if (Math.abs(x - prevX) < minSpacing) {
          x = prevX + minSpacing + random() * 50;
        }
      }

      x = Math.max(safeZoneStart, Math.min(x, finishDistance - 100));
      positions.push(x);
    }

    positions.sort((a, b) => a - b);

    // Создаём препятствия
    positions.forEach((x, id) => {
      const typeRoll = random();
      const type = typeRoll < 0.6 ? 'cactus' : typeRoll < 0.84 ? 'rock' : 'bird';

      let width, height, y, color;
      switch (type) {
        case 'cactus':
          width = 20 + random() * 15;
          height = 40 + random() * 30;
          y = track.groundY - height;
          color = 0x2d5a27;
          break;
        case 'rock':
          width = 30 + random() * 20;
          height = 25 + random() * 15;
          y = track.groundY - height;
          color = 0x5a5a6a;
          break;
        case 'bird':
          width = 25;
          height = 20;
          y = track.groundY - 60 - random() * 30;
          color = 0x8a4a9a;
          break;
      }

      this.obstacles.push({
        id: id,
        x: x,
        y: y,
        width: width,
        height: height,
        type: type,
        color: color,
        graphics: null,
      });
    });

    console.log(`Generated ${this.obstacles.length} obstacles`);
  }

  createUI() {
    // Панель UI
    const uiPanel = this.add.rectangle(400, 30, 780, 50, 0x000000, 0.5);
    uiPanel.setScrollFactor(0);

    // Дистанция
    this.distanceText = this.add.text(30, 20, '0 м', {
      fontSize: '24px',
      fill: '#ffffff',
      fontFamily: 'Arial',
      fontStyle: 'bold',
    }).setScrollFactor(0);

    // Лидерборд
    this.leaderboardText = this.add.text(770, 20, '', {
      fontSize: '16px',
      fill: '#aaaaaa',
      fontFamily: 'Arial',
      align: 'right',
    }).setOrigin(1, 0).setScrollFactor(0);

    // Подсказка по управлению
    this.hintText = this.add.text(400, 570, '⬆️ ПРОБЕЛ / ТАПНИ для прыжка', {
      fontSize: '16px',
      fill: '#666666',
      fontFamily: 'Arial',
    }).setOrigin(0.5).setScrollFactor(0);

    // Скрываем подсказку через 3 секунды
    this.time.delayedCall(3000, () => {
      this.tweens.add({
        targets: this.hintText,
        alpha: 0,
        duration: 1000,
      });
    });
  }

  setupControls() {
    // Клавиатура - пробел, стрелка вверх, W
    this.input.keyboard.on('keydown-SPACE', () => this.jump());
    this.input.keyboard.on('keydown-UP', () => this.jump());
    this.input.keyboard.on('keydown-W', () => this.jump());

    // Touch / клик
    this.input.on('pointerdown', () => this.jump());
  }

  jump() {
    const myPlayer = this.players[gameState.myId];
    if (myPlayer && myPlayer.isAlive && !myPlayer.isJumping) {
      socket.emit('player-input', { action: 'jump' });
    }
  }

  setupSocketEvents() {
    socket.on('game-state', (state) => {
      let maxDistance = 0;
      let myPlayerData = null;

      state.players.forEach((p) => {
        if (this.players[p.id]) {
          const player = this.players[p.id];
          player.distance = p.distance;
          player.isAlive = p.isAlive;
          player.y = p.y;
          player.isJumping = p.isJumping;

          // Запоминаем данные своего игрока
          if (p.id === gameState.myId) {
            myPlayerData = p;
          }

          // Находим максимальную дистанцию среди живых
          if (p.isAlive && p.distance > maxDistance) {
            maxDistance = p.distance;
          }
        }
      });

      // Камера: если свой игрок жив - следуем за ним, иначе за лидером
      // Используем targetCameraX для плавной интерполяции
      if (myPlayerData && myPlayerData.isAlive) {
        this.targetCameraX = myPlayerData.distance;
      } else {
        this.targetCameraX = maxDistance;
      }

      // КЛИЕНТСКАЯ ПРОВЕРКА ФИНИША - если кто-то достиг финиша, завершаем игру
      if (maxDistance >= this.finishDistance && gameState.phase === 'playing') {
        console.log('Client detected finish! Max distance:', maxDistance, 'Finish:', this.finishDistance);
        this.handleClientFinish();
      }
    });

    socket.on('player-eliminated', (data) => {
      console.log('Player eliminated:', data);
      if (this.players[data.playerId]) {
        const player = this.players[data.playerId];
        player.isAlive = false;
        player.container.setAlpha(0.3);

        // Эффект выбывания
        this.tweens.add({
          targets: player.container,
          scaleX: 0.5,
          scaleY: 0.5,
          angle: 45,
          duration: 500,
        });
      }
    });

    socket.on('player-disconnected', (data) => {
      console.log('Player disconnected:', data);
      if (this.players[data.playerId]) {
        this.players[data.playerId].container.destroy();
        delete this.players[data.playerId];
      }
    });

    socket.on('game-end', (data) => {
      console.log('Game ended:', data);
      gameState.phase = 'finished';
      this.scene.start('ResultScene', { results: data.results, rewards: data.rewards });
    });
  }

  // Клиентская обработка финиша (если сервер не отправил game-end)
  handleClientFinish() {
    if (gameState.phase !== 'playing') return;

    gameState.phase = 'finished';
    console.log('Client finishing game...');

    // Собираем результаты из локальных данных игроков
    const results = Object.entries(this.players)
      .map(([id, player]) => ({
        playerId: id,
        spiritId: '',
        distance: Math.floor(player.distance),
        place: 0,
        isBot: player.isBot || false,
      }))
      .sort((a, b) => b.distance - a.distance)
      .map((r, index) => ({ ...r, place: index + 1 }));

    // Пустые награды (сервер не отправил)
    const rewards = [];

    // Переходим на экран результатов
    this.scene.start('ResultScene', { results, rewards });
  }

  update(time, delta) {
    if (gameState.phase !== 'playing') return;

    // Плавная интерполяция камеры к целевой позиции
    // Это устраняет резкие скачки при смерти игрока
    const lerpFactor = Math.min(1, this.cameraLerpSpeed * (delta / 16.67)); // Нормализуем по delta
    this.cameraX = Phaser.Math.Linear(this.cameraX, this.targetCameraX, lerpFactor);

    // Обновляем позиции всех игроков
    const track = GAME_CONFIG.track;
    const myPlayer = this.players[gameState.myId];

    Object.values(this.players).forEach((player) => {
      // Позиция X относительно камеры
      const screenX = player.distance - this.cameraX + 100;

      // Y позиция с учётом прыжка
      const groundY = track.groundY - GAME_CONFIG.playerSize / 2;
      const jumpOffset = player.baseY - player.y;
      const screenY = groundY - jumpOffset;

      player.container.setPosition(screenX, screenY);

      // Скрываем если вне экрана
      const isVisible = screenX > -50 && screenX < GAME_CONFIG.width + 50;
      player.container.setVisible(isVisible);

      // Динамическая видимость других игроков
      // Они становятся более видимыми когда позиция отличается
      if (!player.isMe && myPlayer && player.isAlive) {
        // Разница по горизонтали (дистанция)
        const distanceDiff = Math.abs(player.distance - myPlayer.distance);
        // Разница по вертикали (прыжок)
        const yDiff = Math.abs(player.y - myPlayer.y);

        // Базовая прозрачность 0.4, увеличивается при разнице позиций
        // Максимум 0.9 когда игроки далеко друг от друга
        const distanceVisibility = Math.min(distanceDiff / 100, 1) * 0.3; // до +0.3 от дистанции
        const jumpVisibility = Math.min(yDiff / 50, 1) * 0.2; // до +0.2 от прыжка
        const targetAlpha = Math.min(0.4 + distanceVisibility + jumpVisibility, 0.9);

        // Плавный переход прозрачности
        const currentAlpha = player.container.alpha;
        player.container.setAlpha(Phaser.Math.Linear(currentAlpha, targetAlpha, 0.1));

        // Масштаб тоже слегка меняется - ближе к игроку = чуть меньше
        const targetScale = 0.7 + Math.min(distanceDiff / 200, 1) * 0.15; // 0.7 - 0.85
        const currentScale = player.container.scaleX;
        const newScale = Phaser.Math.Linear(currentScale, targetScale, 0.1);
        player.container.setScale(newScale);
      }

      if (!player.isAlive) return;

      // Анимация бега (если не в прыжке и жив)
      if (!player.isJumping && player.isAlive) {
        player.runPhase += delta * 0.015;
        const legOffset = Math.sin(player.runPhase) * 8;
        player.legL.setPosition(-5, 18 + legOffset);
        player.legR.setPosition(5, 18 - legOffset);
      }

      // Пульсация свечения
      if (player.isAlive) {
        const pulse = 1 + Math.sin(time / 200) * 0.15;
        player.glow.setScale(pulse);
      }
    });

    // Отрисовка препятствий
    this.renderObstacles();

    // Обновляем финишную линию
    this.updateFinishLine();

    // Обновляем UI
    this.updateUI();
  }

  updateFinishLine() {
    if (!this.finishLine) return;

    // Позиция финишной линии относительно камеры
    const finishScreenX = this.finishDistance - this.cameraX + 100;

    // Показываем линию только когда она в видимой области
    const isVisible = finishScreenX > -100 && finishScreenX < GAME_CONFIG.width + 100;
    this.finishLine.setVisible(isVisible);

    if (isVisible) {
      this.finishLine.setPosition(finishScreenX, 0);
    }
  }

  renderObstacles() {
    const viewStart = this.cameraX - 100;
    const viewEnd = this.cameraX + GAME_CONFIG.width + 100;
    const track = GAME_CONFIG.track;

    this.obstacles.forEach((obs) => {
      const screenX = obs.x - this.cameraX + 100;

      if (obs.x >= viewStart && obs.x <= viewEnd) {
        if (!obs.graphics) {
          obs.graphics = this.add.graphics();
          obs.graphics.fillStyle(obs.color, 1);

          if (obs.type === 'cactus') {
            // Кактус - прямоугольник с "руками"
            obs.graphics.fillRect(-obs.width / 2, -obs.height, obs.width, obs.height);
            obs.graphics.fillRect(-obs.width, -obs.height * 0.7, obs.width / 2, obs.height * 0.3);
            obs.graphics.fillRect(obs.width / 2, -obs.height * 0.5, obs.width / 2, obs.height * 0.25);
          } else if (obs.type === 'rock') {
            // Камень - скруглённый прямоугольник
            obs.graphics.fillRoundedRect(-obs.width / 2, -obs.height, obs.width, obs.height, 8);
          } else if (obs.type === 'bird') {
            // Птица - треугольники как крылья
            obs.graphics.fillTriangle(-obs.width / 2, 0, 0, -obs.height / 2, obs.width / 2, 0);
            obs.graphics.fillTriangle(-obs.width / 2, 0, 0, obs.height / 2, obs.width / 2, 0);
          }
        }

        obs.graphics.setPosition(screenX, track.groundY);
        obs.graphics.setVisible(true);
      } else if (obs.graphics) {
        obs.graphics.setVisible(false);
      }
    });
  }

  updateUI() {
    const myPlayer = this.players[gameState.myId];
    if (myPlayer) {
      this.distanceText.setText(`${Math.floor(myPlayer.distance)} м`);
    }

    // Лидерборд
    const sorted = Object.entries(this.players)
      .map(([id, p]) => ({
        id,
        distance: p.distance,
        isAlive: p.isAlive,
        isMe: p.isMe,
      }))
      .sort((a, b) => b.distance - a.distance);

    const leaderboard = sorted.map((p, i) => {
      const medal = i === 0 ? '🥇' : i === 1 ? '🥈' : '🥉';
      const you = p.isMe ? ' (ВЫ)' : '';
      const status = p.isAlive ? '' : ' 💀';
      return `${medal} ${Math.floor(p.distance)}м${you}${status}`;
    }).join('\n');

    this.leaderboardText.setText(leaderboard);
  }
}

// ============ Сцена результатов ============
class ResultScene extends Phaser.Scene {
  constructor() {
    super({ key: 'ResultScene' });
  }

  init(data) {
    this.results = data.results || [];
    this.rewards = data.rewards || [];
  }

  create() {
    // Фон
    this.add.rectangle(400, 300, 800, 600, 0x1a1a2e);

    // Определяем победителя
    const winner = this.results[0];
    const isMyWin = winner && winner.playerId === gameState.myId;
    const myResult = this.results.find(r => r.playerId === gameState.myId);
    const myPlace = myResult ? myResult.place : 0;

    // Большой заголовок с победителем
    if (isMyWin) {
      this.add.text(400, 50, '🎉 ВЫ ПОБЕДИЛИ! 🎉', {
        fontSize: '38px',
        fill: '#ffd700',
        fontFamily: 'Arial',
        fontStyle: 'bold',
      }).setOrigin(0.5);
    } else {
      const winnerLabel = winner?.isBot ? 'Бот' : 'Игрок';
      this.add.text(400, 50, `🏆 ПОБЕДИТЕЛЬ: ${winnerLabel}`, {
        fontSize: '32px',
        fill: '#ffd700',
        fontFamily: 'Arial',
        fontStyle: 'bold',
      }).setOrigin(0.5);

      // Показываем место игрока
      if (myPlace > 0) {
        this.add.text(400, 90, `Вы заняли ${myPlace} место`, {
          fontSize: '22px',
          fill: '#aaaaaa',
          fontFamily: 'Arial',
        }).setOrigin(0.5);
      }
    }

    // Места
    const medals = ['🥇', '🥈', '🥉'];
    const placeColors = ['#ffd700', '#c0c0c0', '#cd7f32'];

    this.results.forEach((result, index) => {
      const y = 140 + index * 80;
      const isMe = result.playerId === gameState.myId;
      const color = placeColors[index] || '#ffffff';
      const isWinner = index === 0;

      // Подсветка победителя
      if (isWinner) {
        this.add.rectangle(400, y, 700, 70, 0x3a3a1a, 0.5);
      }

      // Медаль
      this.add.text(80, y, medals[index] || `${result.place}.`, {
        fontSize: '42px',
      }).setOrigin(0.5);

      // Место
      const placeLabel = isWinner ? 'ПОБЕДИТЕЛЬ' : `${result.place} место`;
      this.add.text(180, y, placeLabel, {
        fontSize: isWinner ? '26px' : '24px',
        fill: color,
        fontFamily: 'Arial',
        fontStyle: 'bold',
      }).setOrigin(0, 0.5);

      // Дистанция
      this.add.text(420, y, `${result.distance} м`, {
        fontSize: '24px',
        fill: isMe ? '#00ffff' : '#ffffff',
        fontFamily: 'Arial',
      }).setOrigin(0, 0.5);

      // Бот или игрок
      const typeLabel = result.isBot ? '🤖' : '👤';
      this.add.text(530, y, typeLabel, {
        fontSize: '24px',
      }).setOrigin(0, 0.5);

      if (isMe) {
        this.add.text(580, y, '◄ ВЫ', {
          fontSize: '22px',
          fill: '#00ffff',
          fontFamily: 'Arial',
          fontStyle: 'bold',
        }).setOrigin(0, 0.5);
      }
    });

    // Награды
    const myReward = this.rewards.find(r => r.playerId === gameState.myId);
    if (myReward) {
      this.add.text(400, 400, '💎 Ваши награды:', {
        fontSize: '22px',
        fill: '#aaaaaa',
        fontFamily: 'Arial',
      }).setOrigin(0.5);

      const rewardsItems = [];
      if (myReward.lumens > 0) rewardsItems.push(`✨ ${myReward.lumens} Люменов`);
      if (myReward.xp > 0) rewardsItems.push(`⭐ ${myReward.xp} XP`);
      if (myReward.ton > 0) rewardsItems.push(`💰 ${myReward.ton} TON!`);
      if (myReward.hasPulseCapsule) rewardsItems.push('💊 Пульс-капсула!');

      this.add.text(400, 440, rewardsItems.join('   '), {
        fontSize: '20px',
        fill: '#00ff88',
        fontFamily: 'Arial',
      }).setOrigin(0.5);
    }

    // Кнопка "Ещё раз"
    const playAgainBtn = this.add.text(300, 520, '🔄 Ещё раз', {
      fontSize: '22px',
      fill: '#ffffff',
      fontFamily: 'Arial',
      backgroundColor: '#335533',
      padding: { x: 20, y: 10 },
    }).setOrigin(0.5).setInteractive({ useHandCursor: true });

    playAgainBtn.on('pointerover', () => playAgainBtn.setStyle({ fill: '#00ff00' }));
    playAgainBtn.on('pointerout', () => playAgainBtn.setStyle({ fill: '#ffffff' }));
    playAgainBtn.on('pointerdown', () => {
      if (socket) socket.disconnect();
      gameState.phase = 'connecting';
      this.scene.start('WaitingScene');
    });

    // Кнопка выхода
    const exitBtn = this.add.text(500, 520, '🚪 Выйти', {
      fontSize: '22px',
      fill: '#ffffff',
      fontFamily: 'Arial',
      backgroundColor: '#553333',
      padding: { x: 20, y: 10 },
    }).setOrigin(0.5).setInteractive({ useHandCursor: true });

    exitBtn.on('pointerover', () => exitBtn.setStyle({ fill: '#ff6666' }));
    exitBtn.on('pointerout', () => exitBtn.setStyle({ fill: '#ffffff' }));
    exitBtn.on('pointerdown', () => {
      if (socket) socket.disconnect();
      window.close();
      setTimeout(() => window.location.reload(), 100);
    });
  }
}

// ============ Конфигурация Phaser ============
const config = {
  type: Phaser.AUTO,
  width: GAME_CONFIG.width,
  height: GAME_CONFIG.height,
  parent: 'game-container',
  backgroundColor: '#1a1a2e',
  scale: {
    mode: Phaser.Scale.FIT,
    autoCenter: Phaser.Scale.CENTER_BOTH,
  },
  scene: [WaitingScene, GameScene, ResultScene],
};

// Запускаем игру
document.getElementById('loading').classList.add('hidden');
const game = new Phaser.Game(config);
