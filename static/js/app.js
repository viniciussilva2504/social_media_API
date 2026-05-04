// ant.social — anti social media JS

const FOOTER_QUOTES = [
  "put your phone down and go to the beach",
  "go read a book, seriously",
  "the sunset is better than this screen",
  "call your mom, she misses you",
  "go for a walk, your legs miss you",
  "the real world has better resolution",
  "touch some grass, it's therapeutic",
  "your dog wants to play with you",
  "go cook something delicious",
  "stare at a wall, it's more productive",
  "go outside, the graphics are amazing",
  "your plants need watering",
  "take a deep breath, not a deep scroll",
  "the stars are out, go look at them",
  "close this tab and open a book",
  "your friends prefer your face, not your feed",
  "go make some real memories",
  "life is happening outside this app",
  "the birds are singing, go listen",
  "your journal misses your handwriting",
  "ant.social media for non-charismatic people",
];

const BRAND_PHRASE = "ant.social media for non-charismatic people";
const BRAND_HTML =
  '<span style="color:#cc2200">a</span>' +
  '<span style="color:#003d99">n</span>' +
  '<span style="color:#c89610">t</span>' +
  ".social media for non-charismatic people";

function rotateHeroQuote() {
  const el = document.getElementById("hero-quote");
  if (!el) return;
  const idx = Math.floor(Math.random() * (FOOTER_QUOTES.length - 1)); // exclude brand phrase from hero
  el.style.opacity = 0;
  setTimeout(() => {
    el.textContent = FOOTER_QUOTES[idx];
    el.style.opacity = 1;
  }, 500);
}

function rotateFooterQuote() {
  const el = document.getElementById("footer-quote");
  if (!el) return;
  const idx = Math.floor(Math.random() * FOOTER_QUOTES.length);
  const quote = FOOTER_QUOTES[idx];
  el.style.opacity = 0;
  setTimeout(() => {
    if (quote === BRAND_PHRASE) {
      el.innerHTML = BRAND_HTML;
    } else {
      el.textContent = quote;
    }
    el.style.opacity = 1;
  }, 500);
}

// Rotate quotes every 15 seconds
document.addEventListener("DOMContentLoaded", () => {
  rotateHeroQuote();
  setInterval(rotateHeroQuote, 15000);

  rotateFooterQuote();
  setInterval(rotateFooterQuote, 12000);
});

// Character counter for post compose
function initCharCounter(textareaId, counterId, maxChars) {
  const textarea = document.getElementById(textareaId);
  const counter = document.getElementById(counterId);
  if (!textarea || !counter) return;

  textarea.addEventListener("input", () => {
    const remaining = maxChars - textarea.value.length;
    counter.textContent = remaining;
    counter.style.color =
      remaining < 10 ? "#cc2200" : remaining < 20 ? "#c89610" : "#aaa";
  });
}

// CSRF token helper for fetch
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// Toggle like via AJAX (called via event delegation)
async function toggleLike(postId, btn) {
  if (btn.disabled) return;
  btn.disabled = true;
  const csrftoken = getCookie("csrftoken");
  try {
    const resp = await fetch(`/antisocial/v1/like/toggle/${postId}/`, {
      method: "POST",
      headers: {
        "X-CSRFToken": csrftoken,
        "Content-Type": "application/json",
      },
      credentials: "same-origin",
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();
    const countEl = btn.querySelector(".like-count");
    if (countEl) countEl.textContent = data.likes_count;
    if (data.status === "liked") {
      btn.classList.add("liked");
    } else {
      btn.classList.remove("liked");
    }
  } catch (err) {
    console.error("Like toggle failed:", err);
  } finally {
    btn.disabled = false;
  }
}

// Toggle follow via AJAX (called via event delegation)
async function toggleFollow(username, btn) {
  if (btn.disabled) return;
  btn.disabled = true;
  const csrftoken = getCookie("csrftoken");
  try {
    const resp = await fetch(`/antisocial/v1/follow/toggle/${username}/`, {
      method: "POST",
      headers: {
        "X-CSRFToken": csrftoken,
        "Content-Type": "application/json",
      },
      credentials: "same-origin",
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();
    if (data.status === "followed") {
      btn.textContent = "unfollow";
      btn.classList.remove("btn-primary");
    } else {
      btn.textContent = "follow";
      btn.classList.add("btn-primary");
    }
  } catch (err) {
    console.error("Follow toggle failed:", err);
  } finally {
    btn.disabled = false;
  }
}

// Event delegation for like and follow buttons
document.addEventListener("click", (e) => {
  const likeBtn = e.target.closest("[data-like-post]");
  if (likeBtn) {
    toggleLike(likeBtn.dataset.likePost, likeBtn);
    return;
  }
  const followBtn = e.target.closest("[data-follow-user]");
  if (followBtn) {
    toggleFollow(followBtn.dataset.followUser, followBtn);
  }
});
