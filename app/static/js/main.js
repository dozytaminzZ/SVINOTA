document.addEventListener('DOMContentLoaded', () => {
    const optionsTrigger = document.querySelector('.info-btn, .table-menu-btn');
    const optionsOverlay = document.getElementById('options-overlay');
    const optionsClose = document.querySelector('.options-close');
    const soundToggle = document.querySelector('[data-sound-toggle]');
    const copyCodeButton = document.querySelector('[data-copy-code]');

    if (optionsTrigger && optionsOverlay && optionsClose) {
        const openOptions = () => {
            optionsOverlay.hidden = false;
            optionsClose.focus();
        };

        const closeOptions = () => {
            optionsOverlay.hidden = true;
            optionsTrigger.focus();
        };

        optionsTrigger.addEventListener('click', openOptions);
        optionsClose.addEventListener('click', closeOptions);

        optionsOverlay.addEventListener('click', (event) => {
            if (event.target === optionsOverlay) {
                closeOptions();
            }
        });

        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && !optionsOverlay.hidden) {
                closeOptions();
            }
        });
    }

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

    const gamePage = document.querySelector('.game-page');
    const discardZone = document.querySelector('.discard-zone');
    const svintusButton = document.querySelector('.svintus-btn');
    const roomId = gamePage?.dataset.roomId;

    let socket = null;

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

            /*
                Позже сюда нужно добавить нормальную перерисовку:
                - renderHand(state.viewer_hand)
                - renderTopDiscard(state.top_discard)
                - renderPlayers(state.players)
                - renderTurnStatus(state.current_player_id)

                Пока оставляем console.log, чтобы не ломать текущий моковый интерфейс.
            */
        });

        socket.on('game:card_played', (payload) => {
            console.log('Another player played card:', payload);

            /*
                Здесь позже можно сделать анимацию:
                карта летит от аватара другого игрока к discard-zone.
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

    function animateGhostToDiscard(ghost) {
        return new Promise((resolve) => {
            const target = document.querySelector('.discard-slot');

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
            ghost.style.opacity = '0.25';

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
            card.classList.remove('is-origin-hidden');
            return;
        }

        if (!socket) {
            console.warn('Socket.IO is not connected. Front animation works, but backend event was not sent.');
            card.classList.remove('is-origin-hidden');
            return;
        }

        if (!roomId) {
            console.error('room_id is missing');
            card.classList.remove('is-origin-hidden');
            return;
        }

        socket.emit('game:play', {
            room_id: roomId,
            card_id: cardId,
            chosen_color: null
        });
    }

    function initCardDrag() {
        document.querySelectorAll('.play-card').forEach((card) => {
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

                if (discardZone) {
                    const isOverDiscard = rectsIntersect(
                        ghost.getBoundingClientRect(),
                        discardZone.getBoundingClientRect()
                    );

                    discardZone.classList.toggle('is-drop-target', isOverDiscard);
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

                if (!ghost || !discardZone) {
                    card.classList.remove('is-origin-hidden');
                    return;
                }

                const isOverDiscard = rectsIntersect(
                    ghost.getBoundingClientRect(),
                    discardZone.getBoundingClientRect()
                );

                discardZone.classList.remove('is-drop-target');

                if (isOverDiscard) {
                    await animateGhostToDiscard(ghost);
                    emitPlayCard(card);
                    return;
                }

                await animateGhostBack(ghost, card);
            });

            card.addEventListener('pointercancel', async () => {
                isDragging = false;
                card.classList.remove('is-selected');

                if (discardZone) {
                    discardZone.classList.remove('is-drop-target');
                }

                if (ghost) {
                    await animateGhostBack(ghost, card);
                }
            });
        });
    }

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