const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('file-upload');
const uploadContent = document.getElementById('upload-content');
const imagePreview = document.getElementById('image-preview');
const predictBtn = document.getElementById('predict-btn');
const resultsContainer = document.getElementById('results-container');
const resultLabel = document.getElementById('result-label');
const resultEmoji = document.getElementById('result-emoji');
const resultTitle = document.getElementById('result-title');
const resultMessage = document.getElementById('result-message');
const resetBtn = document.getElementById('reset-btn');

const probabilityContainer = document.getElementById('probability-container');
const probDogText = document.getElementById('prob-dog-text');
const probDogBar = document.getElementById('prob-dog-bar');
const probCatText = document.getElementById('prob-cat-text');
const probCatBar = document.getElementById('prob-cat-bar');

// Theme toggling logic
const themeToggleBtn = document.getElementById('theme-toggle');
const darkIcon = document.getElementById('theme-icon-dark');
const lightIcon = document.getElementById('theme-icon-light');

// Check OS preference
if (localStorage.theme === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    document.documentElement.classList.add('dark');
    lightIcon.classList.remove('hidden');
    darkIcon.classList.add('hidden');
} else {
    document.documentElement.classList.remove('dark');
    darkIcon.classList.remove('hidden');
    lightIcon.classList.add('hidden');
}

themeToggleBtn.addEventListener('click', () => {
    document.documentElement.classList.toggle('dark');
    if (document.documentElement.classList.contains('dark')) {
        localStorage.theme = 'dark';
        lightIcon.classList.remove('hidden');
        darkIcon.classList.add('hidden');
    } else {
        localStorage.theme = 'light';
        darkIcon.classList.remove('hidden');
        lightIcon.classList.add('hidden');
    }
});


let currentFile = null;
const API_URL = "http://127.0.0.1:8000/predict";

// ─── Drag & Drop Event Listeners ────────────────────────────────────────

dropzone.addEventListener('click', () => fileInput.click());

dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('border-brand-400', 'scale-[1.02]');
});

dropzone.addEventListener('dragleave', (e) => {
    e.preventDefault();
    dropzone.classList.remove('border-brand-400', 'scale-[1.02]');
});

dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('border-brand-400', 'scale-[1.02]');

    if (e.dataTransfer.files.length) {
        handleFileSelect(e.dataTransfer.files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length) {
        handleFileSelect(e.target.files[0]);
    }
});

function handleFileSelect(file) {
    if (!file.type.startsWith('image/')) {
        alert('Please upload a valid image file (JPG/PNG).');
        return;
    }

    currentFile = file;

    const reader = new FileReader();
    reader.onload = (e) => {
        imagePreview.src = e.target.result;
        imagePreview.classList.remove('hidden');
        uploadContent.classList.add('opacity-0');

        predictBtn.removeAttribute('disabled');
        predictBtn.classList.remove('cursor-not-allowed', 'opacity-50', 'bg-slate-200', 'text-slate-500', 'dark:bg-slate-700', 'dark:text-slate-400');
        predictBtn.classList.add('bg-brand-500', 'text-white', 'hover:bg-brand-600', 'hover:-translate-y-1', 'shadow-xl', 'shadow-brand-500/30');

        resultsContainer.classList.add('hidden', 'opacity-0', 'translate-y-4');
    };
    reader.readAsDataURL(file);
}

// ─── API Integration ──────────────────────────────────────────────────

predictBtn.addEventListener('click', async () => {
    if (!currentFile) return;

    const originalText = predictBtn.textContent;
    predictBtn.textContent = 'Thinking... 🤔';
    predictBtn.classList.add('animate-pulse', 'pointer-events-none');

    const formData = new FormData();
    formData.append('file', currentFile);

    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            throw new Error('Failed to process image');
        }

        const data = await response.json();
        showResults(data);

    } catch (err) {
        alert(`Oops! Something went wrong: ${err.message}`);
    } finally {
        predictBtn.classList.remove('animate-pulse', 'pointer-events-none');
        predictBtn.textContent = originalText;
    }
});

resetBtn.addEventListener('click', () => {
    currentFile = null;
    fileInput.value = '';
    imagePreview.src = '';
    imagePreview.classList.add('hidden');
    uploadContent.classList.remove('opacity-0');

    predictBtn.setAttribute('disabled', 'true');
    predictBtn.classList.add('cursor-not-allowed', 'opacity-50', 'bg-slate-200', 'text-slate-500', 'dark:bg-slate-700', 'dark:text-slate-400');
    predictBtn.classList.remove('bg-brand-500', 'text-white', 'hover:bg-brand-600', 'hover:-translate-y-1', 'shadow-xl', 'shadow-brand-500/30');

    resultsContainer.classList.add('hidden', 'opacity-0', 'translate-y-4');
});

// ─── UI Rendering ──────────────────────────────────────────────────────

function showResults(data) {
    resultsContainer.classList.remove('hidden');
    setTimeout(() => {
        resultsContainer.classList.remove('opacity-0', 'translate-y-4');
    }, 50);

    resultTitle.textContent = "We think it's a...";
    resultLabel.classList.remove('text-slate-400');

    if (data.prediction.toLowerCase() === 'cat') {
        resultEmoji.textContent = '🐱';
        resultLabel.textContent = 'Cat!';
        resultLabel.className = 'text-6xl font-extrabold capitalize text-brand-500 mb-4 animate-wiggle inline-block';
        resultMessage.textContent = 'Meow! Those pointy ears gave it away.';
    } else if (data.prediction.toLowerCase() === 'dog') {
        resultEmoji.textContent = '🐶';
        resultLabel.textContent = 'Dog!';
        resultLabel.className = 'text-6xl font-extrabold capitalize text-accent-500 mb-4 animate-bounce inline-block';
        resultMessage.textContent = 'Woof! Who\'s a good boy?';
    } else {
        // Out of Distribution (Not Cat/Dog)
        resultTitle.textContent = "Hold on a second...";
        resultEmoji.textContent = '🧐';
        resultLabel.textContent = 'Wait...';
        resultLabel.className = 'text-5xl font-bold capitalize text-slate-500 mb-4';
        resultMessage.textContent = data.message || "That doesn't look like a cat or a dog to me!";
    }

    // Update Probability Bars
    const formatProb = (p) => (p * 100).toFixed(1) + "%";

    // Set text instantly
    probDogText.textContent = formatProb(data.prob_dog || 0);
    probCatText.textContent = formatProb(data.prob_cat || 0);

    // Reset widths to 0 before animating
    probDogBar.style.width = '0%';
    probCatBar.style.width = '0%';

    // Animate widths
    setTimeout(() => {
        probDogBar.style.width = formatProb(data.prob_dog || 0);
        probCatBar.style.width = formatProb(data.prob_cat || 0);
    }, 150);
}
