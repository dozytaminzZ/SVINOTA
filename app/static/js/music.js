(() => {
  const STORAGE_KEY = "svinota_music_enabled";
  const DEFAULT_TRACKS = [
    "/static/audio/1.mp3",
    "/static/audio/2.mp3",
    "/static/audio/3.mp3"
  ];

  const audio = new Audio();
  audio.preload = "auto";

  let playlist = [];
  let index = 0;
  let enabled = true;
  let userInteracted = false;

  const loadTrack = (trackIndex) => {
    if (!playlist.length) {
      return;
    }
    index = ((trackIndex % playlist.length) + playlist.length) % playlist.length;
    audio.src = playlist[index];
    audio.load();
  };

  const playCurrent = () => {
    audio.play().catch(() => {});
  };

  const nextTrack = () => {
    if (!playlist.length) {
      return;
    }
    loadTrack(index + 1);
    if (enabled && userInteracted) {
      playCurrent();
    }
  };

  const onFirstInteraction = () => {
    userInteracted = true;
    if (enabled) {
      playCurrent();
    }
  };

  const setEnabled = (value) => {
    enabled = Boolean(value);
    localStorage.setItem(STORAGE_KEY, enabled ? "1" : "0");

    if (!enabled) {
      audio.pause();
      audio.currentTime = 0;
      return;
    }

    if (userInteracted) {
      playCurrent();
    }
  };

  const toggle = () => {
    setEnabled(!enabled);
  };

  const init = (options = {}) => {
    playlist = Array.isArray(options.tracks) && options.tracks.length
      ? options.tracks
      : DEFAULT_TRACKS;

    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored !== null) {
      enabled = stored === "1";
    } else if (typeof options.enabled === "boolean") {
      enabled = options.enabled;
    }

    loadTrack(0);
    audio.addEventListener("ended", nextTrack);

    if (options.startOnFirstInteraction === false) {
      userInteracted = true;
      if (enabled) {
        playCurrent();
      }
    } else {
      document.addEventListener("pointerdown", onFirstInteraction, { once: true });
      document.addEventListener("keydown", onFirstInteraction, { once: true });
    }
  };

  window.SvinotaMusic = {
    init,
    toggle,
    setEnabled,
    isEnabled: () => enabled
  };
})();
