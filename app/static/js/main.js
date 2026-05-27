document.addEventListener('DOMContentLoaded', () => {
    const infoButton = document.querySelector('.info-btn');
    const optionsOverlay = document.getElementById('options-overlay');
    const optionsClose = document.querySelector('.options-close');
    const soundToggle = document.querySelector('[data-sound-toggle]');

    if (!infoButton || !optionsOverlay || !optionsClose) {
        return;
    }

    const openOptions = () => {
        optionsOverlay.hidden = false;
        optionsClose.focus();
    };

    const closeOptions = () => {
        optionsOverlay.hidden = true;
        infoButton.focus();
    };

    infoButton.addEventListener('click', openOptions);
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

    if (soundToggle) {
        soundToggle.addEventListener('click', () => {
            const isMuted = soundToggle.dataset.muted === 'true';

            soundToggle.dataset.muted = String(!isMuted);
            soundToggle.textContent = isMuted ? 'Выключить звук' : 'Включить звук';
        });
    }
});
