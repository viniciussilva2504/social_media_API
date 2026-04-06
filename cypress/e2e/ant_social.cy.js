// ant.social — Full E2E Test Suite
// Covers: registration, login, post CRUD, comments, likes, follow,
//         profile, search, feed, password reset, and navigation.
//
// Run with: npx cypress run  (headless)
//       or: npx cypress open  (interactive)
//
// Requires the Django dev server running at http://localhost:8000
// with a fresh/empty database (flush before running).

const uniqueId = () => Math.random().toString(36).substring(2, 8);

describe("ant.social — E2E", () => {
  const user1 = `user_${uniqueId()}`;
  const user2 = `user_${uniqueId()}`;
  const password = "Str0ngP@ss!";

  // ── Public pages ──────────────────────────────────────

  describe("Public Pages", () => {
    it("shows the home page with login/register links", () => {
      cy.visit("/");
      cy.contains("ant.social").should("be.visible");
      cy.get(".nav-links").contains("login").should("be.visible");
      cy.get(".nav-links").contains("register").should("be.visible");
    });

    it("healthcheck endpoint returns ok", () => {
      cy.request("/health/").then((resp) => {
        expect(resp.status).to.eq(200);
        expect(resp.body.status).to.eq("ok");
        expect(resp.body.database).to.eq("ok");
      });
    });

    it("robots.txt is accessible", () => {
      cy.request("/robots.txt").its("status").should("eq", 200);
    });

    it("API docs (Swagger) are accessible", () => {
      cy.request("/api/docs/").its("status").should("eq", 200);
    });
  });

  // ── Registration ──────────────────────────────────────

  describe("Registration", () => {
    it("registers user1 and redirects to feed", () => {
      cy.register(user1, password, `${user1}@test.com`);
      cy.url().should("include", "/feed/");
    });

    it("registers user2", () => {
      cy.register(user2, password, `${user2}@test.com`);
      cy.url().should("include", "/feed/");
    });

    it("rejects duplicate username", () => {
      cy.visit("/register/");
      cy.get("#username").type(user1);
      cy.get("#password").type(password);
      cy.get("#password_confirm").type(password);
      cy.get('button[type="submit"]').click();
      cy.url().should("include", "/register");
      cy.contains("Username already taken").should("be.visible");
    });

    it("rejects password mismatch", () => {
      cy.visit("/register/");
      cy.get("#username").type(`mismatch_${uniqueId()}`);
      cy.get("#password").type(password);
      cy.get("#password_confirm").type("DifferentP@ss1");
      cy.get('button[type="submit"]').click();
      cy.url().should("include", "/register");
      cy.contains("Passwords do not match").should("be.visible");
    });
  });

  // ── Login / Logout ────────────────────────────────────

  describe("Login & Logout", () => {
    it("logs in user1", () => {
      cy.login(user1, password);
      cy.url().should("include", "/feed/");
    });

    it("rejects bad credentials", () => {
      cy.visit("/login/");
      cy.get("#username").type(user1);
      cy.get("#password").type("WrongPassword1!");
      cy.get('button[type="submit"]').click();
      cy.url().should("include", "/login");
      cy.contains("Invalid username or password").should("be.visible");
    });

    it("logs out via POST and returns to home", () => {
      cy.login(user1, password);
      cy.get(".nav-logout-btn").click();
      cy.url().should("eq", Cypress.config("baseUrl") + "/");
    });
  });

  // ── Post CRUD ─────────────────────────────────────────

  describe("Posts", () => {
    beforeEach(() => {
      cy.login(user1, password);
    });

    it("creates a post from the feed compose box", () => {
      cy.visit("/feed/");
      cy.get("#compose-textarea").type("Hello from Cypress!");
      cy.get(".compose-box button[type='submit']").click();
      // after redirect back to feed, our post should appear
      cy.url().should("include", "/feed/");
      cy.contains("Hello from Cypress!").should("be.visible");
    });

    it("creates a post from the dedicated page", () => {
      cy.visit("/post/new/");
      cy.get("#compose-textarea").type("Dedicated page post");
      cy.get('button[type="submit"]').click();
      cy.url().should("include", "/feed/");
    });

    it("views post detail and sees comments section", () => {
      cy.visit("/feed/");
      cy.get(".post-card a").first().click();
      cy.url().should("match", /\/post\/\d+\//);
      cy.contains("comments").should("be.visible");
    });
  });

  // ── Comments ──────────────────────────────────────────

  describe("Comments", () => {
    it("adds a comment on a post", () => {
      cy.login(user1, password);
      cy.visit("/feed/");
      cy.get(".post-card a").first().click();
      cy.get('textarea[name="content"]').type("Great post!");
      cy.get('button[type="submit"]').click();
      cy.contains("Great post!").should("be.visible");
    });
  });

  // ── Profile ───────────────────────────────────────────

  describe("Profile", () => {
    beforeEach(() => {
      cy.login(user1, password);
    });

    it("views own profile with stats", () => {
      cy.visit(`/profile/${user1}/`);
      cy.get(".profile-header").should("be.visible");
      cy.contains(user1).should("be.visible");
      cy.get(".profile-stats").should("be.visible");
    });

    it("edits display name and bio", () => {
      cy.visit(`/profile/${user1}/edit/`);
      cy.get("#display_name").clear().type("Cypress User");
      cy.get("#bio").clear().type("Tested by Cypress");
      cy.get('button[type="submit"]').click();
      cy.url().should("include", `/profile/${user1}/`);
      cy.contains("Cypress User").should("be.visible");
      cy.contains("Tested by Cypress").should("be.visible");
    });

    it("cannot edit another user's profile (redirects)", () => {
      cy.visit(`/profile/${user2}/edit/`);
      cy.url().should("include", `/profile/${user2}/`);
      cy.url().should("not.include", "/edit/");
    });
  });

  // ── Follow / Unfollow ─────────────────────────────────

  describe("Follow System", () => {
    it("user1 follows user2 via AJAX button", () => {
      cy.login(user1, password);
      cy.visit(`/profile/${user2}/`);
      // intercept the AJAX follow toggle
      cy.intercept("POST", `/antisocial/v1/follow/toggle/${user2}/`).as(
        "followToggle",
      );
      cy.get(`[data-follow-user="${user2}"]`).click();
      cy.wait("@followToggle")
        .its("response.statusCode")
        .should("be.oneOf", [200, 201]);
      // verify on followers page
      cy.visit(`/profile/${user2}/followers/`);
      cy.contains(user1).should("be.visible");
    });

    it("followers and following pages load correctly", () => {
      cy.login(user1, password);
      cy.visit(`/profile/${user1}/following/`);
      cy.contains("Following").should("be.visible");
      cy.visit(`/profile/${user2}/followers/`);
      cy.contains("Followers").should("be.visible");
    });
  });

  // ── Search ────────────────────────────────────────────

  describe("Search", () => {
    it("finds a user by username", () => {
      cy.login(user1, password);
      cy.visit(`/search/?q=${user2}`);
      cy.get(".user-list-item").should("have.length.at.least", 1);
      cy.contains(user2).should("be.visible");
    });

    it("shows no results for gibberish", () => {
      cy.login(user1, password);
      cy.visit("/search/?q=zzzznonexistent");
      cy.get(".user-list-item").should("not.exist");
    });
  });

  // ── Feed ──────────────────────────────────────────────

  describe("Feed", () => {
    it("requires authentication (redirects to login)", () => {
      cy.request({ url: "/feed/", followRedirect: false }).then((resp) => {
        expect(resp.status).to.eq(302);
      });
    });

    it("shows followed users' posts", () => {
      // user2 creates a post
      cy.login(user2, password);
      cy.visit("/feed/");
      cy.get("#compose-textarea").type("Post from user2 for feed test");
      cy.get(".compose-box button[type='submit']").click();
      cy.url().should("include", "/feed/");

      // user1 should see it (user1 follows user2 from earlier test)
      cy.login(user1, password);
      cy.visit("/feed/");
      cy.contains("Post from user2 for feed test").should("be.visible");
    });
  });

  // ── Password Reset ────────────────────────────────────

  describe("Password Reset", () => {
    it("loads the password reset form", () => {
      cy.visit("/password-reset/");
      cy.contains("reset password").should("be.visible");
      cy.get("#email").should("be.visible");
    });

    it("submits reset request and shows done page", () => {
      cy.visit("/password-reset/");
      cy.get("#email").type(`${user1}@test.com`);
      cy.get('button[type="submit"]').click();
      cy.url().should("include", "/password-reset/done/");
      cy.contains("check your email").should("be.visible");
    });
  });

  // ── REST API ──────────────────────────────────────────

  describe("REST API", () => {
    let token;

    before(() => {
      cy.request("POST", "/antisocial/v1/login/", {
        username: user1,
        password: password,
      }).then((resp) => {
        token = resp.body.token;
      });
    });

    it("lists posts via API", () => {
      cy.request({
        url: "/antisocial/v1/post/",
        headers: { Authorization: `Token ${token}` },
      }).then((resp) => {
        expect(resp.status).to.eq(200);
        expect(resp.body).to.have.property("results");
      });
    });

    it("creates a post via API", () => {
      cy.request({
        method: "POST",
        url: "/antisocial/v1/post/",
        headers: { Authorization: `Token ${token}` },
        body: { content: "API post from Cypress" },
      }).then((resp) => {
        expect(resp.status).to.eq(201);
        expect(resp.body.content).to.eq("API post from Cypress");
      });
    });

    it("gets feed via API", () => {
      cy.request({
        url: "/antisocial/v1/feed/",
        headers: { Authorization: `Token ${token}` },
      }).then((resp) => {
        expect(resp.status).to.eq(200);
        expect(resp.body).to.have.property("results");
      });
    });

    it("rejects unauthenticated feed request", () => {
      cy.request({
        url: "/antisocial/v1/feed/",
        failOnStatusCode: false,
      }).then((resp) => {
        expect(resp.status).to.eq(403);
      });
    });

    it("searches users via API", () => {
      cy.request({
        url: `/antisocial/v1/users/?q=${user2}`,
        headers: { Authorization: `Token ${token}` },
      }).then((resp) => {
        expect(resp.status).to.eq(200);
        const usernames = resp.body.results.map((u) => u.username);
        expect(usernames).to.include(user2);
      });
    });

    it("toggles follow via API", () => {
      cy.request({
        method: "POST",
        url: `/antisocial/v1/follow/toggle/${user2}/`,
        headers: { Authorization: `Token ${token}` },
      }).then((resp) => {
        expect(resp.status).to.be.oneOf([200, 201]);
        expect(resp.body).to.have.property("status");
      });
    });
  });
});
