// ***********************************************
// ant.social — Cypress support file
// ***********************************************

// Custom command: register a new user via the web form
Cypress.Commands.add("register", (username, password, email = "") => {
  cy.visit("/register/");
  cy.get("#username").type(username);
  if (email) {
    cy.get("#email").type(email);
  }
  cy.get("#password").type(password);
  cy.get("#password_confirm").type(password);
  cy.get('button[type="submit"]').click();
});

// Custom command: login via the web form
Cypress.Commands.add("login", (username, password) => {
  cy.visit("/login/");
  cy.get("#username").type(username);
  cy.get("#password").type(password);
  cy.get('button[type="submit"]').click();
});

// Custom command: Create a user via Django management command
// (requires the dev server to have been seeded, or we use the register flow)
Cypress.Commands.add("createUserAndLogin", (username, password) => {
  cy.register(username, password, `${username}@test.com`);
  // After registration the user is automatically redirected to /feed/
  cy.url().should("include", "/feed/");
});
