import '@material/web/button/filled-tonal-button.js';
import '@material/web/switch/switch.js';
import '@material/web/iconbutton/icon-button.js';
import '@material/web/progress/circular-progress.js';
import '@material/web/chips/assist-chip.js';
import '@material/web/button/outlined-button.js';

import { applyM3Theme } from './theme.js';

document.addEventListener('DOMContentLoaded', () => {
  const body = document.body;
  const isNewsPage = body.dataset.category;

  // --- Shared Theming Logic ---
  const colorPicker = document.getElementById('color-picker');
  const themeToggleButton = document.getElementById('theme-toggle-button');
  const themeIcon = document.getElementById('theme-icon');
  let isDark;
  function updateTheme() {
    const color = colorPicker?.value || localStorage.getItem('accentColor') || '#4CAF50';
    const savedTheme = localStorage.getItem('theme');
    isDark = savedTheme ? savedTheme === 'dark' : true;
    applyM3Theme(color, isDark);
    localStorage.setItem('accentColor', color);
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
    if (themeIcon) {
        themeIcon.textContent = isDark ? 'light_mode' : 'dark_mode';
    }
  }
  if (colorPicker) {
    colorPicker.value = localStorage.getItem('accentColor') || '#4CAF50';
    colorPicker.addEventListener('input', updateTheme);
  }
  if (themeToggleButton) {
    themeToggleButton.addEventListener('click', () => {
      isDark = !isDark;
      localStorage.setItem('theme', isDark ? 'dark' : 'light');
      updateTheme();
    });
  }
  updateTheme();

  // --- NEWS PAGE LOGIC ---
  if (isNewsPage) {
    const newsContainer = document.getElementById('news-container');
    const loadingSentinel = document.getElementById('loading-sentinel');
    const category = body.dataset.category;
    const allCategories = body.dataset.allCategories.split(',');
    
    const categoryPrev = document.getElementById('category-prev');
    const categoryNext = document.getElementById('category-next');
    const slideNavUp = document.getElementById('slide-nav-up');
    const slideNavDown = document.getElementById('slide-nav-down');

    let currentPage = 1;
    let isLoading = false;
    let allNewsLoaded = false;
    let currentSlideIndex = 0;
    
    // --- MUSIC GENERATION LOGIC ---
    let audioContext;
    let currentGainNode;
    let audioLoopId;
    let isMusicPlaying = false;

    const majorScale = [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88];
    const melodies = {
      'Politics': [6, 4, 2, 0, 5, 3, 1], // More serious, descending
      'Business': [0, 2, 4, 5, 6, 5, 4], // Upbeat and energetic
      'Technology': [0, 4, 5, 2, 6], // Jumpy and futuristic
      'Sports': [0, 5, 6, 4, 2, 0], // Fast, repeating pattern
      'World': [6, 4, 5, 3, 2, 1], // Descending and dramatic
      'Health': [0, 2, 4, 5, 4, 2, 0], // Soothing and melodic
      'Automobile': [0, 2, 4, 5, 6],
      'Entertainment': [0, 2, 4, 6],
      'Environment': [0, 2, 4, 6],
      'Finance': [0, 6, 2, 4, 1, 5, 3],
      'India': [0, 2, 4, 6],
      'Lifestyle': [0, 2, 4, 6],
      'Opinion': [6, 4, 2, 0],
      'Science': [0, 4, 2, 6],
      'Travel': [0, 2, 4, 6]
    };

    function playMusic(title, subgenre) {
      if (isMusicPlaying) {
        stopMusic();
      }
      
      try {
        if (!audioContext) {
          audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }

        currentGainNode = audioContext.createGain();
        currentGainNode.gain.setValueAtTime(0.5, audioContext.currentTime);
        currentGainNode.connect(audioContext.destination);

        const selectedMelody = melodies[subgenre] || melodies[category] || melodies['Health'];
        const hash = title.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
        const startNoteIndex = hash % majorScale.length;
        const instrument = (hash % 2 === 0) ? 'sine' : 'sawtooth';

        let noteIndex = 0;
        
        function playNextNote() {
          const noteDuration = 0.25;
          const oscillator = audioContext.createOscillator();
          const frequency = majorScale[(startNoteIndex + selectedMelody[noteIndex]) % majorScale.length];
          
          oscillator.type = instrument;
          oscillator.frequency.setValueAtTime(frequency, audioContext.currentTime);
          
          currentGainNode.gain.setValueAtTime(0, audioContext.currentTime);
          currentGainNode.gain.linearRampToValueAtTime(0.5, audioContext.currentTime + noteDuration / 4);
          currentGainNode.gain.linearRampToValueAtTime(0, audioContext.currentTime + noteDuration);

          oscillator.connect(currentGainNode);
          oscillator.start();
          oscillator.stop(audioContext.currentTime + noteDuration);
          
          noteIndex++;
          if (noteIndex < selectedMelody.length) {
            audioLoopId = setTimeout(playNextNote, noteDuration * 1000);
          } else {
            noteIndex = 0;
            audioLoopId = setTimeout(playNextNote, noteDuration * 1000);
          }
        }
        playNextNote();
        isMusicPlaying = true;
      } catch (e) {
        console.error("Web Audio API not supported or failed to play sound:", e);
      }
    }
    
    function stopMusic() {
      if (audioLoopId) {
        clearTimeout(audioLoopId);
        audioLoopId = null;
      }
      if (currentGainNode && audioContext) {
        currentGainNode.gain.cancelScheduledValues(audioContext.currentTime);
        currentGainNode.gain.setValueAtTime(0, audioContext.currentTime);
      }
      if (audioContext) {
        audioContext.close().catch(e => console.error("Error closing audio context:", e));
        audioContext = null;
      }
      isMusicPlaying = false;
    }
    
    // --- Music control event listeners ---
    const musicPlayButton = document.getElementById('music-play-button');
    const musicPauseButton = document.getElementById('music-pause-button');
    
    function toggleMusic() {
        if (isMusicPlaying) {
            stopMusic();
            musicPlayButton.style.display = 'block';
            musicPauseButton.style.display = 'none';
        } else {
            const currentSlide = document.querySelectorAll('.news-slide')[currentSlideIndex];
            if (currentSlide) {
                playMusic(currentSlide.dataset.title, currentSlide.dataset.subgenre);
                musicPlayButton.style.display = 'none';
                musicPauseButton.style.display = 'block';
            }
        }
    }

    if (musicPlayButton && musicPauseButton) {
        musicPlayButton.addEventListener('click', toggleMusic);
        musicPauseButton.addEventListener('click', toggleMusic);
    }
    
    const catCurrentIndex = allCategories.indexOf(category);
    if (catCurrentIndex > 0) {
        categoryPrev.href = `/news/${allCategories[catCurrentIndex - 1]}`;
    } else {
        categoryPrev.style.display = 'none';
    }
    if (catCurrentIndex < allCategories.length - 1) {
        categoryNext.href = `/news/${allCategories[catCurrentIndex + 1]}`;
    } else {
        categoryNext.style.display = 'none';
    }

    const scrollToSlide = (index) => {
        const slideHeight = window.innerHeight;
        newsContainer.scrollTo({ top: index * slideHeight, behavior: 'smooth' });
    };
    slideNavUp.addEventListener('click', () => { if (currentSlideIndex > 0) scrollToSlide(currentSlideIndex - 1); });
    slideNavDown.addEventListener('click', () => {
        const slideCount = document.querySelectorAll('.news-slide').length;
        if (currentSlideIndex < slideCount - 1) scrollToSlide(currentSlideIndex + 1);
    });

    const updateSlideArrowVisibility = () => {
        const slideCount = document.querySelectorAll('.news-slide').length;
        slideNavUp.classList.toggle('show', currentSlideIndex > 0);
        slideNavDown.classList.toggle('show', currentSlideIndex < slideCount - 1);
    };

    newsContainer.addEventListener('scroll', () => {
        const slideHeight = window.innerHeight;
        const newSlideIndex = Math.round(newsContainer.scrollTop / slideHeight);
        
        if (newSlideIndex !== currentSlideIndex) {
            const slides = document.querySelectorAll('.news-slide');
            const currentSlide = slides[newSlideIndex];
            if (currentSlide && isMusicPlaying) {
                playMusic(currentSlide.dataset.title, currentSlide.dataset.subgenre);
            }
        }
        currentSlideIndex = newSlideIndex;
        updateSlideArrowVisibility();
    });

    const createNewsSlide = (item) => {
        const slide = document.createElement('div');
        slide.className = 'news-slide';
        slide.dataset.title = item.title;
        slide.dataset.subgenre = item.subgenre;
        const imagePath = `/static/images/subgenres/${item.img_subgenre}.png`;
        slide.innerHTML = `
            <div class="background-image" style="background-image: url('${imagePath}');" onerror="this.style.backgroundImage='url(/static/images/subgenres/Default.jpg)'"></div>
            <div class="scrim-overlay"></div>
            <div class="news-content">
                <h2>${item.title}</h2>
                <md-assist-chip label="${item.subgenre}"></md-assist-chip>
                <p>${item.summary}</p>
                <md-outlined-button href="${item.link}" target="_blank">Read Full Article</md-outlined-button>
            </div>`;
        return slide;
    };
    
    // --- Updated Load Logic ---
    const loadAllNews = async () => {
        if (isLoading || allNewsLoaded || !category) return;
        isLoading = true;
        loadingSentinel.classList.add('loading');
        loadingSentinel.innerHTML = `<div class="skeleton-card"><div class="skeleton title"></div><div class="skeleton chip"></div><div class="skeleton text"></div><div class="skeleton text"></div><div class="skeleton text-2"></div><div class="skeleton button"></div></div>`;

        let page = 1;
        let hasMorePages = true;

        while (hasMorePages) {
            try {
                const response = await fetch(`/api/get_news?category=${category}&page=${page}`);
                const newsItems = await response.json();

                if (newsItems.length > 0) {
                    newsItems.forEach(item => {
                        newsContainer.insertBefore(createNewsSlide(item), loadingSentinel);
                    });
                    page++;
                } else {
                    hasMorePages = false;
                    allNewsLoaded = true;
                }
            } catch (error) {
                console.error("Failed to fetch news:", error);
                hasMorePages = false;
            }
        }
        
        loadingSentinel.classList.remove('loading');
        if (allNewsLoaded) {
            loadingSentinel.classList.add('end');
            loadingSentinel.innerHTML = `<div id="end-of-feed"><h3>You're All Caught Up!</h3><p>You've seen all the latest news in the ${category} category.</p><md-filled-tonal-button href="/">Explore Other Categories</md-filled-tonal-button></div>`;
        } else {
            loadingSentinel.innerHTML = '';
        }
        updateSlideArrowVisibility();
        isLoading = false;
    };
    const toggley=()=>{
      const currentSlide = document.querySelectorAll('.news-slide')[currentSlideIndex];
      const newsContainer = document.getElementById('news-container');
      const firstNewsSlide = newsContainer.querySelector('.news-slide');
if(firstNewsSlide && currentSlide){
      if(isMusicPlaying){
      }
      else{
        const musicPlayButton = document.getElementById('music-play-button');
    const musicPauseButton = document.getElementById('music-pause-button');
    musicPauseButton.remove();
    musicPlayButton.remove();
    const currentSlide = document.querySelectorAll('.news-slide')[currentSlideIndex];
    playMusic(currentSlide.dataset.title, currentSlide.dataset.subgenre);
    }}
      }
    window,addEventListener("click",toggley)
    // Add event listener to stop music when leaving the page
    window.addEventListener('beforeunload', stopMusic);
    
    loadAllNews();
  }
});