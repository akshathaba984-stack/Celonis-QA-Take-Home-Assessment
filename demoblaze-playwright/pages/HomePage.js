class HomePage {
  /**
   * @param {import('@playwright/test').Page} page
   */
  constructor(page) {
    this.page = page;
    this.laptopsCategory = page.getByRole('link', { name: 'Laptops', exact: true });
    this.productGrid = page.locator('#tbodyid');
  }

  async open() {
    await this.page.goto('/');
    await this.page.waitForLoadState('domcontentloaded');
  }

  async goToLaptopsCategory() {
    await this.laptopsCategory.click();
    await this.productGrid.locator('.card-title a').first().waitFor({ state: 'visible' });
  }

  /**
   * @param {string | RegExp} productName
   */
  async openProduct(productName) {
    const productLink = this.productGrid.getByRole('link', { name: productName });
    await productLink.click();
    await this.page.waitForURL(/prod\.html\?idp_=/);
  }
}

module.exports = { HomePage };
