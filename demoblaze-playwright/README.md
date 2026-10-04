# Demoblaze Playwright Automation

Simple JavaScript UI automation for the [Demoblaze](https://www.demoblaze.com/) demo store using [Playwright](https://playwright.dev/).

## What this automation covers

End-to-end scenario (no order submission):

1. Open Demoblaze
2. Open the **Laptops** category
3. Select **MacBook air**
4. Verify the product detail page
5. **Add to cart** (accepts the browser alert)
6. Open **Cart**
7. Verify **MacBook air** and its price in the cart
8. Click **Place Order**
9. Verify the checkout modal and fields: Name, Country, City, Credit Card, Month, Year

## Application under test

- **URL:** https://www.demoblaze.com/
- **Scope:** Public guest checkout flow only (no login, no purchase submit)

## Project structure

```
demoblaze-playwright/
├── playwright.config.js    # Playwright settings, base URL, HTML reporter
├── package.json
├── pages/                  # Page Object Model — UI actions per screen
│   ├── HomePage.js
│   ├── ProductPage.js
│   └── CartPage.js
└── tests/
    └── macbook-air-checkout.spec.js   # End-to-end test scenario
```

## Prerequisites

- [Node.js](https://nodejs.org/) 18 or newer
- npm (included with Node.js)

## Required dependencies

- `@playwright/test` — Playwright Test runner and assertions

Browsers are installed separately via the Playwright CLI (see below).

## Install dependencies

```bash
npm install
npx playwright install chromium
```

## Run the Playwright test

```bash
npm test
```

Or:

```bash
npx playwright test
```

## Run in headed (visible browser) mode

```bash
npm run test:headed
```

Or:

```bash
npx playwright test --headed
```

Interactive UI mode:

```bash
npm run test:ui
```

## View the HTML test report

After a test run, open the report:

```bash
npm run report
```

Or:

```bash
npx playwright show-report
```

Reports are written to `playwright-report/` (configured in `playwright.config.js`).

## Framework design

**Page Object Model (POM):** Each major screen has its own class under `pages/`. Methods describe *what the user does* on that screen (for example, `goToLaptopsCategory()`, `addToCart()`), and locators live in one place.

**Tests stay thin:** `tests/macbook-air-checkout.spec.js` reads like the manual test steps. It creates page objects and calls their methods, plus a few Playwright `expect` checks at the end.

**Why separate pages from tests?**

- New scenarios (phones, monitors, negative cases) can reuse the same page classes without duplicating selectors.
- When Demoblaze markup changes, you update locators in one file instead of every test.
- Reviews and demos are easier: the spec file shows *flow*; page files show *how the UI is driven*.
