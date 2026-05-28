document.addEventListener('DOMContentLoaded', () => {
    const optionsTrigger = document.querySelector('.info-btn, .table-menu-btn');
    const optionsOverlay = document.getElementById('options-overlay');
    const optionsClose = document.querySelector('.options-close');
    const cardsOpenButtons = document.querySelectorAll('[data-cards-open]');
    const cardsOverlay = document.getElementById('cards-modal');
    const cardsClose = document.querySelector('.cards-modal-close');
    const soundToggle = document.querySelector('[data-sound-toggle]');
    const copyCodeButton = document.querySelector('[data-copy-code]');
    let lastCardsTrigger = null;

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

    document.addEventListener('keydown', (event) => {
        if (event.key !== 'Escape') {
            return;
        }

        if (cardsOverlay && !cardsOverlay.hidden) {
            closeCardsModal();
            return;
        }

        if (optionsOverlay && !optionsOverlay.hidden) {
            closeOptions();
        }
    });

    if (soundToggle) {
        soundToggle.addEventListener('click', () => {
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
    const demoDeckCards = [
        { id: 'draw-red-4', src: '/static/cards/red/red4.jpg', name: 'Красная 4', color: 'red', type: 'number' },
        { id: 'draw-yellow-7', src: '/static/cards/yellow/yellow7.jpg', name: 'Желтая 7', color: 'yellow', type: 'number' },
        { id: 'draw-blue-8', src: '/static/cards/blue/blue8.jpg', name: 'Синяя 8', color: 'blue', type: 'number' },
        { id: 'draw-green-11', src: '/static/cards/green/green11.jpg', name: 'Зеленая спецкарта', color: 'green', type: 'special' },
        { id: 'draw-grey-0', src: '/static/cards/grey/grey0.jpg', name: 'Полисвин', color: 'grey', type: 'special' }
    ];

    let socket = null;
    let drawIndex = 0;
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

            document.querySelectorAll('.play-card.is-origin-hidden').forEach((card) => {
                card.classList.remove('is-origin-hidden');
            });
        });

        socket.on('game:action', (payload) => {
            console.log('Game action:', payload);
        });

        socket.on('game:state', (state) => {
            console.log('New game state:', state);
            updateDirectionArrow(state.direction);

            /*
                Позже сюда нужно добавить нормальную перерисовку:
                - renderHand(state.viewer_hand)
                - renderTopCard(state.top_card)
                - renderPlayers(state.players)
                - renderTurnStatus(state.current_player_id)

                Пока оставляем console.log, чтобы не ломать текущий моковый интерфейс.
            */
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

    function emitPlayCard(card) {
        const cardId = card.dataset.cardId;

        if (!cardId) {
            console.error('card_id is missing on card element');
            return;
        }

        if (!socket) {
            console.warn('Socket.IO is not connected. Front animation works, but backend event was not sent.');
            return;
        }

        if (!roomId) {
            console.error('room_id is missing');
            return;
        }

        socket.emit('game:play', {
            room_id: roomId,
            card_id: cardId,
            chosen_color: null
        });
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

    function createDrawnCard() {
        const cardData = demoDeckCards[drawIndex % demoDeckCards.length];
        const card = document.createElement('button');
        const image = document.createElement('img');

        drawIndex += 1;

        card.className = 'play-card is-origin-hidden';
        card.type = 'button';
        card.dataset.cardId = `${cardData.id}-${Date.now()}`;
        card.dataset.cardColor = cardData.color;
        card.dataset.cardType = cardData.type;

        image.src = cardData.src;
        image.alt = cardData.name;

        card.appendChild(image);

        return card;
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

            ghost.classList.add('is-drawing');
            ghost.style.left = `${left}px`;
            ghost.style.top = `${top}px`;
            ghost.style.width = `${targetRect.width}px`;
            ghost.style.height = `${targetRect.height}px`;
            ghost.style.transform = 'rotate(0deg) scale(1)';
            ghost.style.opacity = '0.72';

            window.setTimeout(() => {
                ghost.remove();
                resolve();
            }, 330);
        });
    }

    function emitDrawCard() {
        if (!socket || !roomId) {
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
        const card = createDrawnCard();

        playerHand.appendChild(card);
        bindCardDrag(card);
        updateHandLayout();
        updateYouCardsCount();

        await animateDeckGhostToCard(ghost, card);

        card.classList.remove('is-origin-hidden');
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
                    await animateGhostToPlayZone(ghost);
                    placeCardOnTable(card);
                    emitPlayCard(card);
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
