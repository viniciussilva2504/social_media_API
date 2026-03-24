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
];

function rotateFooterQuote() {
  const el = document.getElementById("footer-quote");
  if (!el) return;
  const idx = Math.floor(Math.random() * FOOTER_QUOTES.length);
  el.style.opacity = 0;
  setTimeout(() => {
    el.textContent = FOOTER_QUOTES[idx];
    el.style.opacity = 1;
  }, 500);
}

// Rotate quotes every 60 seconds
document.addEventListener("DOMContentLoaded", () => {
  rotateFooterQuote();
  setInterval(rotateFooterQuote, 60000);
});

// Character counter for post compose
function initCharCounter(textareaId, counterId, maxChars) {
  const textarea = document.getElementById(textareaId);
  const counter = document.getElementById(counterId);
  if (!textarea || !counter) return;

  textarea.addEventListener("input", () => {
    const remaining = maxChars - textarea.value.length;
    counter.textContent = remaining;
    counter.style.color = remaining < 20 ? "#c0392b" : "#aaa";
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
  }
}

// Toggle follow via AJAX (called via event delegation)
async function toggleFollow(username, btn) {
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
