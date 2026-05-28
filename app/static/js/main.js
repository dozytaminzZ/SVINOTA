document.addEventListener('DOMContentLoaded', () => {
    const optionsTrigger = document.querySelector('.info-btn, .table-menu-btn');
    const optionsOverlay = document.getElementById('options-overlay');
    const optionsClose = document.querySelector('.options-close');
    const cardsOpenButtons = document.querySelectorAll('[data-cards-open]');
    const cardsOverlay = document.getElementById('cards-modal');
    const cardsClose = document.querySelector('.cards-modal-close');
    const howToOpenButtons = document.querySelectorAll('[data-how-to-open]');
    const howToOverlay = document.getElementById('how-to-modal');
    const howToClose = document.querySelector('.how-to-close');
    const howToSlides = Array.from(document.querySelectorAll('[data-how-to-slide]'));
    const howToDots = Array.from(document.querySelectorAll('[data-how-to-dot]'));
    const howToPrev = document.querySelector('[data-how-to-prev]');
    const howToNext = document.querySelector('[data-how-to-next]');
    const howToCurrent = document.querySelector('[data-how-to-current]');
    const soundToggle = document.querySelector('[data-sound-toggle]');
    const copyCodeButton = document.querySelector('[data-copy-code]');
    const colorChoiceOverlay = document.getElementById('color-choice-overlay');
    const colorChoiceClose = document.querySelector('.color-choice-close');
    const colorChoiceButtons = document.querySelectorAll('[data-card-color-choice]');
    let lastCardsTrigger = null;
    let lastHowToTrigger = null;
    let currentHowToSlide = 0;
    let pendingColorChoice = null;
    const musicApi = window.SvinotaMusic;

    if (musicApi) {
        musicApi.init({
            startOnFirstInteraction: true
        });
    }

    const updateSoundToggle = () => {
        if (!soundToggle) {
            return;
        }

        if (!musicApi) {
            return;
        }

        const isEnabled = musicApi.isEnabled();
        soundToggle.dataset.muted = String(!isEnabled);
        soundToggle.textContent = isEnabled ? 'Выключить звук' : 'Включить звук';
    };

    const closeOptions = () => {
        if (optionsOverlay) {
            optionsOverlay.hidden = true;
        }

        if (optionsTrigger) {
            optionsTrigger.focus();
        }
    };

    if (optionsTrigger && optionsOverlay && optionsClose) {
        const openOptions = () => {
            optionsOverlay.hidden = false;
            optionsClose.focus();
        };

        optionsTrigger.addEventListener('click', openOptions);
        optionsClose.addEventListener('click', closeOptions);

        optionsOverlay.addEventListener('click', (event) => {
            if (event.target === optionsOverlay) {
                closeOptions();
            }
        });

    }

    const closeCardsModal = () => {
        if (!cardsOverlay) {
            return;
        }

        cardsOverlay.hidden = true;

        if (lastCardsTrigger) {
            lastCardsTrigger.focus();
        }
    };

    if (cardsOverlay && cardsClose) {
        cardsOpenButtons.forEach((button) => {
            button.addEventListener('click', () => {
                lastCardsTrigger = button;
                closeOptions();
                cardsOverlay.hidden = false;
                cardsClose.focus();
            });
        });

        cardsClose.addEventListener('click', closeCardsModal);

        cardsOverlay.addEventListener('click', (event) => {
            if (event.target === cardsOverlay) {
                closeCardsModal();
            }
        });
    }

    const renderHowToSlide = (index) => {
        if (!howToSlides.length) {
            return;
        }

        currentHowToSlide = (index + howToSlides.length) % howToSlides.length;

        howToSlides.forEach((slide, slideIndex) => {
            slide.classList.toggle('is-active', slideIndex === currentHowToSlide);
        });

        howToDots.forEach((dot, dotIndex) => {
            dot.classList.toggle('is-active', dotIndex === currentHowToSlide);
        });

        if (howToCurrent) {
            howToCurrent.textContent = String(currentHowToSlide + 1);
        }
    };

    const closeHowToModal = () => {
        if (!howToOverlay) {
            return;
        }

        howToOverlay.hidden = true;

        if (lastHowToTrigger) {
            lastHowToTrigger.focus();
        }
    };

    if (howToOverlay && howToClose) {
        howToOpenButtons.forEach((button) => {
            button.addEventListener('click', () => {
                lastHowToTrigger = button;
                closeOptions();
                renderHowToSlide(0);
                howToOverlay.hidden = false;
                howToClose.focus();
            });
        });

        howToClose.addEventListener('click', closeHowToModal);

        howToOverlay.addEventListener('click', (event) => {
            if (event.target === howToOverlay) {
                closeHowToModal();
            }
        });

        howToPrev?.addEventListener('click', () => {
            renderHowToSlide(currentHowToSlide - 1);
        });

        howToNext?.addEventListener('click', () => {
            renderHowToSlide(currentHowToSlide + 1);
        });

        howToDots.forEach((dot) => {
            dot.addEventListener('click', () => {
                renderHowToSlide(Number(dot.dataset.howToDot || 0));
            });
        });
    }

    document.addEventListener('keydown', (event) => {
        if (event.key !== 'Escape') {
            return;
        }

        if (cardsOverlay && !cardsOverlay.hidden) {
            closeCardsModal();
            return;
        }

        if (howToOverlay && !howToOverlay.hidden) {
            closeHowToModal();
            return;
        }

        if (optionsOverlay && !optionsOverlay.hidden) {
            closeOptions();
            return;
        }

        if (colorChoiceOverlay && !colorChoiceOverlay.hidden) {
            closeColorChoice(null);
        }
    });

    document.addEventListener('keydown', (event) => {
        if (!howToOverlay || howToOverlay.hidden) {
            return;
        }

        if (event.key === 'ArrowLeft') {
            event.preventDefault();
            renderHowToSlide(currentHowToSlide - 1);
        }

        if (event.key === 'ArrowRight') {
            event.preventDefault();
            renderHowToSlide(currentHowToSlide + 1);
        }
    });

    function closeColorChoice(color) {
        if (!colorChoiceOverlay) {
            return;
        }

        colorChoiceOverlay.hidden = true;

        if (pendingColorChoice) {
            pendingColorChoice(color);
            pendingColorChoice = null;
        }
    }

    function chooseCardColor() {
        if (!colorChoiceOverlay) {
            return Promise.resolve(null);
        }

        colorChoiceOverlay.hidden = false;

        const firstButton = colorChoiceOverlay.querySelector('[data-card-color-choice]');

        if (firstButton) {
            firstButton.focus();
        }

        return new Promise((resolve) => {
            pendingColorChoice = resolve;
        });
    }

    colorChoiceButtons.forEach((button) => {
        button.addEventListener('click', () => {
            closeColorChoice(button.dataset.cardColorChoice);
        });
    });

    if (colorChoiceClose) {
        colorChoiceClose.addEventListener('click', () => {
            closeColorChoice(null);
        });
    }

    if (colorChoiceOverlay) {
        colorChoiceOverlay.addEventListener('click', (event) => {
            if (event.target === colorChoiceOverlay) {
                closeColorChoice(null);
            }
        });
    }

    if (soundToggle) {
        updateSoundToggle();
        soundToggle.addEventListener('click', () => {
            if (musicApi) {
                musicApi.toggle();
                updateSoundToggle();
                return;
            }

            const isMuted = soundToggle.dataset.muted === 'true';
            soundToggle.dataset.muted = String(!isMuted);
            soundToggle.textContent = isMuted ? 'Выключить звук' : 'Включить звук';
        });
    }

    if (copyCodeButton) {
        copyCodeButton.addEventListener('click', async () => {
            const code = copyCodeButton.dataset.copyCode;

            if (!code) {
                return;
            }

            try {
                await navigator.clipboard.writeText(code);
                copyCodeButton.classList.add('is-copied');
                copyCodeButton.setAttribute('aria-label', 'ID игры скопирован');
            } catch (error) {
                copyCodeButton.setAttribute('aria-label', 'Не удалось скопировать ID');
            }
        });
    }

    const waitingRoomPage = document.querySelector('[data-waiting-room-id]');
    const waitingRoomId = waitingRoomPage?.dataset.waitingRoomId;
    const initialWaitingPlayersCount = Number(waitingRoomPage?.dataset.waitingPlayersCount || 0);

    if (waitingRoomPage && waitingRoomId) {
        const checkWaitingRoomStatus = async () => {
            try {
                const response = await fetch(`/lobby/status?room_id=${encodeURIComponent(waitingRoomId)}`, {
                    headers: {
                        Accept: 'application/json'
                    }
                });

                if (!response.ok) {
                    return;
                }

                const payload = await response.json();

                if (payload.room?.status === 'playing' && payload.game_url) {
                    window.location.href = payload.game_url;
                    return;
                }

                if (payload.room?.status === 'waiting' && payload.room.players_count !== initialWaitingPlayersCount) {
                    window.location.reload();
                }
            } catch (error) {
                // The next poll will retry quietly.
            }
        };

        window.setInterval(checkWaitingRoomStatus, 1000);
        checkWaitingRoomStatus();
    }

    document.querySelectorAll('.card-info-tile').forEach((cardTile) => {
        cardTile.addEventListener('click', () => {
            const isFlipped = cardTile.classList.toggle('is-flipped');
            cardTile.setAttribute('aria-pressed', String(isFlipped));
        });
    });

    const gamePage = document.querySelector('.game-page');
    const playZone = document.querySelector('.play-zone');
    const deckZone = document.querySelector('.deck-zone');
    const deckCard = document.querySelector('.deck-card');
    const playerHand = document.querySelector('.player-hand');
    const directionArrow = document.querySelector('.direction-arrow');
    const svintusButton = document.querySelector('.svintus-btn');
    const roomId = gamePage?.dataset.roomId;
    const currentUserId = gamePage?.dataset.currentUserId;
    const resultUrl = gamePage?.dataset.resultUrl;
    const playerNamesScript = document.getElementById('game-player-names');
    let playerNames = {};

    if (playerNamesScript) {
        try {
            playerNames = JSON.parse(playerNamesScript.textContent || '{}');
        } catch (error) {
            playerNames = {};
        }
    }


    let socket = null;
    let isDrawingCard = false;
    let playedCardIndex = 0;

    if (window.io && gamePage && roomId) {
        socket = io();

        socket.emit('game:join', {
            room_id: roomId
        });

        socket.emit('game:state', {
            room_id: roomId
        });

        socket.on('game:joined', (payload) => {
            console.log('Joined game room:', payload);
        });

        socket.on('game:error', (payload) => {
            console.error('Game error:', payload);
            showGameError(payload?.error || 'Действие сейчас нельзя выполнить');

            document.querySelectorAll('.play-card.is-origin-hidden').forEach((card) => {
                card.classList.remove('is-origin-hidden');
            });

            requestGameState();
        });

        socket.on('game:action', (payload) => {
            console.log('Game action:', payload);
        });

        socket.on('game:state', (state) => {
            console.log('New game state:', state);
            renderGameState(state);
        });

        socket.on('game:card_played', (payload) => {
            console.log('Another player played card:', payload);

            /*
                Здесь позже можно сделать анимацию:
                карта летит от аватара другого игрока к play-zone.
            */
        });
    }

    function rectsIntersect(a, b) {
        return !(
            a.right < b.left ||
            a.left > b.right ||
            a.bottom < b.top ||
            a.top > b.bottom
        );
    }

    function createGhost(card) {
        const rect = card.getBoundingClientRect();
        const ghost = card.cloneNode(true);

        ghost.classList.remove('play-card', 'is-selected');
        ghost.classList.add('drag-card-ghost');

        ghost.style.left = `${rect.left}px`;
        ghost.style.top = `${rect.top}px`;
        ghost.style.width = `${rect.width}px`;
        ghost.style.height = `${rect.height}px`;

        document.body.appendChild(ghost);

        return ghost;
    }

    function requestGameState() {
        if (!socket || !roomId) {
            return;
        }

        socket.emit('game:state', {
            room_id: roomId
        });
    }

    async function postGameAction(endpoint, payload = {}) {
        if (!roomId) {
            return null;
        }

        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Accept: 'application/json'
            },
            body: JSON.stringify({
                room_id: roomId,
                ...payload
            })
        });

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            showGameError(data.error || 'Действие сейчас нельзя выполнить');
            return null;
        }

        if (data.state) {
            renderGameState(data.state);
        }

        return data;
    }

    async function fetchGameState() {
        if (!roomId) {
            return;
        }

        try {
            const response = await fetch(`/game/state?room_id=${encodeURIComponent(roomId)}`, {
                headers: {
                    Accept: 'application/json'
                }
            });

            if (!response.ok) {
                return;
            }

            const data = await response.json();

            if (data.state) {
                renderGameState(data.state);
            }
        } catch (error) {
            // Socket events or the next poll will retry.
        }
    }

    function showGameError(message) {
        const turnStatus = document.querySelector('.turn-status');

        if (!turnStatus) {
            return;
        }

        turnStatus.dataset.error = message;
        turnStatus.classList.add('has-error');

        window.setTimeout(() => {
            turnStatus.classList.remove('has-error');
            delete turnStatus.dataset.error;
        }, 1800);
    }

    function getPlayerName(playerId) {
        return playerNames[playerId] || 'Игрок';
    }

    function getCardAssetValue(card) {
        if (!card) {
            return 0;
        }

        if (card.color === null || card.color === 'grey') {
            return 0;
        }

        if (card.type === 'number') {
            return Number(card.value || 0);
        }

        if (card.type === 'skip') {
            return 8;
        }

        if (card.type === 'reverse') {
            return 9;
        }

        if (card.type === 'cover_deck') {
            return 10;
        }

        return 11;
    }

    function getCardImageSrc(card) {
        const color = card?.color || 'grey';
        const value = getCardAssetValue(card);

        return `/static/cards/${color}/${color}${value}.jpg`;
    }

    function getCardLabel(card) {
        if (!card) {
            return 'Карта';
        }

        if (card.type === 'number') {
            return `${card.color} ${card.value}`;
        }

        return `${card.color || 'grey'} ${card.type}`;
    }

    function createCardButton(card) {
        const button = document.createElement('button');
        const image = document.createElement('img');

        button.className = 'play-card';
        button.type = 'button';
        button.dataset.cardId = card.id;
        button.dataset.cardColor = card.color || 'grey';
        button.dataset.cardType = card.type;

        image.src = getCardImageSrc(card);
        image.alt = getCardLabel(card);

        button.appendChild(image);

        return button;
    }

    function renderHand(cards = []) {
        if (!playerHand) {
            return;
        }

        playerHand.replaceChildren();

        cards.forEach((card) => {
            const button = createCardButton(card);
            playerHand.appendChild(button);
            bindCardDrag(button);
        });

        updateHandLayout();
        updateYouCardsCount();
    }

    function renderTopDiscard(card) {
        const target = document.querySelector('.play-slot');

        if (!target || !card) {
            return;
        }

        const tableCard = createCardButton(card);

        tableCard.classList.remove('play-card');
        tableCard.classList.add('table-played-card', 'table-played-card-3');
        tableCard.removeAttribute('style');
        tableCard.disabled = true;

        target.classList.add('has-card');
        target.replaceChildren(tableCard);
    }

    function renderPlayers(players = []) {
        players.forEach((player) => {
            const seat = document.querySelector(`[data-player-id="${player.id}"]`);

            if (!seat) {
                return;
            }

            seat.classList.toggle('active-player', Boolean(player.is_current));

            const counter = seat.querySelector('.player-badge span, .side-badge span');

            if (counter) {
                counter.textContent = `${player.hand_count} карт`;
            }

            seat.querySelectorAll('.opponent-hand, .side-hand').forEach((hand) => {
                const cardClass = hand.classList.contains('side-hand') ? 'side-card' : 'mini-card';
                const spacing = cardClass === 'side-card' ? 9 : 10;
                const count = player.hand_count;

                hand.replaceChildren();

                for (let index = 0; index < count; index += 1) {
                    const back = document.createElement('span');

                    back.className = `card-back ${cardClass}`;
                    back.style.setProperty('--x', `${(index - ((count - 1) / 2)) * spacing}px`);
                    hand.appendChild(back);
                }
            });
        });
    }

    function renderTurnStatus(state) {
        const turnStrong = document.querySelector('.turn-status strong');

        if (turnStrong) {
            turnStrong.textContent = getPlayerName(state.current_player_id);
        }
    }

    function renderGameState(state) {
        if (!state) {
            return;
        }

        updateDirectionArrow(state.direction);
        renderPlayers(state.players || []);
        renderTurnStatus(state);
        renderTopDiscard(state.top_discard);

        if (Array.isArray(state.viewer_hand)) {
            renderHand(state.viewer_hand);
        }

        if (state.status === 'finished' && resultUrl) {
            window.location.href = resultUrl;
        }
    }

    function createDeckGhost() {
        if (!deckCard) {
            return null;
        }

        const rect = deckCard.getBoundingClientRect();
        const ghost = deckCard.cloneNode(true);

        ghost.classList.remove('deck-card');
        ghost.classList.add('draw-card-ghost');

        ghost.style.left = `${rect.left}px`;
        ghost.style.top = `${rect.top}px`;
        ghost.style.width = `${rect.width}px`;
        ghost.style.height = `${rect.height}px`;

        document.body.appendChild(ghost);

        return ghost;
    }

    function animateGhostToPlayZone(ghost) {
        return new Promise((resolve) => {
            const target = document.querySelector('.play-slot');

            if (!target) {
                ghost.remove();
                resolve();
                return;
            }

            const targetRect = target.getBoundingClientRect();
            const ghostRect = ghost.getBoundingClientRect();

            const left = targetRect.left + targetRect.width / 2 - ghostRect.width / 2;
            const top = targetRect.top + targetRect.height / 2 - ghostRect.height / 2;

            ghost.classList.add('is-dropping');
            ghost.style.left = `${left}px`;
            ghost.style.top = `${top}px`;
            ghost.style.transform = 'rotate(0deg) scale(0.92)';

            window.setTimeout(() => {
                ghost.remove();
                resolve();
            }, 230);
        });
    }

    function animateGhostBack(ghost, card) {
        return new Promise((resolve) => {
            const rect = card.getBoundingClientRect();

            ghost.classList.add('is-returning');
            ghost.style.left = `${rect.left}px`;
            ghost.style.top = `${rect.top}px`;
            ghost.style.transform = 'rotate(0deg) scale(1)';
            ghost.style.opacity = '0.4';

            window.setTimeout(() => {
                ghost.remove();
                card.classList.remove('is-origin-hidden');
                resolve();
            }, 230);
        });
    }

    async function emitPlayCard(card) {
        const cardId = card.dataset.cardId;

        if (!cardId) {
            console.error('card_id is missing on card element');
            return false;
        }

        const chosenColor = card.dataset.cardColor === 'grey'
            ? await chooseCardColor()
            : null;

        if (card.dataset.cardColor === 'grey' && !chosenColor) {
            return false;
        }

        if (!socket) {
            postGameAction('/game/play', {
                card_id: cardId,
                chosen_color: chosenColor
            });
            return true;
        }

        if (!roomId) {
            console.error('room_id is missing');
            return false;
        }

        socket.emit('game:play', {
            room_id: roomId,
            card_id: cardId,
            chosen_color: chosenColor
        });

        return true;
    }

    function updateDirectionArrow(direction) {
        if (!directionArrow) {
            return;
        }

        const normalizedDirection = Number(direction) === -1 ? -1 : 1;
        const isCounterClockwise = normalizedDirection === -1;

        directionArrow.textContent = isCounterClockwise ? '↺' : '↻';
        directionArrow.dataset.direction = String(normalizedDirection);
        directionArrow.classList.toggle('is-counter-clockwise', isCounterClockwise);
        directionArrow.classList.toggle('is-clockwise', !isCounterClockwise);
    }

    function removePlayedCard(card) {
        card.remove();
        updateHandLayout();
        updateYouCardsCount();
    }

    function placeCardOnTable(card) {
        const target = document.querySelector('.play-slot');

        if (!target) {
            return;
        }

        const tableCard = card.cloneNode(true);
        const position = Math.floor(Math.random() * 5) + 1;

        playedCardIndex += 1;

        tableCard.classList.remove('play-card', 'is-selected', 'is-origin-hidden');
        tableCard.classList.add('table-played-card', `table-played-card-${position}`);
        tableCard.removeAttribute('style');
        tableCard.removeAttribute('data-drag-ready');
        tableCard.disabled = true;
        tableCard.style.zIndex = String(playedCardIndex);

        target.classList.add('has-card');
        target.appendChild(tableCard);
    }

    function updateHandLayout() {
        if (!playerHand) {
            return;
        }

        const cards = Array.from(playerHand.querySelectorAll('.play-card'));
        const spacing = cards.length > 1 ? Math.min(46, 900 / (cards.length - 1)) : 0;
        const center = (cards.length - 1) / 2;

        cards.forEach((card, index) => {
            card.style.setProperty('--x', `${(index - center) * spacing}px`);
        });
    }

    function updateYouCardsCount() {
        if (!playerHand) {
            return;
        }

        const counter = document.querySelector('.you-badge span');

        if (counter) {
            counter.textContent = `${playerHand.querySelectorAll('.play-card').length} карт`;
        }
    }

    function animateDeckGhostToCard(ghost, card) {
        return new Promise((resolve) => {
            if (!ghost || !card) {
                resolve();
                return;
            }

            const targetRect = card.getBoundingClientRect();
            const ghostRect = ghost.getBoundingClientRect();
            const left = targetRect.left + targetRect.width / 2 - ghostRect.width / 2;
            const top = targetRect.top + targetRect.height / 2 - ghostRect.height / 2;
            const shouldResize = card.classList?.contains('play-card');

            ghost.classList.add('is-drawing');
            ghost.style.left = `${left}px`;
            ghost.style.top = `${top}px`;

            if (shouldResize) {
                ghost.style.width = `${targetRect.width}px`;
                ghost.style.height = `${targetRect.height}px`;
            }

            ghost.style.transform = 'rotate(0deg) scale(1)';
            ghost.style.opacity = '0.72';

            window.setTimeout(() => {
                ghost.remove();
                resolve();
            }, 330);
        });
    }

    function emitDrawCard() {
        if (!roomId) {
            return;
        }

        if (!socket) {
            postGameAction('/game/draw');
            return;
        }

        socket.emit('game:draw', {
            room_id: roomId
        });
    }

    async function drawCardFromDeck() {
        if (!playerHand || isDrawingCard) {
            return;
        }

        isDrawingCard = true;
        deckZone?.classList.add('is-drawing');

        const ghost = createDeckGhost();
        const target = playerHand.querySelector('.play-card:last-child') || playerHand;

        await animateDeckGhostToCard(ghost, target);
        deckZone?.classList.remove('is-drawing');
        emitDrawCard();
        isDrawingCard = false;
    }

    function bindCardDrag(card) {
        if (card.dataset.dragReady === 'true') {
            return;
        }

        card.dataset.dragReady = 'true';

            let ghost = null;
            let startX = 0;
            let startY = 0;
            let shiftX = 0;
            let shiftY = 0;
            let isDragging = false;

            card.addEventListener('pointerdown', (event) => {
                if (event.button !== 0) {
                    return;
                }

                event.preventDefault();

                const rect = card.getBoundingClientRect();

                startX = event.clientX;
                startY = event.clientY;
                shiftX = event.clientX - rect.left;
                shiftY = event.clientY - rect.top;

                isDragging = true;

                card.classList.add('is-selected');
                ghost = createGhost(card);
                card.setPointerCapture(event.pointerId);
            });

            card.addEventListener('pointermove', (event) => {
                if (!isDragging || !ghost) {
                    return;
                }

                const dx = Math.abs(event.clientX - startX);
                const dy = Math.abs(event.clientY - startY);

                if (dx > 3 || dy > 3) {
                    card.classList.add('is-origin-hidden');
                }

                ghost.style.left = `${event.clientX - shiftX}px`;
                ghost.style.top = `${event.clientY - shiftY}px`;

                if (playZone) {
                    const isOverDiscard = rectsIntersect(
                        ghost.getBoundingClientRect(),
                        playZone.getBoundingClientRect()
                    );

                    playZone.classList.toggle('is-drop-target', isOverDiscard);
                }
            });

            card.addEventListener('pointerup', async (event) => {
                if (!isDragging) {
                    return;
                }

                isDragging = false;

                try {
                    card.releasePointerCapture(event.pointerId);
                } catch (error) {
                    // Иногда pointer capture уже может быть снят браузером.
                }

                card.classList.remove('is-selected');

                if (!ghost || !playZone) {
                    card.classList.remove('is-origin-hidden');
                    return;
                }

                const isOverDiscard = rectsIntersect(
                    ghost.getBoundingClientRect(),
                    playZone.getBoundingClientRect()
                );

                playZone.classList.remove('is-drop-target');

                if (isOverDiscard) {
                    const isSent = await emitPlayCard(card);

                    if (!isSent) {
                        await animateGhostBack(ghost, card);
                        return;
                    }

                    await animateGhostToPlayZone(ghost);
                    placeCardOnTable(card);
                    removePlayedCard(card);
                    return;
                }

                await animateGhostBack(ghost, card);
            });

            card.addEventListener('pointercancel', async () => {
                isDragging = false;
                card.classList.remove('is-selected');

                if (playZone) {
                    playZone.classList.remove('is-drop-target');
                }

                if (ghost) {
                    await animateGhostBack(ghost, card);
                }
            });
    }

    function initCardDrag() {
        document.querySelectorAll('.play-card').forEach((card) => {
            bindCardDrag(card);
        });
    }

    if (deckZone) {
        deckZone.addEventListener('click', drawCardFromDeck);
        deckZone.addEventListener('keydown', (event) => {
            if (event.key !== 'Enter' && event.key !== ' ') {
                return;
            }

            event.preventDefault();
            drawCardFromDeck();
        });
    }

    updateHandLayout();
    initCardDrag();

    if (gamePage && roomId && !socket) {
        fetchGameState();
        window.setInterval(fetchGameState, 1800);
    }

    if (svintusButton) {
        svintusButton.addEventListener('click', () => {
            if (!socket || !roomId) {
                console.warn('Cannot call SVINTUS: socket or room_id is missing');
                return;
            }

            socket.emit('game:svintus', {
                room_id: roomId
            });
        });
    }
});
