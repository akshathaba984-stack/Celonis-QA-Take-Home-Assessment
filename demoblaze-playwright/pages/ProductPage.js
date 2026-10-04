class ProductPage {
  /**
   * @param {import('@playwright/test').Page} page
   */
  constructor(page) {
    this.page = page;
    this.productTitle = page.locator('h2.name');
    this.productPrice = page.locator('h3.price-container');
    this.addToCartButton = page.getByRole('link', { name: 'Add to cart' });
    this.cartLink = page.locator('#cartur');
  }

  /**
   * @param {string | RegExp} expectedName
   */
  async expectProductDisplayed(expectedName) {
    await this.productTitle.waitFor({ state: 'visible' });
    await this.productPrice.waitFor({ state: 'visible' });
    await this.addToCartButton.waitFor({ state: 'visible' });
    await this.page.getByRole('heading', { name: expectedName, level: 2 }).waitFor({
      state: 'visible',
    });
  }

  async addToCart() {
    this.page.once('dialog', (dialog) => dialog.accept());
    await this.addToCartButton.click();
  }

  async openCart() {
    await this.cartLink.click();
    await this.page.waitForURL('**/cart.html');
  }
}

module.exports = { ProductPage };
