class CartPage {
  /**
   * @param {import('@playwright/test').Page} page
   */
  constructor(page) {
    this.page = page;
    this.cartTableBody = page.locator('#tbodyid');
    this.cartRows = page.locator('#tbodyid tr');
    this.totalPrice = page.locator('#totalp');
    this.placeOrderButton = page.getByRole('button', { name: 'Place Order' });
    this.orderModal = page.locator('#orderModal');
    this.orderModalTitle = page.locator('#orderModalLabel');
    this.checkoutFields = {
      name: page.locator('#name'),
      country: page.locator('#country'),
      city: page.locator('#city'),
      creditCard: page.locator('#card'),
      month: page.locator('#month'),
      year: page.locator('#year'),
    };
  }

  /**
   * @param {string | RegExp} productName
   */
  async expectProductInCart(productName) {
    const row = this.cartRows.filter({ hasText: productName });
    await row.waitFor({ state: 'visible' });
    await row.getByRole('cell').nth(1).waitFor({ state: 'visible' });
  }

  /**
   * @param {string | RegExp} productName
   */
  async expectProductHasPrice(productName) {
    const row = this.cartRows.filter({ hasText: productName });
    const priceCell = row.getByRole('cell').nth(2);
    await priceCell.waitFor({ state: 'visible' });
    const priceText = (await priceCell.innerText()).trim();
    if (!/^\d+(\.\d+)?$/.test(priceText)) {
      throw new Error(`Expected numeric price in cart, got "${priceText}"`);
    }
  }

  async expectCartTotalDisplayed() {
    await this.totalPrice.waitFor({ state: 'visible' });
    const total = (await this.totalPrice.innerText()).trim();
    if (!/^\d+(\.\d+)?$/.test(total)) {
      throw new Error(`Expected numeric cart total, got "${total}"`);
    }
  }

  async openPlaceOrderForm() {
    await this.placeOrderButton.click();
    await this.orderModal.waitFor({ state: 'visible' });
  }

  async expectPlaceOrderFormVisible() {
    await this.orderModalTitle.waitFor({ state: 'visible' });
    await this.page.getByText('Place order', { exact: true }).waitFor({ state: 'visible' });
  }

  async expectCheckoutFieldsVisible() {
    for (const field of Object.values(this.checkoutFields)) {
      await field.waitFor({ state: 'visible' });
    }
  }
}

module.exports = { CartPage };
