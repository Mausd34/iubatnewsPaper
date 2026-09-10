/* IUBAT Campus News — front-end behaviour (Alpine.js + fetch helpers) */

/* ---------- CSRF helper for fetch() POST requests ---------- */
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
}
window.CSRF_TOKEN = document.querySelector(
  'meta[name="csrf-token"]'
)?.content || getCookie("csrftoken");

async function postForm(url, formData, isJson = false) {
  const opts = {
    method: "POST",
    headers: { "X-CSRFToken": window.CSRF_TOKEN },
  };
  if (isJson) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(formData);
  } else {
    opts.body = formData;
  }
  const res = await fetch(url, opts);
  const data = await res.json();
  return { ok: res.ok, status: res.status, data };
}

/* ---------- Newsletter subscription (footer) ---------- */
function newsletterForm() {
  return {
    loading: false,
    message: "",
    error: false,
    async subscribe() {
      const form = this.$el;
      const fd = new FormData(form);
      this.loading = true;
      this.message = "";
      try {
        const { ok, data } = await postForm(
          form.action,
          fd
        );
        this.error = !ok;
        this.message = ok
          ? data.message
          : Object.values(data.errors || {}).flat().join(" ");
        if (ok) form.reset();
      } catch (e) {
        this.error = true;
        this.message = "Something went wrong. Please try again.";
      } finally {
        this.loading = false;
        setTimeout(() => (this.message = ""), 6000);
      }
    },
  };
}

/* ---------- Comments ---------- */
function commentSection(slug) {
  return {
    slug,
    replyTo: null,
    loading: false,
    message: "",
    setReply(id, name) {
      this.replyTo = id;
      this.message = `Replying to ${name}…`;
      document
        .getElementById("comment-box")
        ?.scrollIntoView({ behavior: "smooth", block: "center" });
    },
    cancelReply() {
      this.replyTo = null;
      this.message = "";
    },
    async submit() {
      const form = this.$refs.commentForm;
      const fd = new FormData(form);
      if (this.replyTo) fd.append("parent", this.replyTo);
      this.loading = true;
      try {
        const { ok, data } = await postForm(
          `/news/article/${this.slug}/comment/`,
          fd
        );
        if (!ok) {
          this.message = Object.values(data.errors || {})
            .flat()
            .join(" ");
          return;
        }
        this.message = data.message;
        form.reset();
        this.replyTo = null;
        if (data.approved) {
          setTimeout(() => window.location.reload(), 800);
        }
      } finally {
        this.loading = false;
      }
    },
  };
}

/* ---------- Reactions (like / love / insightful) ---------- */
function reactionBar(slug, userReaction, initialCounts) {
  return {
    slug,
    active: userReaction || null,
    counts: initialCounts || { like: 0, love: 0, insightful: 0, total: 0 },
    async react(type) {
      if (!window.CSRF_TOKEN) {
        window.location.href = "/accounts/login/";
        return;
      }
      const fd = new FormData();
      fd.append("reaction_type", type);
      const { ok, data } = await postForm(
        `/news/article/${this.slug}/react/`,
        fd
      );
      if (ok) {
        this.counts = data.counts;
        this.active = data.user_reaction;
      }
    },
  };
}

/* ---------- Share menu ---------- */
function shareMenu(url, title) {
  return {
    open: false,
    copied: false,
    async copyLink() {
      await navigator.clipboard.writeText(url);
      this.copied = true;
      setTimeout(() => (this.copied = false), 2000);
    },
    shareFb() {
      return `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(
        url
      )}`;
    },
    shareTwitter() {
      return `https://twitter.com/intent/tweet?text=${encodeURIComponent(
        title
      )}&url=${encodeURIComponent(url)}`;
    },
  };
}

/* Expose globally for inline x-data usage */
Object.assign(window, {
  newsletterForm,
  commentSection,
  reactionBar,
  shareMenu,
});
