// --- CENTRALIZED COMPONENT IMPORTS ---
import '@material/web/button/filled-tonal-button.js';
import '@material/web/button/outlined-button.js';
import '@material/web/button/text-button.js';
import '@material/web/iconbutton/icon-button.js';
import '@material/web/chips/assist-chip.js';
import '@material/web/textfield/outlined-text-field.js';
import '@material/web/button/filled-button.js';
// --- END OF IMPORTS ---

import { applyM3Theme } from './theme.js';

document.addEventListener('DOMContentLoaded', () => {
  const body = document.body;
  const isNewsPage = document.getElementById('news-container');

  // --- Shared Theming Logic ---
  const colorPicker = document.getElementById('color-picker');
  const themeToggleButton = document.getElementById('theme-toggle-button');
  const themeIcon = document.getElementById('theme-icon');
  let isDark;

  function updateTheme() {
    // Default color is green (#4CAF50)
    const color = colorPicker?.value || localStorage.getItem('accentColor') || '#4CAF50';
    
    // Default mode is dark
    isDark = localStorage.getItem('theme') !== 'light'; 
    
    applyM3Theme(color, isDark);
    localStorage.setItem('accentColor', color);
    
    if (themeIcon) {
        themeIcon.textContent = isDark ? 'light_mode' : 'dark_mode';
    }
  }

  if (colorPicker) {
    colorPicker.value = localStorage.getItem('accentColor') || '#4CAF50';
    colorPicker.addEventListener('input', () => {
        localStorage.setItem('accentColor', colorPicker.value);
        updateTheme();
    });
  }
  
  if (themeToggleButton) {
    themeToggleButton.addEventListener('click', () => {
      isDark = !isDark;
      localStorage.setItem('theme', isDark ? 'dark' : 'light');
      updateTheme();
    });
  }
  
  // Initial theme setup on page load
  updateTheme();

  
  // --- NEWS PAGE LOGIC ---
  if (isNewsPage) {
    const newsContainer = document.getElementById('news-container');
    const loadingSentinel = document.getElementById('loading-sentinel');
    const pageHeader = document.querySelector('.page-header');
    const category = body.dataset.category;
    
    // A flag to distinguish page types
    const isForYouPage = !category;

    let currentPage = 1;
    let isLoading = false;
    let allNewsLoaded = false;
    
    let currentUtterance;
    
    let audioContext;
    let currentGainNode;
    let audioLoopId;
    let isMusicPlaying = false;
    const speechSynthesis=window.speechSynthesis;
    
    // This part is unchanged
    const scales = {
        major: [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88],
        minor: [261.63, 277.18, 311.13, 349.23, 392.00, 415.30, 466.16]
    };
    const moods = {
        'Politics': { scale: scales.minor, instrument: 'sawtooth', tempo: 0.30, pattern: [6, 4, 2, 0, 5, 3, 1] },
        'World': { scale: scales.minor, instrument: 'sine', tempo: 0.35, pattern: [6, 4, 5, 3, 2, 1] },
        'Business': { scale: scales.major, instrument: 'sine', tempo: 0.25, pattern: [0, 2, 4, 5, 6, 5, 4] },
        'Technology':{ scale: scales.major, instrument: 'square', tempo: 0.25, pattern: [0, 4, 5, 2, 6] },
        'Health': { scale: scales.major, instrument: 'sine', tempo: 0.40, pattern: [0, 2, 4, 5, 4, 2, 0] },
        'default': { scale: scales.major, instrument: 'sine', tempo: 0.30, pattern: [0, 2, 4, 5] }
    };

    function playMusic(title, subgenre) {
        if (isMusicPlaying) stopMusic();
        try {
            if (!audioContext) audioContext = new (window.AudioContext || window.webkitAudioContext)();
            currentGainNode = audioContext.createGain();
            currentGainNode.gain.setValueAtTime(0.5, audioContext.currentTime);
            currentGainNode.connect(audioContext.destination);

            const mood = moods[subgenre] || moods[category] || moods['default'];
            const { pattern: selectedMelody, tempo: noteDuration, instrument, scale } = mood;
            const hash = title.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
            const startNoteIndex = hash % scale.length;
            
            let noteIndex = 0;
            const playNextNote = () => {
                const oscillator = audioContext.createOscillator();
                const frequency = scale[(startNoteIndex + selectedMelody[noteIndex]) % scale.length];
                oscillator.type = instrument;
                oscillator.frequency.setValueAtTime(frequency, audioContext.currentTime);
                currentGainNode.gain.cancelScheduledValues(audioContext.currentTime);
                currentGainNode.gain.setValueAtTime(0, audioContext.currentTime);
                currentGainNode.gain.linearRampToValueAtTime(0.5, audioContext.currentTime + noteDuration / 4);
                currentGainNode.gain.linearRampToValueAtTime(0, audioContext.currentTime + noteDuration);
                oscillator.connect(currentGainNode);
                oscillator.start();
                oscillator.stop(audioContext.currentTime + noteDuration);
                noteIndex = (noteIndex + 1) % selectedMelody.length;
                audioLoopId = setTimeout(playNextNote, noteDuration * 1000);
            };
            playNextNote();
            isMusicPlaying = true;
        } catch (e) { console.error("Web Audio API Error:", e); }
    }
    
    function stopMusic() {
        if (audioLoopId) clearTimeout(audioLoopId);
        audioLoopId = null;
        if (currentGainNode && audioContext) {
            currentGainNode.gain.cancelScheduledValues(audioContext.currentTime);
            currentGainNode.gain.linearRampToValueAtTime(0, audioContext.currentTime + 0.05);
        }
        isMusicPlaying = false;
    }

    const musicPlayButton = document.getElementById('music-play-button');
    const musicPauseButton = document.getElementById('music-pause-button');
    function toggleMusic() {
        if (isMusicPlaying) {
            stopMusic();
            musicPlayButton.style.display = 'block';
            musicPauseButton.style.display = 'none';
        } else {
            const currentSlide = newsContainer.querySelector('.news-slide');
            if (currentSlide) {
                playMusic(currentSlide.dataset.title, currentSlide.dataset.subgenre);
                musicPlayButton.style.display = 'none';
                musicPauseButton.style.display = 'block';
            }
        }
    }
    if(musicPlayButton && musicPauseButton){
        musicPlayButton.addEventListener('click', toggleMusic);
        musicPauseButton.addEventListener('click', toggleMusic);
    }

    newsContainer.addEventListener('scroll', () => {
        if (newsContainer.scrollTop > 10) pageHeader.classList.add('scrolled');
        else pageHeader.classList.remove('scrolled');
        if (speechSynthesis.speaking) speechSynthesis.cancel();
    });

    const createNewsSlide = (item) => {
        const slide = document.createElement('div');
        slide.className = 'news-slide';
        slide.dataset.title = item.title;
        slide.dataset.subgenre = item.subgenre;
        const imagePath = `/static/images/subgenres/${item.img_subgenre}.png`;
        slide.innerHTML = `
            <div class="background-image" style="background-image: url('${imagePath}');" onerror="this.style.backgroundImage='url(/static/images/subgenres/Default.jpg)'"></div>
            <div class="news-content">
                <h2>${item.title}</h2>
                <md-assist-chip label="${item.subgenre}"></md-assist-chip>
                <p>${item.summary}</p>
                <div class="action-buttons">
                    <md-outlined-button href="${item.link}" target="_blank">Read Full Article</md-outlined-button>
                    <md-icon-button class="tts-button" aria-label="Read summary aloud">
                        <span class="material-symbols-outlined">volume_up</span>
                    </md-icon-button>
                </div>
            </div>`;
        
        slide.querySelector('.tts-button').addEventListener('click', (e) => {
            e.stopPropagation();
            if (speechSynthesis.speaking) {
                speechSynthesis.cancel();
            } else {
                currentUtterance = new SpeechSynthesisUtterance(item.summary);
                speechSynthesis.speak(currentUtterance);
            }
        });
        return slide;
    };

    const loadNews = async () => {
        if (isLoading || allNewsLoaded) return;
        isLoading = true;
        
        loadingSentinel.innerHTML = `<div class="skeleton-card">
    <div class="skeleton title"></div>
    <div class="skeleton chip"></div>
    <div class="skeleton text"></div>
    <div class="skeleton text short"></div> <div class="skeleton button"></div>
</div>`;


        try {
            const apiUrl = isForYouPage
                ? `/api/get_news_for_you?page=${currentPage}`
                : `/api/get_news?category=${category}&page=${currentPage}`;
            
            const response = await fetch(apiUrl);
            const newsItems = await response.json();

            if (newsItems.length > 0) {
                newsItems.forEach(item => newsContainer.insertBefore(createNewsSlide(item), loadingSentinel));
                currentPage++;
                // The special check for 'isForYouPage' has been removed from here.
            } else {
                allNewsLoaded = true;
            }
        } catch (error) {
            console.error("Failed to fetch news:", error);
            loadingSentinel.innerHTML = "Failed to load news.";
        }
        isLoading = false;
        
        if (allNewsLoaded) {
             const message = isForYouPage 
                ? "Latest updates from your bookmarks." 
                : `You're all caught up on ${category} news.`;
             loadingSentinel.innerHTML = `<div id="end-of-feed" style="text-align: center; padding: 2rem; border-radius: 28px;"><h3>You're All Caught Up!</h3><p>${message}</p><md-filled-tonal-button href="/">Back to Home</md-filled-tonal-button></div>`;
        }
    };
    
    // The 'if' condition has been removed. The observer is now created for ALL news pages.
    const observer = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting) {
            loadNews();
        }
    }, { threshold: 0.1 });
    observer.observe(loadingSentinel);

    // Call loadNews() immediately to fetch the first batch of articles on any news page.
    loadNews(); 
    
  } // End of if(isNewsPage)
});

// Helper functions like applyM3Theme are assumed to be present.
