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
});
